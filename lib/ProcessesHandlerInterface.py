import multiprocessing, time
from lib import \
    Config, \
    Logger, \
    UDP_Server, \
    OpensearchInterface

from web import \
    ApiServer, \
    ViewServer
    # ProxyServer


conf = Config.conf
log = Logger.log()

class ProcessesHandlerInterface():
    def __init__(self,
                 udp_queue: multiprocessing.Queue,
                 heartBeat_queue: multiprocessing.Queue,
                 initMode=True):

        self.processes = {
            "udpReceiver" : UDP_Server.UDPReceiver(udp_queue, heartBeat_queue),
            "osInputSender" : OpensearchInterface.OpensearchInputUDP_Data(udp_queue, heartBeat_queue),
            # "proxyServer" : ProxyServer.ProxyServer(heartBeat_queue),
            "apiServer" : ApiServer.API_Server(heartBeat_queue),
            "viewServer" : ViewServer.ViewServer(heartBeat_queue)
        }
        self.udp_queue = udp_queue
        self.heartBeat_queue = heartBeat_queue
        self.processesTime = {
            "udpReceiver" : time.time(),
            "osInputSender" : time.time(),
            # "proxyServer" : time.time(),
            "apiServer" : time.time(),
            "viewServer" : time.time()
        }

        self.processesDeadCount = {
            "udpReceiver": 0,
            "osInputSender": 0,
            # "proxyServer": 0,
            "apiServer": 0,
            "viewServer": 0
        }
        self.stopHeartBeat = False
        if initMode:
            self.createProcess(initMode=initMode)

    def getProcesses(self):
        return self.processes

    def printStatus(self):
        print("**************| Processes Status |**************")
        print("==| Processes DeathCount |==")
        print(self.processesDeadCount)
        print()
        print("==| Processes RunningTime |==")
        print(self.processesTime)

    def listenHeartBeat(self):
        lastTime = time.time()+100
        while True:
            currentTime = time.time()
            if self.stopHeartBeat:
                break
            else:
                if self.heartBeat_queue.empty():
                    self.checkDeadProcessor()
                else:
                    heartBeat = self.heartBeat_queue.get()
                    log.info("The {} processor is alive.".format(heartBeat['psName']))
                    self.processesTime[heartBeat['psName']] = time.time()

            if currentTime - lastTime >= 60 or currentTime - lastTime < 0:
                self.printStatus()
                lastTime = time.time()


    def setStopHeartBeat(self,control:bool):
        self.stopHeartBeat = control

    def checkDeadProcessor(self):
        for psName, processLastTime in self.processesTime.items():
            if (time.time() - processLastTime) > 60:
                self.processKiller(psName)
                self.createProcess(psName=psName)
                self.processesDeadCount[psName] += 1
            else:
                continue

    def processKiller(self, psName):
        self.processes[psName].terminate()
        self.processes[psName].join()


    def createProcess(self, initMode=False, psName=None):
        if initMode:
            for psName, ps in self.processes.items():
                print("{} process starting".format(psName))
                ps.start()

        if not initMode:
            print("The {} processor is restarted.".format(psName))
            if psName == "udpReceiver":
                self.processes["udpReceiver"] = UDP_Server.UDPReceiver(self.udp_queue, self.heartBeat_queue)
                self.processesTime["udpReceiver"] = time.time()
                self.processes["udpReceiver"].start()

            elif psName == "osInputSender":
                self.processes["osInputSender"] = OpensearchInterface.OpensearchInputUDP_Data(self.udp_queue, self.heartBeat_queue)
                self.processesTime["osInputSender"] = time.time()
                self.processes["osInputSender"].start()

            # elif psName == "proxyServer":
            #     self.processes["proxyServer"] = ProxyServer.ProxyServer(self.heartBeat_queue)
            #     self.processesTime["proxyServer"] = time.time()
            #     self.processes["proxyServer"].start()

            elif psName == "apiServer":
                self.processes["apiServer"] = ApiServer.API_Server(self.heartBeat_queue)
                self.processesTime["apiServer"] = time.time()
                self.processes["apiServer"].start()

            elif psName == "viewServer":
                self.processes["viewServer"] = ViewServer.ViewServer(self.heartBeat_queue)
                self.processesTime["viewServer"] = time.time()
                self.processes["viewServer"].start()


