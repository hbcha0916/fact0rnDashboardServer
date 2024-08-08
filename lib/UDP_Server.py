import multiprocessing,threading
import time
import socket
from lib import \
    Config,\
    Logger

conf = Config.conf
log = Logger.log()

class UDPReceiver(multiprocessing.Process):
    def __init__(self, udp_queue:multiprocessing.Queue, heartBeat_queue:multiprocessing.Queue):
        super().__init__()
        print("initing..")
        print("Queue is {}".format(udp_queue))
        self.udp_queue = udp_queue
        self.heartBeat_queue = heartBeat_queue

    def run(self):
        log.info("UDP Server Started")
        udpServerHeartBeatSender = threading.Thread(target=self.sendHeartBeat, args=()).start()
        UDP_IP = str(conf.UDP_socket_host)
        UDP_PORT = int(conf.UDP_socket_port)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))

        while True:
            try:
                data, addr = sock.recvfrom(8192)  # buffer size is 1024 bytes
                log.info("데이터 받음 {}".format(data))
                self.udp_queue.put(data)
            except Exception as e:
                log.error("UDP RECV ERR | {}".format(e))
                continue

    def sendHeartBeat(self):
        while True:
            self.heartBeat_queue.put({"psName": "udpReceiver"})
            time.sleep(2)