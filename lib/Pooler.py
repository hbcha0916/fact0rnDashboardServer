import requests
import time
from lib import \
    Config,\
    Logger,\
    OpensearchInterface,\
    UnitFunctions as unit

from lib.osQueries import Queries

conf = Config.conf
log = Logger.log()

class CurrentPooler():
    serverIsReady = False
    workers = workersDetail = struDatas = None
    def __init__(self):
        self.os = OpensearchInterface.OpensearchSender()

    def setWorkerNodes(self):
        while True:
            query = Queries.getWorkers
            response = self.os.sendGetQuery(query)
            unique_worker_ids = [bucket["key"] for bucket in response["aggregations"]["unique_worker_ids"]["buckets"]]
            unique_worker_ids.sort()
            self.workers = unique_worker_ids
            time.sleep(conf.BackendPoolingDataTimeSec)
    def getWorkerNodes(self):
        # /api/workers
        while True:
            if self.workers:
                return self.workers

    def setWorkersDetails(self):
        while True:
            if self.workers:
                data = {}
                for workerID in self.workers:
                    returnData = {}
                    query = Queries.getWorkerDetail(workerID)
                    response = self.os.sendGetQuery(query)
                    returnData[workerID] = response["hits"]["hits"][0]["_source"]
                    data.update(returnData)
                self.workersDetail = data
                self.struDatas = unit.workersDetail_to_StruDetail(data)
            time.sleep(conf.BackendPoolingDataTimeSec)
    def getWorkersDetail(self):
        while True:
            if self.workersDetail:
                return self.workersDetail

    def getStruDatas(self):
        while True:
            if self.struDatas:
                return self.struDatas

    def getWorkerDetail(self,workerID):
        while True:
            if self.workersDetail:
                return {workerID: self.workersDetail[workerID]}

class GetFindBlockAndSuccess():
    def __init__(self):
        self.os = OpensearchInterface.OpensearchSender()
        self.returnData = {'complete': {}, "find": {}}
        self.now = True

    def empty(self):
        return self.now

    def get(self):
        return self.returnData
    def set(self):
        while True:
            try:
                terms = [1, 7, 30]
                events = ["Complete Factorization", "Find block"]
                eventsMaxSizes = {}
                for event in events:
                    query = Queries.getEventCount(event)
                    response = self.os.sendGetQuery(query,
                                                    index="worker_event",
                                                    type="count")
                    eventsMaxSizes[event] = response["count"]

                ## Total Data
                for event in events:
                    query = Queries.getEvents(event, eventsMaxSizes[event])
                    response = self.os.sendGetQuery(query,
                                                    index="worker_event")
                    if event == "Complete Factorization":
                        tmp = []
                        for i in response['hits']['hits']:
                            tmp.append(float(i['_source']['Message'].split("Factorization ")[-1].split("/")[-1]))

                        try:
                            self.returnData['complete']['total'] = {"count": len(tmp), "avg": round(sum(tmp) / len(tmp), 2)}
                        except ZeroDivisionError:
                            self.returnData['complete']['total'] = {"count": 0, "avg": 0}

                    elif event == "Find block":
                        tmp = []
                        self.returnData['find']['total'] = []
                        failCount = 0
                        for i in response['hits']['hits']:
                            tmp.append(i['_source']['Message'])
                            raceStatus = unit.isRaceSuccess(
                                i['_source']['Message'].split("Height: ")[-1].split(" ")[0],
                                i['_source']['Message'].split("Nonce: ")[-1].split(" ")[0]
                            )
                            if "failNonce" in raceStatus:
                                failCount += 1

                            self.returnData['find']['total'].append(
                                {
                                    "Worker": i['_source']['Miner Info']['Worker'],
                                    "Height": i['_source']['Message'].split("Height: ")[-1].split(" ")[0],
                                    "Nonce": i['_source']['Message'].split("Nonce: ")[-1].split(" ")[0],
                                    "RaceStatus": raceStatus
                                }
                            )

                        self.returnData['find']['total'].append(
                            {
                                "info": {
                                    "FindCount": len(tmp),
                                    "SuccessCount": len(tmp) - failCount,
                                    "FailCount": failCount
                                }
                            }
                        )

                ## Term Data
                for term in terms:
                    for event in events:
                        query = Queries.getEvents_Term(event, str(term), int(eventsMaxSizes[event]))
                        response = self.os.sendGetQuery(query, index="worker_event")
                        if event == "Complete Factorization":
                            tmp = []
                            for i in response['hits']['hits']:
                                tmp.append(float(i['_source']['Message'].split("Factorization ")[-1].split("/")[-1]))
                            try:
                                self.returnData['complete']["{}d".format(term)] = {"count": len(tmp),
                                                                              "avg": round(sum(tmp) / len(tmp), 2)}
                            except ZeroDivisionError:
                                self.returnData['complete']["{}d".format(term)] = {"count": 0,
                                                                              "avg": 0}
                        elif event == "Find block":
                            tmp = []
                            self.returnData['find']["{}d".format(term)] = []
                            failCount = 0
                            for i in response['hits']['hits']:
                                tmp.append(i['_source']['Message'])
                                raceStatus = unit.isRaceSuccess(
                                    i['_source']['Message'].split("Height: ")[-1].split(" ")[0],
                                    i['_source']['Message'].split("Nonce: ")[-1].split(" ")[0]
                                )
                                if "failNonce" in raceStatus:
                                    failCount += 1

                                self.returnData['find']["{}d".format(term)].append(
                                    {
                                        "Worker": i['_source']['Miner Info']['Worker'],
                                        "Height": i['_source']['Message'].split("Height: ")[-1].split(" ")[0],
                                        "Nonce": i['_source']['Message'].split("Nonce: ")[-1].split(" ")[0],
                                        "RaceStatus": raceStatus
                                    }
                                )
                            self.returnData['find']["{}d".format(term)].append(
                                {
                                    "info": {
                                        "FindCount": len(tmp),
                                        "SuccessCount": len(tmp) - failCount,
                                        "FailCount": failCount
                                    }
                                }
                            )
                            self.now = False
                            time.sleep(conf.BackendPoolingLargeDataTimeSec)
            except:
                continue

class GetCurrentBlock():
    url = "https://explorer.fact0rn.io/api/getblockcount"
    blockCount = None
    changeTime = 99999999999
    findBlockAndSuccess = {"msg": "ready"}
    def __init__(self):
        response = requests.get(self.url)
        self.blockCount = response.json()

    def poolingGetBlockFN(self):
        while True:
            try:
                response = requests.get(self.url)
                if self.blockCount != response.json():
                    self.blockCount = response.json()
                    self.changeTime = time.time()
                    log.info("ChangedBlock\'{}\'".format(self.blockCount))
                time.sleep(5)
            except:
                time.sleep(5)
                continue

    def getBlockCount(self):
        return self.blockCount

    def getChangeTime(self):
        return self.changeTime
