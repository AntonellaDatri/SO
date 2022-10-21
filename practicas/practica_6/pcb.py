from state import *


# Emulate the PCB
class PCB:

    def __init__(self, pid, priority, path):
        # constructor
        self._status = NEW
        self._baseDir = 0
        self._pc = 0
        self._path = path
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

    @property
    def path(self):
        return self._path