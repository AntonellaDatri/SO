## emulates an Input/Output device controller (driver)
class IoDeviceController:

    def __init__(self, device):
        self._device = device
        self._waiting_queue = []
        self._currentPCB = None

    def runOperation(self, pcb, instruction):
        pair = {'pcb': pcb, 'instruction': instruction}
        # append: adds the element at the end of the queue
        self._waiting_queue.append(pair)
        # try to send the instruction to hardware's device (if is idle)
        self.__load_from_waiting_queue_if_apply()

    def getFinishedPCB(self):
        finishedPCB = self._currentPCB
        self._currentPCB = None
        self.__load_from_waiting_queue_if_apply()
        return finishedPCB

    def __load_from_waiting_queue_if_apply(self):
        if (len(self._waiting_queue) > 0) and self._device.is_idle:
            ## pop(): extracts (deletes and return) the first element in queue
            pair = self._waiting_queue.pop(0)
            # print(pair)
            pcb = pair['pcb']
            instruction = pair['instruction']
            self._currentPCB = pcb
            self._device.execute(instruction)

    def __repr__(self):
        return "IoDeviceController for {deviceID} running: {currentPCB} waiting: {waiting_queue}".format(
            deviceID=self._device.deviceId, currentPCB=self._currentPCB, waiting_queue=self._waiting_queue)