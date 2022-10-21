class PageTableInfo:

    def __init__(self, pid, page, frame=-1):
        self._pid = pid
        self._page = page
        self._frame = frame
        self._swap = False

    @property
    def pid(self):
        return self._pid

    @property
    def page(self):
        return self._page

    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, frame):
        self._frame = frame

    @property
    def swap(self):
        return self._swap

    @swap.setter
    def swap(self, swap):
        self._swap = swap
