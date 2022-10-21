from hardware import *


# Emulates the Statistics
class Statistics:

    def __init__(self, pcbTable):
        self._pcbTable = pcbTable
        self._listPCBS = []
        self._listOfTicksNbr = []

    def addPCB(self, pcb):
        self._listPCBS.append([pcb.getID()])
        counter = 0
        while counter < len(self._listOfTicksNbr):
            self._listPCBS[pcb.getID()].append(" ")
            counter += 1

    def gather(self, tick):
        self._listOfTicksNbr.append(tick)
        for pcb in self._pcbTable.allPCBS():
            self.addStatusToList(pcb)
        log.logger.info(tabulate(self._listPCBS, self._listOfTicksNbr, tablefmt='fancy_grid'))

    def addStatusToList(self, pcb):
        pid = pcb.getID()
        if pcb.status().type() == "running":
            self._listPCBS[pid].append("{pc}".format(pc=HARDWARE.cpu.pc))
        if pcb.status().type() == "terminated":
            self._listPCBS[pid].append("-")
        if pcb.status().type() == "ready":
            self._listPCBS[pid].append("*")
        if pcb.status().type() == "waiting":
            self._listPCBS[pid].append("IO")
