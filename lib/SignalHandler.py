import multiprocessing, threading
from lib import \
    Logger, \
    ProcessesHandlerInterface

log = Logger.log()

class SignalHandler():
    def __init__(self, processesHandler:ProcessesHandlerInterface.ProcessesHandlerInterface):
        self.processesHandler = processesHandler
        self.processes = self.processesHandler.getProcesses()

    def handleSignal(self, signal, frame):
        log.critical("Shutting down...")
        self.processesHandler.setStopHeartBeat(True)
        for psName, process in self.processes.items():
            process.terminate()
            process.join()

        exit(0)