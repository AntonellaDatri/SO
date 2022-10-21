class FileSystem:

    def __init__(self):
        self._programs = []

    def write(self, path, program):
        self._programs.append({"Path": path, "Program": program})

    def read(self, path):
        program = None
        for dic in self._programs:
            if path == dic["Path"]:
                program = dic["Program"].instructions
        return program
