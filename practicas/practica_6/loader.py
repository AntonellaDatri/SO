from hardware import HARDWARE
from state import *
import log


class Loader:

    # Constructor
    def __init__(self, memoryManager):
        self._nextBaseDir = 0
        self._memoryManager = memoryManager

    # Carga el programa en memoria
    def load(self, pcb, program):
        pcb.setBaseDir(self._nextBaseDir)
        programSize = len(program)
        cantPage = programSize // HARDWARE.mmu.frameSize
        if (programSize % HARDWARE.mmu.frameSize) > 0:
            cantPage += 1
        self._memoryManager.createPageTable(pcb.getID(), cantPage)
        pcb.setStatus(READY)
