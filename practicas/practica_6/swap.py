class Swap:
    def __init__(self, fileSystem, victimSelection):
        self._fileSystem = fileSystem
        self._victimSelection = victimSelection
        self._cache = []

    def addCache(self, ptInfo, instructions):
        self._cache.append({"ptInfo": ptInfo, "pid": ptInfo.pid, "instructions": instructions})

    def program(self, pageInfo, path):
        if pageInfo.swap:
            program = self.readCache(pageInfo)
        else:
            program = self._fileSystem.read(path)
        return program

    def readCache(self, pageInfo):
        for dicPI in self._cache:
            if dicPI["ptInfo"].page == pageInfo.page and dicPI["pid"] == pageInfo.pid:
                return dicPI["instructions"]

    @property
    def victimSelection(self):
        return self._victimSelection

    @property
    def fileSystem(self):
        return self._fileSystem
