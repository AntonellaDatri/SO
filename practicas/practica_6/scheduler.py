from state import *
from hardware import HARDWARE


# Emulates the Schedulers
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

    def mustExpropriate(self, actualPCB, pcbToAdd):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class")


# Del 0 al 10, se maneja la prioridad, siendo 0 el menos importante al 10, el de mayor importancia.
class SchedulerPriorityPreemptive (Scheduler):
    def getNext(self):
        self.getOld()
        return self._readyQueue.pop(0)["pcb"]

    def getOld(self):
        for dictionary in self._readyQueue:
            dictionary["priorityActual"] = dictionary["priorityActual"] + 1
# dictionary = {"pcb": dictionary["pcb"], "priorityActual": (dictionary["priorityActual"]) + 1}

    def addToReadyQueue(self, pcb):
        dictionary = {"pcb": pcb, "priorityActual": (pcb.priority())}
        list = []
        while self._readyQueue != [] and (pcb.priority() < self._readyQueue[0]["priorityActual"]):
            list.append(self._readyQueue.pop(0))
        list.append(dictionary)
        self._readyQueue = list + self._readyQueue

    def mustExpropriate(self, actualPCB, pcbToAdd):
        return pcbToAdd.priority() > actualPCB.priority()


class SchedulerPriorityNonPreemptive (SchedulerPriorityPreemptive):

    def mustExpropriate(self, actualPCB, pcbToAdd):
        return False


class SchedulerFCFS(Scheduler):
    def mustExpropriate(self, actualPCB, pcbToAdd):
        return False


class SchedulerRoundRobin(Scheduler):

    def __init__(self, quantum):
        Scheduler.__init__(self)
        HARDWARE.timer.quantum = quantum

    def mustExpropriate(self, actualPCB, pcbToAdd):
        return False
