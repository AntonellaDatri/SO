#!/usr/bin/env python


from hardware import *
import log


class Program():

    def __init__(self, name, instructions):
        self._name = name
        self._instructions = self.expand(instructions)

    @property
    def name(self):
        return self._name

    @property
    def instructions(self):
        return self._instructions

    def addInstr(self, instruction):
        self._instructions.append(instruction)

    def expand(self, instructions):
        expanded = []
        for i in instructions:
            if isinstance(i, list):
                ## is a list of instructions
                expanded.extend(i)
            else:
                ## a single instr (a String)
                expanded.append(i)

        ## now test if last instruction is EXIT
        ## if not... add an EXIT as final instruction
        last = expanded[-1]
        if not ASM.isEXIT(last):
            expanded.append(INSTRUCTION_EXIT)

        return expanded

    def __repr__(self):
        return "Program({name}, {instructions})".format(name=self._name, instructions=self._instructions)


## emulates an Input/Output device controller (driver)
class IoDeviceController:

    def __init__(self, device):
        self._device = device
        self._waiting_queue = []
        self._currentPCB = None

    def runOperation(self, pcb, instruction):
        pair = {'pcb': pcb, 'instruction': instruction}
        # append: adds the element at the end of the queue
        self._waiting_queue.append(pair)
        # try to send the instruction to hardware's device (if is idle)
        self.__load_from_waiting_queue_if_apply()

    def getFinishedPCB(self):
        finishedPCB = self._currentPCB
        self._currentPCB = None
        self.__load_from_waiting_queue_if_apply()
        return finishedPCB

    def __load_from_waiting_queue_if_apply(self):
        if (len(self._waiting_queue) > 0) and self._device.is_idle:
            ## pop(): extracts (deletes and return) the first element in queue
            pair = self._waiting_queue.pop(0)
            # print(pair)
            pcb = pair['pcb']
            instruction = pair['instruction']
            self._currentPCB = pcb
            self._device.execute(instruction)

    def __repr__(self):
        return "IoDeviceController for {deviceID} running: {currentPCB} waiting: {waiting_queue}".format(
            deviceID=self._device.deviceId, currentPCB=self._currentPCB, waiting_queue=self._waiting_queue)

## emulates the Interruptions Handlers
class AbstractInterruptionHandler:
    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def kernel(self):
        return self._kernel

    def execute(self, irq):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class {classname}".format(classname=self.__class__.__name__))


## emula el handler de la interrupcion KILL
class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        pcb = self.kernel.pcbTable().running()
        Dispatcher.save(pcb)
        pcb.setStatus(TERMINATED)
        self.kernel.pcbTable().setRunning(None)
        log.logger.info(" Program Finished ")
        if (self.kernel.readyQueue() != []):
            p = self.kernel.readyQueue().pop(0)
            Dispatcher.load(p)
            self.kernel.pcbTable().setRunning(p)


## emula el handler de la interrupcion I/O IN
class IoInInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        operation = irq.parameters
        pcb = self.kernel.pcbTable().running()
        Dispatcher.save(pcb)
        self.kernel.pcbTable().running().setStatus(WAITING)
        self.kernel.pcbTable().setRunning(None)
        if (self.kernel.readyQueue() != []):
            p = self.kernel.readyQueue().pop(0)
            Dispatcher.load(p)
            self.kernel.pcbTable().setRunning(p)
        self.kernel.ioDeviceController.runOperation(pcb, operation)
        log.logger.info(self.kernel.ioDeviceController)
		

## emula el handler de la interrupcion I/O OUT
class IoOutInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        pcb = self.kernel.ioDeviceController.getFinishedPCB()
        pcb.setStatus(READY)
        log.logger.info(self.kernel.ioDeviceController)
        if self.kernel.pcbTable().running() is None:
            Dispatcher.load(pcb)
            self.kernel.pcbTable().setRunning(pcb)
        else:
            self.kernel.readyQueue().append(pcb)


## emula el handler de la interrupcion NEW
class NewInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        log.logger.info("Cargando programa")
        pcb = self.kernel.pcbTable().create()
        self.kernel.loader().load(pcb, irq.parameters)
        if self.kernel.pcbTable().running() is None:
            Dispatcher.load(pcb)
            self.kernel.pcbTable().setRunning(pcb)
        else:
            self.kernel.readyQueue().append(pcb)
			
			
class Loader:

	# Constructor
	def __init__(self):
		self._nextBaseDir = 0
	
	# Carga el programa en memoria 
	def load(self, pcb, program):
		pcb.setBaseDir(self._nextBaseDir)
		progSize = len(program.instructions)
		for index in range(0, progSize):
			inst = program.instructions[index]
			HARDWARE.memory.write(self._nextBaseDir, inst)
			self._nextBaseDir = self._nextBaseDir + 1
		pcb.setStatus(READY)
		log.logger.info(HARDWARE)
		

class Dispatcher:
	
	# Asigna a la cpu un proceso a ejecutar
	def load(pcb):
		HARDWARE.cpu.pc = pcb.pc()
		HARDWARE.mmu.baseDir = pcb.baseDir() 
		pcb.setStatus(RUNNING)
		
	# Guarda el estado de un proceso que está dejando la cpu
	def save(pcb):
		pcb.setPc(HARDWARE.cpu.pc) 
		HARDWARE.cpu.pc = -1


# emulates the core of an Operative System
class Kernel:

    def __init__(self):
        ## setup interruption handlers
        new_handler = NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, new_handler)

        kill_handler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, kill_handler)

        io_in_handler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, io_in_handler)

        io_out_handler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, io_out_handler)

        ## controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)
		## maneja los pcbs
        self._pcbTable = PCBTable()
		## se encarga de cargar los programas a memoria
        self._loader = Loader()
		## emulates the Interrupt Vector Table
        self._interruptVector = HARDWARE._interruptVector
#########################################
#esto no va
        self._readyQueue = []
#########################################


    @property
	#retorna el controlador del dispositivo de I/O
    def ioDeviceController(self):
        return self._ioDeviceController

	#retorna la pcb table
    def pcbTable(self):
        return self._pcbTable
    
	#retorna el loader
    def loader(self):
        return self._loader
#########################################    
#esto no va
    def readyQueue(self):
        return self._readyQueue
#########################################

    def run(self, program):
        new_irq = IRQ(NEW_INTERRUPTION_TYPE, program)
        self._interruptVector.handle(new_irq)

	## emulates a "system call" for programs execution
    def __repr__(self):
        return "Kernel "
	

class PCBTable:

	#constructor
	def __init__(self):
		self._pcbs = []
		self._running = None
		self._pidActual = 0

	#crea un nuevo pcb
	def create(self):
		pcb = PCB(self._pidActual)
		self._pcbs.append(pcb)
		self._pidActual = self._pidActual + 1
		return pcb
	
	#retorna el pcb del programa que se esta ejecutando
	def running(self):
		return self._running
	#setea el pcb del programa que se va a ejecutar
	def setRunning(self, pcb):
		self._running = pcb
	
	#agrega un pcb a la lista de pcb
	def add(self, pcb):
		self._pcbs.append(pcb)

	#elimina un pcb de la lista de pcb
	def remove(self, pcb):
		self._pcbs.remove(pcb)



class PCB:

	def __init__(self, pid):
	#constructor
		self._status = NEW
		self._baseDir = 0
		self._pc = 0
		self._pid = pid

	#retorna el pc del programa
	def pc(self):
		return self._pc
	#setea el pc del programa
	def setPc(self, pc):
		self._pc = pc
	
	#retorna en que direccion se encuentra la primer instruccion del programa
	def baseDir(self):
		return self._baseDir
	#setea la direccion en que se encuentra la primer instruccion del programa
	def setBaseDir(self, baseDir):
		self._baseDir = baseDir
	
	#retorna el estado del programa
	def status(self):
		return self._status
	#setea el estado del programa
	def setStatus(self, status):
		self._status = status

class State:
    def __init__(self, type):
        _type = type

    def type(self):
        return self._type


NEW = State ("new")
TERMINATED = State ("terminated")
READY = State ("ready")
RUNNING = State ("running")
WAITING = State ("waiting")