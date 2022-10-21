import log


# Emulate victim selection algorithms
class VictimSelection:

    def doSomething(self, page, pageTable, usedFrames):
        log.logger.error("-- METHOD MUST BE OVERRIDEN in class")

    def getVictimFrame(self, usedFrames, pageTables):
        log.logger.error("-- METHOD MUST BE OVERRIDEN in class")


class VictimSelectionFIFO(VictimSelection):

    def doSomething(self, page, pageTable, usedFrames):
        pass

    def getVictimFrame(self, usedFrames, pageTables):
        return usedFrames.pop(0)["frame"]


class VictimSelectionLRU(VictimSelection):

    def doSomething(self, page, pageTable, usedFrames):
        frame = 0
        for ptInfo in pageTable:
            if ptInfo.page == page:
                frame = ptInfo.frame
        for frame1 in usedFrames:
            if frame1["frame"] == frame:
                usedFrames.remove({"frame": frame, "bit": 1})
        usedFrames.append({"frame": frame, "bit": 1})

    def getVictimFrame(self, usedFrames, pageTables):
        return usedFrames.pop(0)["frame"]


class VictimSelectionSecondChance(VictimSelection):
    def doSomething(self, page, pageTable, usedFrames):
        frame = 0
        for ptInfo in pageTable:
            if ptInfo.page == page:
                frame = ptInfo.frame
        for frame1 in usedFrames:
            if frame1["frame"] == frame:
                usedFrames.append({"frame": frame1["frame"], "bit": 1})
                usedFrames.remove(frame1)

    def getVictimFrame(self, usedFrames, pageTables):
        while usedFrames[0]["bit"] != 0:
            usedFrames[0]["bit"] = 0
            frame = usedFrames.pop(0)
            usedFrames.append(frame)
        return usedFrames.pop(0)["frame"]

