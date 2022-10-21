#!/usr/bin/env python
# coding=utf-8

from hardware import *
import log
from pcbTable import *
from scheduler import *
from victimSelection import *
from interruptionHandler import *
from statistics import *
from fileSystem import *
from swap import *
from ioDeviceController import *
from dispatcher import *
from loader import *
from memoryManager import *
from program import *


# Emulates the core of an Operative System
class Kernel:

    def __init__(self, scheduler, victim):
        ## setup interruption handlers
        # New
        new_handler = NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, new_handler)

        # Kill
        kill_handler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, kill_handler)

        # IO
        io_in_handler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, io_in_handler)

        io_out_handler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, io_out_handler)

        # Time Out
        time_out_handler = TimeOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(TIMEOUT_INTERRUPTION_TYPE, time_out_handler)

        # Page Fault
        page_fault_handler = PageFaultInterruptionHandler(self)
        HARDWARE.interruptVector.register(PAGE_FAULT_INTERRUPTION_TYPE, page_fault_handler)

        # Statistics
        statistics_handler = StatisticsInterruptionHandler(self)
        HARDWARE.interruptVector.register(STATISTICS_INTERRUPTION_TYPE, statistics_handler)

        # Controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)

        # PCB handler
        self._pcbTable = PCBTable()

        # Emulates the Interrupt Vector Table
        self._interruptVector = HARDWARE.interruptVector

        # Emulates the dispatcher
        self._dispatcher = Dispatcher()

        # Emulates the scheduler
        self._scheduler = scheduler

        # Emulates the statistics
        self._statistics = Statistics(self._pcbTable)

        # Emulate the file system
        self._fileSystem = FileSystem()

        # Emulates the swap
        self._swap = Swap(self._fileSystem, victim)

        ## emulates the memoryManager
        self._memoryManager = MemoryManager(HARDWARE.mmu.frameSize, self._swap)

        ## se encarga de cargar los programas a memoria
        self._loader = Loader(self._memoryManager)

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
    def statistics(self):
        return self._statistics

    @property
    def fileSystem(self):
        return self._fileSystem

    @property
    def memoryManager(self):
        return self._memoryManager

    def run(self, path, priority):
        program = self._fileSystem.read(path)
        new_irq = IRQ(NEW_INTERRUPTION_TYPE, {"path": path, "pro": program, "prio": priority})
        self._interruptVector.handle(new_irq)

    ## emulates a "system call" for programs execution
    def __repr__(self):
        return "Kernel"
