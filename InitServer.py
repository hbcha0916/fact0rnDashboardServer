import multiprocessing, threading
import signal
from lib import \
    UnitFunctions as unit, \
    Config, \
    Logger, \
    SignalHandler, \
    ProcessesHandlerInterface



conf = Config.conf
log = Logger.log()

def startProcesses():
    udp_queue = multiprocessing.Queue()
    heartBeat_queue = multiprocessing.Queue()

    processesHandler = ProcessesHandlerInterface.ProcessesHandlerInterface(
        udp_queue,
        heartBeat_queue
    )

    processesHandlerThread = threading.Thread(target=processesHandler.listenHeartBeat
                                              , args=())

    processesHandlerThread.start()

    signal_handler = SignalHandler.SignalHandler(processesHandler)
    signal.signal(signal.SIGTERM, signal_handler.handleSignal)
    signal.signal(signal.SIGINT, signal_handler.handleSignal)

    # for process in processes:
    #     process.join()

if __name__ == "__main__":
    welcome = r"""
  __               _    _____              
 / _|             | |  |  _  |             
| |_   __ _   ___ | |_ | |/' | _ __  _ __  
|  _| / _` | / __|| __||  /| || '__|| '_ \ 
| |  | (_| || (__ | |_ \ |_/ /| |   | | | |
|_|   \__,_| \___| \__| \___/ |_|   |_| |_|                     
"""
    print(welcome)
    unit.ckeckConfig()
    unit.checkOpenSearch()
    startProcesses()
