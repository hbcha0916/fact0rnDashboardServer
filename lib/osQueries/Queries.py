## DynamicQueries #########################################
def setIndexBoxy(shards:int = 1, replicas:int = 0) -> dict:
    # default {shards: 1, replicas: 0} SingleNode
    query = {
        "settings": {
            "number_of_shards": shards,
            "number_of_replicas": replicas
        }
    }
    return query

def getWorkerDetail(workerID:str) -> dict:
    query = {
        "size": 1,
        "query": {
            "bool": {
                "must": [
                    {"match": {"worker_id": workerID}}
                    # (구){"match": {"worker_id": worker}}
                ]
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ]
    }
    return query

def getEventCount(event:str) -> dict:
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"Event": event}}
                ]
            }
        }
    }

    return query

def getEvents(event:str, maxSize:int) -> dict:
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"Event": event}}
                ]
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ],
        "size": maxSize
    }

    return query

def getEvents_Term(event:str, term:str, size:int) -> dict:
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"Event": event}}
                ],
                "filter": [
                    {
                        "range": {
                            "timestamp": {
                                "gte": "now-" + term + "d/d",
                                "lte": "now/d"
                            }
                        }
                    }
                ]
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ],
        "size": size
    }

    return query

def getEventLogsTime(timestamp) -> dict:
    query = {
        "_source": ["Message", "worker_id", "timestamp"],
        "query": {
            "bool": {
                "filter": [
                    {
                        "range": {
                            "timestamp": {
                                "gt": timestamp
                            }
                        }
                    }
                ]
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ],
        "size": 100
    }

    return query

def deleteWorkerStatusQuery(workerID, timestamp) -> dict:
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"worker_id": str(workerID)}},
                    {"range": {"timestamp": {"lt": int(timestamp)}}}
                ]
            }
        }
    }
    return query

def deleteWorker(workerID) -> dict:
    query = {
      "query": {
        "term": {
          "worker_id": workerID
        }
      }
    }

    return query


## StaticQueries ###########################################
setMappingQuery = {
    'properties': {
        'timestamp': {
            'type': 'date'
        },
        'worker_id': {
            'type': 'keyword'
        }
    }
}

getWorkers = {
    "size": 0,
    "aggs": {
        "unique_worker_ids": {
            "terms": {
                "field": "worker_id",
                "size": 10000  # 고유한 worker_id의 최대 개수를 지정합니다. 필요에 따라 조정할 수 있습니다.
            }
        }
    }
}

getWorkerNodes = {
    "size": 0,
    "aggs": {
        "unique_worker_ids": {
            "terms": {
                "field": "worker_id",
                "size": 10000  # 고유한 worker_id의 최대 개수를 지정합니다. 필요에 따라 조정할 수 있습니다.
            }
        }
    }
}

getEventLogs = {
    "_source": ["Message", "worker_id", "timestamp"],

    "sort": [
        {"timestamp": {"order": "desc"}}
    ],
    "size": 100
}
