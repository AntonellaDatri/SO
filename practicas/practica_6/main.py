from hardware import *
from so import *
import log


##
##  MAIN 
##
if __name__ == '__main__':
    log.setupLogger()
    log.logger.info('Starting emulator')

    HARDWARE.setup(manualClock=True, memorySize=20)
    ## Switch on computer
    HARDWARE.switchOn()

    ## new create the Operative System Kernel
    kernel = Kernel(SchedulerRoundRobin(3), VictimSelectionSecondChance())
    #  SchedulerFCFS()
    #  SchedulerRoundRobin(quantum)
    #  SchedulerPriorityNonPreemptive()
    #  SchedulerPriorityPreemptive()

    #  VictimSelectionFIFO()
    #  VictimSelectionLRU()
    #  VictimSelectionSecondChance()

    prg1 = Program([ASM.CPU(1), ASM.IO(), ASM.CPU(5), ASM.IO(), ASM.CPU(1)])
    prg2 = Program([ASM.CPU(6), ASM.IO(), ASM.CPU(1)])
    prg3 = Program([ASM.CPU(4), ASM.IO(), ASM.CPU(1)])

    kernel.fileSystem.write("prg1.exe", prg1)
    kernel.fileSystem.write("prg2.exe", prg2)
    kernel.fileSystem.write("prg3.exe", prg3)

    # execute all programs "concurrently"
    kernel.run("prg1.exe", 1)
    kernel.run("prg2.exe", 2)
    kernel.run("prg3.exe", 3)

    HARDWARE.clock.do_ticks(36)
