#!/usr/bin/env python


from hardware import *
import log


class Program:

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

    #Lo usan KILL e IO IN
    def loadTheNext(self):
        if self.kernel.scheduler().isNotEmptyReadyQueue():
            pcb = self.kernel.scheduler().getNext()
            self.loadPCB(pcb)

    # Lo usan NEW e IO OUT
    def needToExpropriate(self, pcb, actualPCB):
        if self.kernel.pcbTable().running() is None:
            self.kernel.dispatcher().load(pcb)
            self.kernel.pcbTable().setRunning(pcb)
        else:
            self.haveToExpropriate(actualPCB, pcb)

    #Subtarea de needToExpropriate
    def haveToExpropriate(self, actualPCB, pcb):
        if self.kernel.scheduler().mustExpropriate(actualPCB, pcb):
            self.savePCB(actualPCB)
            self.loadPCB(pcb)
        else:
            self.kernel.scheduler().addToReadyQueue(pcb)

    #Subtarea, carga el pcb
    def loadPCB(self, pcb):
        self.kernel.dispatcher().load(pcb)
        self.kernel.pcbTable().setRunning(pcb)

    #Subtarea, salva el pcb que se esta corriendo
    def savePCB(self, actualPCB):
        self.kernel.dispatcher().save(actualPCB)
        self.kernel.scheduler().addToReadyQueue(actualPCB)
        actualPCB.setStatus(READY)

    def execute(self, irq):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class {classname}".format(classname=self.__class__.__name__))


## emula el handler de la interrupcion KILL
class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        actualPCB = self.kernel.pcbTable().running()
        self.kernel.dispatcher().save(actualPCB)
        actualPCB.setStatus(TERMINATED)
        self.kernel.pcbTable().setRunning(None)
        self.loadTheNext()
        log.logger.info(" Program Finished ")

## emula el handler de la interrupcion I/O IN
class IoInInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        operation = irq.parameters
        actualPCB = self.kernel.pcbTable().running()
        self.kernel.dispatcher().save(actualPCB)
        self.kernel.pcbTable().running().setStatus(WAITING)
        self.kernel.pcbTable().setRunning(None)
        self.loadTheNext()
        self.kernel.ioDeviceController.runOperation(actualPCB, operation)
        log.logger.info(self.kernel.ioDeviceController)


## emula el handler de la interrupcion I/O OUT
class IoOutInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        pcb = self.kernel.ioDeviceController.getFinishedPCB()
        actualPCB = self.kernel.pcbTable().running()
        log.logger.info(self.kernel.ioDeviceController)
        self.needToExpropriate(pcb, actualPCB)

## emula el handler de la interruption NEW
class NewInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        log.logger.info("Cargando programa")
        actualPCB = self.kernel.pcbTable().running()
        pcb = self.kernel.pcbTable().create(irq.parameters["prio"])
        self.kernel.stadistics().addPCB(pcb)
        self.kernel.loader().load(pcb, irq.parameters["pro"])
        self.needToExpropriate(pcb, actualPCB)

# Emula el handler de la interruption TimeOut
class TimeOutInterruptionHandler(AbstractInterruptionHandler):
    def execute(self, irq):
        if self.kernel.scheduler().isNotEmptyReadyQueue():
            actualPCB = self.kernel.pcbTable().running()
            self.savePCB(actualPCB)
            pcb = self.kernel.scheduler().getNext()
            self.loadPCB(pcb)

class StadisticsInterruptionHandler(AbstractInterruptionHandler):
    def execute(self, irq):
        pid = self.kernel.pcbTable().running().getID()
        pc = irq.parameters["pc"]
        tick = irq.parameters["tick"]
        self.kernel.stadistics().gather(pid, pc, tick)



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
    def load(self, pcb):
        HARDWARE.cpu.pc = pcb.pc()
        HARDWARE.mmu.baseDir = pcb.baseDir()
        pcb.setStatus(RUNNING)
        HARDWARE.timer.reset()

    # Guarda el estado de un proceso que está dejando la cpu
    def save(self, pcb):
        pcb.setPc(HARDWARE.cpu.pc)
        HARDWARE.cpu.pc = -1

class PCBTable:

    # constructor
    def __init__(self):
        self._pcbs = []
        self._running = None
        self._pidActual = 0

    def allPCBS(self):
        return  self._pcbs

    # crea un nuevo pcb
    def create(self, priority):
        pcb = PCB(self._pidActual, priority)
        self._pcbs.append(pcb)
        self._pidActual = self._pidActual + 1
        return pcb

    # retorna el pcb del programa que se esta ejecutando
    def running(self):
        return self._running

    # setea el pcb del programa que se va a ejecutar
    def setRunning(self, pcb):
        self._running = pcb

    # agrega un pcb a la lista de pcb
    def add(self, pcb):
        self._pcbs.append(pcb)

    # elimina un pcb de la lista de pcb
    def remove(self, pcb):
        self._pcbs.remove(pcb)


class PCB:

    def __init__(self, pid, priority):
        # constructor
        self._status = NEW
        self._baseDir = 0
        self._pc = 0
        self._pid = pid
        self._priority = priority

    # retorna el pc del programa
    def pc(self):
        return self._pc

    # retorna la prioridad del programa
    def priority(self):
        return self._priority

    # setea el pc del programa
    def setPc(self, pc):
        self._pc = pc

    def getID(self):
        return self._pid
    # retorna en que direccion se encuentra la primer instruccion del programa
    def baseDir(self):
        return self._baseDir

    # setea la direccion en que se encuentra la primer instruccion del programa
    def setBaseDir(self, baseDir):
        self._baseDir = baseDir

    # retorna el estado del programa
    def status(self):
        return self._status

    # setea el estado del programa
    def setStatus(self, status):
        self._status = status


class Stadistics():

    def __init__(self, pcbTable):
        self._pcbTable = pcbTable
        self._listaPCBS = []
        self._listaDeTicksNbr = []


    def addPCB(self, pcb):
        self._listaPCBS.append([pcb.getID()])
    def recolectar(self, pid, pc, tick):
        self._listaDeTicksNbr.append(tick)
        posicionActual = 0
        for pcb in self._pcbTable.allPCBS():
            self.addStatusToList(pcb, posicionActual)
            posicionActual = posicionActual + 1
        log.logger.info(tabulate(self._listaPCBS, self._listaDeTicksNbr, tablefmt='fancy_grid'))

    def tick(self, tickNbr):
        #self.generatePCBSList()
        #ticks = str(tickNbr)
        #self._listaDeTicksNbr.append(ticks)
        posicionActual = 0
       # for pcb in self._pcbTable.allPCBS():
         #   self.addStatusToList(pcb, posicionActual)
         #   posicionActual = posicionActual + 1
        #if self._pcbTable.running() is None:
         #   log.logger.info(tabulate(self._listaPCBS, self._listaDeTicksNbr, tablefmt='fancy_grid'))

    def addStatusToList(self, pcb, posicion):
        if pcb.status().type() == "running":
            self._listaPCBS[posicion].append("{pc}".format(pc=HARDWARE.cpu.pc))
        if pcb.status().type() == "terminated":
            self._listaPCBS[posicion].append("-")
        if pcb.status().type() == "ready":
            self._listaPCBS[posicion].append("*")

##Los numeros ceros que aparecen cuando se cargan los procesos 1 y 2, son cuando se lanza el kill del proceso anterior
## pero este aun no esta corriendo, solo cambio el estado.

class State:
    def __init__(self, type):
        self._type = type

    def type(self):
        return self._type


NEW = State("new")
TERMINATED = State("terminated")
READY = State("ready")
RUNNING = State("running")
WAITING = State("waiting")

class Scheduler:
    def __init__(self):
        self._readyQueue = []

    def isNotEmptyReadyQueue(self):
        return self._readyQueue != []

    def addToReadyQueue(self, pcb):
        self._readyQueue.append(pcb)

    def getNext(self):
        return self._readyQueue.pop(0)


    def mustExpropiate(self, actualPCB, pcbToAdd):
       log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class")


##Del 0 al 10, se maneja la prioridad, siendo 0 el menos importante al 10, el de mayor importancia.
class SchedulerPriorityPreemptive (Scheduler):
    def getNext(self):
        self.envejecer()
        return self._readyQueue.pop(0)["pcb"]

    def envejecer(self):
        for diccionario in self._readyQueue:
           diccionario = {"pcb": diccionario["pcb"], "priorityActual": (diccionario["priorityActual"]) + 1}

    def addToReadyQueue(self, pcb):
        diccionario = {"pcb":pcb, "priorityActual": (pcb.priority())}
        lista = []
        while self._readyQueue != [] and (pcb.priority() < self._readyQueue[0]["priorityActual"]):
            lista.append(self._readyQueue.pop(0))
        lista.append(diccionario)
        self._readyQueue = lista + self._readyQueue


    def mustExpropiate(self, actualPCB, pcbToAdd):
        return pcbToAdd.priority() > actualPCB.priority()

class SchedulerPriorityNonPreemptive (SchedulerPriorityPreemptive):

    def mustExpropiate(self, actualPCB, pcbToAdd):
        return False


class SchedulerFCFS(Scheduler):
    def mustExpropiate(self, actualPCB, pcbToAdd):
        return False

class SchedulerRoundRobin(Scheduler):

    def __init__(self, quantum):
        Scheduler.__init__(self)
        HARDWARE.timer.quantum = quantum

    def mustExpropiate(self, actualPCB, pcbToAdd):
        return False

# emulates the core of an Operative System



class Kernel:

    def __init__(self, scheduler):
        ## setup interruption handlers
        new_handler = NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, new_handler)

        kill_handler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, kill_handler)

        io_in_handler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, io_in_handler)

        io_out_handler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, io_out_handler)
        time_out_handler = TimeOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(TIMEOUT_INTERRUPTION_TYPE, time_out_handler)
        HARDWARE.interruptVector.register(STADISTICS_INTERRUPTION_TYPE, StadisticsInterruptionHandler(self))
        ## controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)
        ## maneja los pcbs
        self._pcbTable = PCBTable()
        ## se encarga de cargar los programas a memoria
        self._loader = Loader()
        ## emulates the Interrupt Vector Table
        self._interruptVector = HARDWARE._interruptVector
        ## emulates the dispatcher
        self._dispatcher = Dispatcher()
        ##emulates the scheduler
        self._scheduler = scheduler
        ##emulates the stadistics
        self._stadistics = Stadistics(self._pcbTable)
        #HARDWARE.clock.addSubscriber(self._stadistics)


    @property
    # retorna el controlador del dispositivo de I/O
    def ioDeviceController(self):
        return self._ioDeviceController

    # retorna la pcb table
    def pcbTable(self):
        return self._pcbTable

    # retorna el dispatcher
    def dispatcher(self):
        return self._dispatcher
    # retorna el scheduler
    def scheduler(self):
        return self._scheduler
    # retorna el loader
    def loader(self):
        return self._loader
    # retorna el stadistics
    def stadistics(self):
        return self._stadistics

    def run(self, program, priority):
        new_irq = IRQ(NEW_INTERRUPTION_TYPE, {"pro":program, "prio":priority})
        self._interruptVector.handle(new_irq)

    ## emulates a "system call" for programs execution
    def __repr__(self):
        return "Kernel "
