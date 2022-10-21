from hardware import *
from pageTableInfo import *


class MemoryManager:

    def __init__(self, frameSize, swap):
        self._freeFrames = list(range(0, HARDWARE.memory.size // HARDWARE.mmu.frameSize))
        self._usedFrames = []
        self._freeMemory = HARDWARE.memory.size
        self._pageTables = []
        self._frameSize = frameSize
        self._swap = swap

    def isNotEmptyFreeFrames(self):
        return self._freeFrames != []

    def allocFrames(self, pageInfo, actualPCB):
        if self.isNotEmptyFreeFrames():
            frame = self._freeFrames.pop(0)
        else:
            frame = self.swapOut()
        self.swapIn(pageInfo, frame, actualPCB)
        pageInfo.frame = frame
        self._usedFrames.append({"frame": frame, "bit": 1})

    def setFreeFrames(self, pageTable):
        for ptInfo in pageTable:
            if ptInfo.frame != -1:
                self._freeFrames.append(ptInfo.frame)
                ptInfo.frame = -1
                self._freeMemory += self._frameSize

    def putPageTable(self, pageTable):
        self._pageTables.append(pageTable)

    def getPageTable(self, pid):
        pageTable = None
        for pTable in self._pageTables:
            if pTable[0].pid == pid:
                pageTable = pTable
        return pageTable

    def createPageTable(self, pid, pages):
        pageTable = []
        for page in range(0, pages):
            pageTable.append(PageTableInfo(pid, page))
        self.putPageTable(pageTable)
        return pageTable

    @staticmethod
    def framesPageTable(pageTable):
        frames = []
        for ptInfo in pageTable:
            frames.append(ptInfo.frame)
        return frames

    @property
    def frameSize(self):
        return self._frameSize

    def reorderFrames(self, pcb):
        page = pcb.pc() // 4
        pageTable = self.getPageTable(pcb.getID())
        self._swap.victimSelection.doSomething(page, pageTable, self._usedFrames)

    def swapIn(self, pageInfo, frame, actualPCB):
        path = actualPCB.path
        program = self._swap.program(pageInfo, path)
        page = pageInfo.page
        dirBase = frame * self._frameSize
        start = page * self._frameSize
        end = start + self._frameSize - 1
        programSize = len(program)
        if end > programSize - 1:
            end = programSize - 1
        for i in range(start, end + 1):
            inst = program[i]
            HARDWARE.memory.write(dirBase, inst)
            dirBase += 1
        self.reorderFrames(actualPCB)

    def swapOut(self):
        frame = self._swap.victimSelection.getVictimFrame(self._usedFrames, self._pageTables)
        instruction = []
        for i in range(frame * self._frameSize, frame * self._frameSize + self._frameSize):
            instruction.append(HARDWARE.memory.read(i))
        for pageTable in self._pageTables:
            for ptInfo in pageTable:
                if ptInfo.frame == frame:
                    ptInfo.frame = -1
                    ptInfo.swap = True
                    self._swap.addCache(ptInfo, instruction)
        return frame
