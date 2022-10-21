import log
from state import *
from hardware import *
# Emulates the Interruptions Handlers
class AbstractInterruptionHandler:
    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def kernel(self):
        return self._kernel

    # Lo usan KILL e IO IN
    def loadTheNext(self):
        if self.kernel.scheduler().isNotEmptyReadyQueue():
            pcb = self.kernel.scheduler().getNext()
            self.loadPCB(pcb)
        
        HARDWARE.timer.reset()

    # Lo usan NEW e IO OUT
    def needToExpropriate(self, pcb, actualPCB):
        if self.kernel.pcbTable().running() is None:
            pageTable = self.kernel.memoryManager.getPageTable(pcb.getID())
            self.kernel.dispatcher().load(pcb, pageTable)
            self.kernel.pcbTable().setRunning(pcb)
        else:
            self.haveToExpropriate(actualPCB, pcb)

    # Subtarea de needToExpropriate
    def haveToExpropriate(self, actualPCB, pcb):
        if self.kernel.scheduler().mustExpropriate(actualPCB, pcb):
            self.savePCB(actualPCB)
            self.loadPCB(pcb)
        else:
            pcb.setStatus(READY)
            self.kernel.memoryManager.reorderFrames(pcb)
            self.kernel.scheduler().addToReadyQueue(pcb)

    # Subtarea, carga el pcb
    def loadPCB(self, pcb):
        self.kernel.dispatcher().load(pcb, self.kernel.memoryManager.getPageTable(pcb.getID()))
        self.kernel.memoryManager.reorderFrames(pcb)
        self.kernel.pcbTable().setRunning(pcb)
        HARDWARE.timer.reset()

    # Subtarea, salva el pcb que se esta corriendo
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
        self.kernel.memoryManager.setFreeFrames(pageTable)
        self.kernel.dispatcher().save(actualPCB)
        actualPCB.setStatus(TERMINATED)
        self.kernel.pcbTable().setRunning(None)
        self.loadTheNext()
        HARDWARE.timer.reset()
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
        pcb = self.kernel.pcbTable().create(irq.parameters["prio"], irq.parameters["path"])
        self.kernel.statistics().addPCB(pcb)
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


class StatisticsInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        tick = irq.parameters["tick"]
        self.kernel.statistics().gather(tick)


class PageFaultInterruptionHandler(AbstractInterruptionHandler):
    def execute(self, irq):
        actualPCB = self.kernel.pcbTable().running()
        pageTable = self.kernel.memoryManager.getPageTable(actualPCB.getID())
        self.kernel.dispatcher().save(actualPCB)
        pageNumber = actualPCB.pc() // self.kernel.memoryManager.frameSize
        pageInfo = pageTable[pageNumber]
        self.kernel.memoryManager.allocFrames(pageInfo, actualPCB)
        self.kernel.dispatcher().load(actualPCB, pageTable)
