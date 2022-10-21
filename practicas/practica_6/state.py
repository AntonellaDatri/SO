# Emulates the States
class State:
    def __init__(self, type):
        self._type = type

    def type(self):
        return self._type


NEW = State("new")
TERMINATED = State("terminated")
READY = State("ready")
RUNNING = State("running")
WAITING = State("waiting")
