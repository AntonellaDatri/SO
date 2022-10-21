from hardware import *

class Program:

    def __init__(self, instructions):
        self._instructions = self.expand(instructions)

    @property
    def instructions(self):
        return self._instructions

    def addInstr(self, instruction):
        self._instructions.append(instruction)

    @staticmethod
    def expand(instructions):
        expanded = []
        for i in instructions:
            if isinstance(i, list):
                ## is a list of instructions
                expanded.extend(i)
            else:
                ## a single instr (a String)
                expanded.append(i)

        ## now test if last instruction is EXIT
        ## if not... add an EXIT as final instruction
        last = expanded[-1]
        if not ASM.isEXIT(last):
            expanded.append(INSTRUCTION_EXIT)

        return expanded

    def __repr__(self):
        return "Program({instructions})".format(instructions=self._instructions)

