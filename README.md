# grupo_8

### Integrantes:

| Nombre y Apellido              |      Mail                      |     usuario Gitlab   |
| -----------------------------  | ------------------------------ | -------------------  |
| AldanaCastro                   | aldanacastro1999@gmail.com     | aldiiicastro         |
| Ignacio Mendez                 | ignacio.mendez0000@gmail.com   | nancio               |
| Antonella D'Atri               |antonella.datri@alu.unq.edu.ar  |antonelladatri        |



### Entregas:

| TP |  Commit  |
| -- | -------- |
| 1  | f21b5214 |
| 2  | af4b87d0 |
| 3  | b4929afb |
| 4  | 474c4070 |
| 5  | 643b7cb2 |
| 6  | a5a21f44 |



#### TP1
    Esta Ok

#### TP2
    Esta OK
* [Este metodo](https://gitlab.com/so-unq-2019-s2-c2/grupo_8/blob/master/practicas/practica_2/so.py#L64) se podria mejorar:
    - [Esta pregunta](https://gitlab.com/so-unq-2019-s2-c2/grupo_8/blob/master/practicas/practica_2/so.py#L67) se podria delegar al Kernel
    - [Estas](https://gitlab.com/so-unq-2019-s2-c2/grupo_8/blob/master/practicas/practica_2/so.py#L68) [dos](https://gitlab.com/so-unq-2019-s2-c2/grupo_8/blob/master/practicas/practica_2/so.py#L69) son un poco mas graves porque ademas de romper el encapsulamiento para preguntar el valor lo modifican, esa modificacion tiene logica asociada (poca pero logica la fin) que podria estar en el Kernel

#### TP3
    En terminos generales esta bien, pero se podria mejorar:
    
* [El Dispatcher](https://gitlab.com/so-unq-2019-s2-c2/grupo_8/blob/master/practicas/practica_3/so.py#L173) esta siendo usado como una clase estatica, no es esta mal, pero definirlo asi es incorrecto en Python les sugiero que lean [esto](https://docs.python.org/3/library/functions.html#classmethod) y [esto](https://docs.python.org/3/library/functions.html#staticmethod) 
* [Esto](https://gitlab.com/so-unq-2019-s2-c2/grupo_8/blob/master/practicas/practica_3/so.py#L148) se podria delegar a la PCBTable simplemente preguntando si hay algun PCB en ejecucion
* Esta bien que no tengan los estados como string planos:
    ```python
    NEW = State ("new")
    TERMINATED = State ("terminated")
    READY = State ("ready")
    RUNNING = State ("running")
    WAITING = State ("waiting")
    ```
    En lugar de tener instancias sueltas podrian tener un enum o al menos una clase que contengan los estados, algo asi:
    ```python
    from enum import Enum
    class States(Enum):
        NEW = "NEW"
        TERMINATED = "TERMINATED"
        READY = "READY"
        RUNNING = "RUNNING"
        WAITING = "WAITING"
    ```
    
    O asi:
    
    ```python
    class States():
        NEW = "NEW"
        TERMINATED = "TERMINATED"
        READY = "READY"
        RUNNING = "RUNNING"
        WAITING = "WAITING"
    ```







