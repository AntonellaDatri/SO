from hardware import *
from so import *
import log


##
##  MAIN 
##

if __name__ == '__main__':
    log.setupLogger()
    log.logger.info('Starting emulator')

    ## setup our hardware and set memory size to 25 "cells"
    HARDWARE.setup(25)

    ## new create the Operative System Kernel
    # "booteamos" el sistema operativo
    kernel = Kernel()

    ##  create a program
    # Ahora vamos a intentar ejecutar 3 programas a la vez
    ###################
    prg1 = Program("prg1.exe", [ASM.CPU(2), ASM.IO(), ASM.CPU(3), ASM.IO(), ASM.CPU(2)])
    prg2 = Program("prg2.exe", [ASM.CPU(4), ASM.IO(), ASM.CPU(1)])
    prg3 = Program("prg3.exe", [ASM.CPU(3)])


    # execute all programs "concurrently"
    kernel.run(prg1)
    kernel.run(prg2)
    kernel.run(prg3)
    ## Switch on computer
    HARDWARE.switchOn()

##1. MMU: es una especie de cache entre la memoria y el cpu.
##La MMU se encarga de gestionar la memoria del Hardware, la del SO y la de aplicacion. 	Se suele encontrar en el CPU. Tambien se encarga de asignar la memoria a del SO a los procesos. 	Una mala gestión de memoria es un problema grande cuando se trata de mejorar el rendimiento
##de sistemas de ordenadores.
##También se encarga de transformar direcciones logicas en direcciones fisicas al momento de hacer el fetch(ir a buscar la instruccion a ejecutar) para lo cual se necesita saber la direccion base del proceso y por cual instruccion va

##3. IoDeviceController: contiene que dispositivo es, una lista de espera y el current PCB. RunOperation guarda el PCB y la instruccion . Los añade a la lista, y se fija si corresponde correrlos. Si corresponde se ejecuta el dispositivo y se modifica el current PCB que maneja por el PCB que estaba guardado en la waiting queue.
##Finish lo que hace es volver el current PCB a ninguno, y nuevamente fijarse si corresponde correr a un dispositivo de la waiting queue
##PrinterIODevice: Maneja un ID y un tiempo de ejecucion. Cambia el estado del CPU a ocupado. Va contando los ticks que se van ejucutando, si los ticks que se realizaron son mayores al tiempo de ejecucion del dispositivo, se ejecuta la salida del dispositivo.

##4. IoInInterruptionHandler.execute() e IoOutInterruptionHandler.execute(): El proceso se va ejecutando instruccion por instrucción, mientras el CPU va evaluando que tipo de interrupcion es, cuando evalua y se encuentra con un llamado al IO, llama al vector de interrupcion que maneje ese dispositivo de entrada y salida. De ahi es cuando se llama al exeecute de Io In Interraption Handler.
##Va contando los Ticks que maneja esa intruccion de Entrada, una vez que se cumplieron todos. Se encargan de ejecutar el Io Out Interraption Handler, para salir y que el proceso se siga ejecutando.

##5.1. La CPU no hace nada en ese momento.

##5.2. El branch tardaría 3 ticks más por cada I/O que haya. Lo mejor sería la multiprogramacion


