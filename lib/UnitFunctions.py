from json import loads
import time
import requests
from lib import \
    Config,\
    Logger,\
    OpensearchInterface

from lib.osQueries import Queries

conf = Config.conf
confOri = Config.confOri
log = Logger.log()

def checkOpenSearch() -> None:
    isFail = False
    print("Scanning OpenSearch.")
    os = OpensearchInterface.OpensearchSender()

    indices = [
        "WORKER_CLIENT_STATUS",
        "WORKER_EVENT",
        "WORKER_MINER_STATUS",
        "WORKER_REGISTERED",
        "WORKER_START"
    ]
    for i in range(0, len(indices)):
        indices[i] = indices[i].lower()

    indexBody = Queries.setIndexBoxy()

    mapping = Queries.setMappingQuery
    try:
        for index in indices:
            if not os.sendGetQuery(None, type="exists", index=index):
                log.info("The '{}' index does not exist, so we create it.".format(index))
                os.sendSetQuery(indexBody, type="create", index=index)
                os.sendSetQuery(mapping, type="put_mapping", index=index)

        log.info("OpenSearch scan succeeded.")
    except Exception as e:
        log.error("I encountered a problem while scanning Opensearch. Execption | {}".format(e))
        isFail = True
    finally:
        os.connectionClose()
        if isFail:
            exit(1)
    time.sleep(1)

def ckeckConfig() -> None:
    isFail = False
    try:
        for config in confOri.keys():
            if confOri[config] == None and confOri[config] == "":
                log.error("The content of ‘{}‘ in ‘conf’ is None!".format(config))
                isFail = True

        if isFail: exit(1)

        if not conf.LOG_level in ['WARN','WARNING','INFO','DEBUG','ERROR','CRITICAL']:
            log.error("The content of ‘LOG_level’ in ‘conf’ must be one of [‘WARN’,‘WARNING’,‘INFO’,‘DEBUG’,‘ERROR’,‘CRITICAL’].")
            isFail = True

        if conf.DEV_MODE == "Y":
            log.warning("You're running in developer mode.")


    except Exception as e:
        log.error("Something went wrong. Exception [{}]".format(e))
        isFail = True

    finally:
        if isFail: exit(1)

def makeJsonData(message) -> dict:
    parsedJson = loads(message)
    parsedData = {}
    parsedData["index"] = parsedJson["topic"].lower()
    parsedData["datas"] = modifyData(parsedJson["senddata"])
    parsedData["datas"]["timestamp"] = int(time.time() * 1000.0)
    parsedData["datas"]["worker_id"] = "{}_{}".format(parsedData["datas"]["Miner Info"]["Farm"],
                                                      parsedData["datas"]["Miner Info"]["Worker"])

    return parsedData


# async def parsedJson(message, isKafka=False) -> dict:
#     try:
#         if isKafka:
#             data = json.loads(message.value)
#             return data
#         else:
#             data = json.loads(message)
#             return data
#     except Exception as e:
#         log.error("JSON Load Fail | {}".format(message))


def modifyData(data : dict) -> dict:
    dictData = data
    dictDataOri = data
    try:
        # Change CPU INFO
        tmpDic = {}
        for key, value in dictData['CPU Info'].items():
            if 'Frequency' in key:
                if 'Mhz' in value:
                    tmpDic[key+" Mhz"] = float(value.split('Mhz')[0])
            elif 'Usage' in key:
                if '%' in value:
                    tmpDic[key+" Percent"] = float(value.split('%')[0])
            else:
                tmpDic[key] = dictData['CPU Info'][key]

        dictData['CPU Info'] = tmpDic
        tmpDic = {}
        for key, value in dictData['Memory Info'].items():
            if 'GB' in value:
                tmpDic[key + " GB"] = float(value.split('GB')[0])
            elif '%' in value:
                tmpDic[key + " Percent"] = float(value.split('%')[0])
            else:
                tmpDic[key] = dictData['Memory Info'][key]

        dictData['Memory Info'] = tmpDic
        return dictData
    except KeyError as keyError:
        # log.error("keyError {}\ndata {}".format(keyError,dictDataOri))
        return dictDataOri

def workersDetail_to_StruDetail(data):
    struData = {}
    for worker_id, worker_id_values in data.items():
        for workerData, workerDetail in data[worker_id].items():
            if "Miner Info" in workerData:
                if not workerDetail['Farm'] in struData:
                    struData[workerDetail['Farm']] = {}
                if not workerDetail['Group'] in struData:
                    struData[workerDetail['Farm']][workerDetail['Group']] = []

    for worker_id, worker_id_values in data.items():
        for workerData, workerDetail in data[worker_id].items():
            if "Miner Info" in workerData:
                struData[workerDetail['Farm']][workerDetail['Group']].append(workerDetail['Worker'])

    return struData

def isRaceSuccess(height : str, nonce : str) -> dict:
    nodeNonce = str(nonce)
    token = str(requests.get("https://explorer.fact0rn.io/api/getblockhash?index="+height).text)
    factNonce = str(requests.get("https://explorer.fact0rn.io/api/getblock?hash="+token).json()["nonce"])
    if nodeNonce[:-4] == factNonce[:-4]:
        return {"isSuc": True}
    else:
        return {"isSuc": False, "failNonce": nodeNonce, "successNonce": factNonce}
