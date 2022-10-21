#!/usr/bin/env python


from hardware import *
import log


class Program:

    def __init__(self, instructions):
        self._instructions = self.expand(instructions)

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
        return "Program({instructions})".format(instructions=self._instructions)


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
            self.kernel.dispatcher().load(pcb, self.kernel.memoryManager.getPageTable(pcb.getID()))
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
        self.kernel.dispatcher().load(pcb, self.kernel.memoryManager.getPageTable(pcb.getID()))
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
        pageTable = self.kernel.memoryManager.getPageTable(actualPCB.getID())
        frames = self.kernel.memoryManager.framesPageTable(pageTable)
        self.kernel.memoryManager.setFreeFrames(frames)
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
        tick = irq.parameters["tick"]
        self.kernel.stadistics().gather(tick)


class Loader:

    # Constructor
    def __init__(self, memoryManager):
        self._nextBaseDir = 0
        self._memoryManager = memoryManager

    # Carga el programa en memoria
    def load(self, pcb, program):
        pcb.setBaseDir(self._nextBaseDir)
        progSize= len(program.instructions)
        cantFrames= progSize // HARDWARE.mmu.frameSize
        if (progSize % HARDWARE.mmu.frameSize) > 0:
            cantFrames += 1
        framesAsignados = self._memoryManager.allocFrames(cantFrames)
        pageTable = self._memoryManager.createPageTable(pcb.getID(), cantFrames, framesAsignados)
        for pageInfo in pageTable:
            page = pageInfo.page
            frame = pageInfo.frame
            dirBase = frame * self._memoryManager.frameSize
            start = page * self._memoryManager.frameSize
            end = start + self._memoryManager.frameSize - 1
            if end > progSize -1:
                end = progSize -1
            for i in range(start, end + 1):
                inst = program.instructions[i]
                HARDWARE.memory.write(dirBase, inst)
                dirBase += 1
        pcb.setStatus(READY)
        log.logger.info(HARDWARE)


class Dispatcher:

    # Asigna a la cpu un proceso a ejecutar
    def load(self, pcb, pageTableDelPCB):
        HARDWARE.mmu.resetTLB()
        for ptInfo in pageTableDelPCB:
            HARDWARE.mmu.setPageFrame(ptInfo.page, ptInfo.frame)
        HARDWARE.cpu.pc = pcb.pc()
        pcb.setStatus(RUNNING)
        HARDWARE.timer.reset()

    # Guarda el estado de un proceso que está dejando la cpu
    def save(self, pcb):
        pcb.setPc(HARDWARE.cpu.pc)
        HARDWARE.cpu.pc = -1


    #def activeTimer(self, quantum):
    #   HARDWARE.timer.quantum = quantum

class MemoryManager:

    def __init__(self, frameSize):
        self._freeFrames = list(range(0, HARDWARE.memory.size // HARDWARE.mmu.frameSize))
        self._freeMemory = HARDWARE.memory.size
        self._pageTables = []
        self._frameSize = frameSize

    def allocFrames(self, cantFrames):
        frames = []
        while (cantFrames != 0):
            frames.append(self._freeFrames.pop(0))
            cantFrames -= 1
        self._freeMemory -= HARDWARE.mmu.frameSize * cantFrames
        return frames

    def liberarFrames(self, frames):
        self._freeFrames + frames
        for frame in frames:
            self._freeMemory += HARDWARE.mmu.frameSize

    def putPageTable(self, pageTable):
        self._pageTables.append(pageTable)

    def getPageTable(self, pid):
        pageTable = None
        for pTable in self._pageTables:
            if pTable[0].pid == pid:
                pageTable = pTable
        return pageTable

    def createPageTable(self,pid, paginas, frames):
        pageTable = []
        for page in range(0, paginas):
            pageTable.append(PageTableInfo(pid, page, frames[page]))
        self.putPageTable(pageTable)
        return pageTable

    def framesPageTable(self, pageTable):
        frames = []
        for ptInfo in pageTable:
            frames.append(ptInfo.frame)
        return frames

    @property
    def frameSize(self):
        return self._frameSize


class FileSystem:

    def __init__(self):
        self._programs = []

    def write(self, path, program):
        self._programs.append({"Path": path, "Program": program})

    def read(self, path):
        programa = None
        for dic in self._programs:
           if path == dic["Path"]:
               programa = dic["Program"]
        return programa

class PageTableInfo:

    def __init__(self, pid, pagina, frame):
        self._pid = pid
        self._page = pagina
        self._frame = frame

    @property
    def pid(self):
        return self._pid
    @property
    def page(self):
        return self._page

    @property
    def frame(self):
        return self._frame

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
    def recolectar(self, tick):
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
        if pcb.status().type() == "waiting":
            self._listaPCBS[posicion].append("IO")
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
        pcb.setStatus(READY)


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

        self._memoryManager = MemoryManager(HARDWARE.mmu.frameSize)
        ## se encarga de cargar los programas a memoria
        self._loader = Loader(self._memoryManager)
        ## emulates the Interrupt Vector Table
        self._interruptVector = HARDWARE._interruptVector
        ## emulates the dispatcher
        self._dispatcher = Dispatcher()
        ##emulates the scheduler
        self._scheduler = scheduler
        ##emulates the stadistics
        self._stadistics = Stadistics(self._pcbTable)

        self._fileSystem = FileSystem()




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

    @property
    def fileSystem(self):
        return self._fileSystem

    @property
    def memoryManager(self):
        return self._memoryManager

    def run(self, path, priority):
        program = self._fileSystem.read(path)
        new_irq = IRQ(NEW_INTERRUPTION_TYPE, {"pro":program, "prio":priority})
        self._interruptVector.handle(new_irq)

    ## emulates a "system call" for programs execution
    def __repr__(self):
        return "Kernel "
