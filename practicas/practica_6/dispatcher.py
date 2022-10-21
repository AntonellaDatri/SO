from hardware import HARDWARE
from state import *

class Dispatcher:

    # Asigna a la cpu un proceso a ejecutar
    @staticmethod
    def load(pcb, pageTableDelPCB):
        HARDWARE.mmu.resetTLB()
        for ptInfo in pageTableDelPCB:
            if ptInfo.frame != -1:
                HARDWARE.mmu.setPageFrame(ptInfo.page, ptInfo.frame)
        HARDWARE.cpu.pc = pcb.pc()
        pcb.setStatus(RUNNING)


    # Guarda el estado de un proceso que esta dejando la cpu
    @staticmethod
    def save(pcb):
        pcb.setPc(HARDWARE.cpu.pc)
        HARDWARE.cpu.pc = -1
