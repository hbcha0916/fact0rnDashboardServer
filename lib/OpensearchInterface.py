import multiprocessing, threading
import time
from queue import Empty
from opensearchpy import OpenSearch
from lib import \
    UnitFunctions as unit, \
    Config, \
    Logger
from lib.osQueries import Queries

conf = Config.conf
log = Logger.log()

class OpensearchInputUDP_Data(multiprocessing.Process):
    def __init__(self, udp_queue:multiprocessing.Queue, heartBeat_queue:multiprocessing.Queue):
        super().__init__()
        self.udp_queue = udp_queue
        self.heartBeat_queue = heartBeat_queue
        self.os = OpenSearch(
            hosts=[{"host": conf.OS_host, "port": conf.OS_port}],
            verify_certs=False,
            pool_maxsize=30
        )

    def run(self):
        log.info("OS Sender started.")
        osServerHeartBeatSender = threading.Thread(target=self.sendHeartBeat, args=()).start()
        try:
            while True:
                try:
                    if self.udp_queue.empty():
                        continue
                    else:
                        udpText = self.udp_queue.get()
                        data = unit.makeJsonData(udpText)
                        self.os.index(index=data['index'], body=data['datas'])

                except KeyError as k:
                    log.error("OpensearchInputUDP_Data.run Key ERROR | {}".format(k))

                except Exception as e:
                    log.error("OpensearchInputUDP_Data.run ERROR | {}".format(e))
        finally:
            self.os.close()

    def sendHeartBeat(self):
        while True:
            self.heartBeat_queue.put({"psName": "osInputSender"})
            time.sleep(2)

class OutdatedDataHandler:
    def __init__(self):
        self.os = OpensearchSender()

    def deleteData(self):
        while True:
            query = Queries.getWorkers
            response = self.os.sendGetQuery(query)
            unique_worker_ids = [bucket["key"] for bucket in response["aggregations"]["unique_worker_ids"]["buckets"]]
            unique_worker_ids.sort()
            workers = unique_worker_ids

            for workerID in workers:
                query = Queries.getWorkerDetail(workerID)
                response = self.os.sendGetQuery(query)
                dataTimeStamp = int(response["hits"]["hits"][0]["_source"]["timestamp"])
                delQuery = Queries.deleteWorkerStatusQuery(workerID, dataTimeStamp)
                self.os.sendSetQuery(delQuery, index="worker_client_status", type="delete")



            time.sleep(60)



class OpensearchSender:
    def __init__(self):
        self.os = OpenSearch(
            hosts=[{"host": conf.OS_host, "port": conf.OS_port}],
            verify_certs=False,
            pool_maxsize=30
        )

    def connectionClose(self):
        self.os.close()

    def sendGetQuery(self, query, index="worker_client_status", type="search"):
        try:
            if type == "search":
                response = self.os.search(
                    body=query,
                    index=index
                )
                return response
            elif type == "count":
                response = self.os.count(
                    body=query,
                    index=index
                )
                return response

            elif type == "exists":
                return self.os.indices.exists(index=index)
        except Exception as e:
            log.error("OpensearchInterface.sendGetQuery ERR | {}".format(e))



    def sendSetQuery(self, body, index=None, type=None):
        try:
            if type == "create":
                self.os.indices.create(index=index, body=body)

            elif type == "put_mapping":
                self.os.indices.put_mapping(index=index, body=body)

            elif type == "delete":
                self.os.delete_by_query(body=body, index=index)
        except Exception as e:
            log.error("OpensearchInterface.sendSetQuery ERR | {}".format(e))




    def getOS_Object(self):
        return self.os