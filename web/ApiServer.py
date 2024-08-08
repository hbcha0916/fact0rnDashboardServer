from datetime import datetime
import multiprocessing
from fastapi import FastAPI
from typing import List, Dict
import time
import uvicorn
import threading
from lib.osQueries import Queries
from lib import \
    UnitFunctions as unit, \
    Config, \
    Logger, \
    OpensearchInterface, \
    Pooler

conf = Config.conf
log = Logger.log()
class API_Server(multiprocessing.Process):
    def __init__(self, heartBeat_queue:multiprocessing.Queue):
        super().__init__()
        self.heartBeat_queue = heartBeat_queue

    def sendHeartBeat(self):
        while True:
            self.heartBeat_queue.put({"psName": "apiServer"})
            time.sleep(2)

    def run(self):
        try:
            self.currentBlock = Pooler.GetCurrentBlock()
            self.findAndSuccess = Pooler.GetFindBlockAndSuccess()
            self.dataPooler = Pooler.CurrentPooler()
            self.pooler1 = threading.Thread(target=self.currentBlock.poolingGetBlockFN, args=()).start()
            self.pooler2 = threading.Thread(target=self.findAndSuccess.set, args=()).start()
            self.pooler3 = threading.Thread(target=self.dataPooler.setWorkerNodes, args=()).start()
            self.pooler4 = threading.Thread(target=self.dataPooler.setWorkersDetails, args=()).start()
            apiServerHeartBeatSender = threading.Thread(target=self.sendHeartBeat, args=()).start()
            app = FastAPI()
            self.os = OpensearchInterface.OpensearchSender()

            # 현재 워커들을 출력(keyword가 worker)
            @app.get("/api/workers")
            def getWorkers():
                data = self.dataPooler.getWorkerNodes()
                return {"result": data}

            # 워커Detail을 받아와 구조화로 데이터 변경
            @app.get("/api/struct-data")
            def struData():
                data = self.dataPooler.getStruDatas()
                return {"result": data}

            # 워커ID를 링크에 입력하면 해당 워커ID의 상세정보 출력
            @app.get("/api/workers/{workerID}")
            def getWorkerDetail(workerID:str):
                data = self.dataPooler.getWorkerDetail(workerID)
                return {"result": data}

            # 워커ID들을 리스트로 받아 모든 워커ID의 상세정보 출력
            @app.get("/api/workers-detail")
            def getWorkersDetails():
                data = self.dataPooler.getWorkersDetail()
                return {"result": data}

            # 현재 서버 시작 이후에 블럭이 바뀌면 바뀐 이후의 경과시간
            @app.get("/api/current-block-info")
            async def getCurrentBlockInfo():
                blockCount = self.currentBlock.getBlockCount()
                overTime = time.time() - self.currentBlock.getChangeTime()
                if overTime < 0:
                    overTime = "The block hasn't changed since the server started.\nKeep the server in the on state."
                data = dict({"blockCount": blockCount, "overTime": overTime})
                return {"result": data}

            @app.get("/api/block-mining-count")
            def getFindBlockAndSuccess():
                while True:
                    if self.findAndSuccess.empty():
                        continue
                    else:
                        returnData = self.findAndSuccess.get()
                        return {"result": returnData}

            @app.get("/api/event/logs")
            def getEventlogsAll():
                query = Queries.getEventLogs
                logs = []
                response = self.os.sendGetQuery(query, index="worker_event")
                try:
                    for data in response['hits']['hits']:
                        dt_object = datetime.fromtimestamp(data['_source']['timestamp'] / 1000.0)
                        formatted_date = dt_object.strftime('%Y/%m/%d %H:%M:%S.%f')[:-3]
                        logs.append("[{}] {} | {}".format(formatted_date, data['_source']['worker_id'],
                                                          data['_source']['Message']))
                    return {"result": logs, "lastTime": response['hits']['hits'][0]['_source']['timestamp']}
                except KeyError:
                    return {"result": ["No events yet!"], "lastTime": 0}
                except IndexError:
                    return {"result": ["No events yet!"], "lastTime": 0}

            @app.get("/api/event/logs/ge-{timestamp}")
            def getEventlogs(timestamp:str):
                query = Queries.getEventLogsTime(timestamp)
                response = self.os.sendGetQuery(query, index="worker_event")
                logs = []
                try:
                    for data in response['hits']['hits']:
                        dt_object = datetime.fromtimestamp(data['_source']['timestamp'] / 1000.0)
                        formatted_date = dt_object.strftime('%Y/%m/%d %H:%M:%S.%f')[:-3]
                        logs.append(
                            "[{}] {} | {}".format(formatted_date, data['_source']['worker_id'],
                                                  data['_source']['Message']))

                    return {"result": logs, "lastTime": response['hits']['hits'][0]['_source']['timestamp']}
                except KeyError:
                    return {"result": [], "lastTime": 0}
                except IndexError:
                    return {"result": [], "lastTime ": 0}

            @app.delete("/api/workers/{workerID}")
            def deleteWorker(workerID:str):
                query = Queries.deleteWorker(workerID)
                indices = ["worker_event","worker_client_status","worker_registered","worker_miner_status","worker_start"]
                for index in indices:
                    self.os.sendSetQuery(query, index=index, type="delete")

            log.info("API Server started.")
            uvicorn.run(app, host=conf.WebServer_host, port=conf.APIServer_port)
        except Exception as e:
            log.error("API Server ERR | {}".format(e))