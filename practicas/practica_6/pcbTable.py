from pcb import *


# Emulates the PCB table
class PCBTable:

    # constructor
    def __init__(self):
        self._pcbs = []
        self._running = None
        self._pidActual = 0

    def allPCBS(self):
        return self._pcbs

    # crea un nuevo pcb
    def create(self, priority, path):
        pcb = PCB(self._pidActual, priority, path)
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
