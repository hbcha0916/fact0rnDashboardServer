import yaml
from pathlib import Path
from types import SimpleNamespace
import os

confOri = yaml.safe_load(Path('/opt/Fact0rnDashboardServer3/conf.yml').read_text())
# confOri = yaml.safe_load(Path('./conf.yml').read_text())

confOri['BackendPoolingDataTimeSec'] = int(confOri['BackendPoolingDataTimeSec'])
confOri['BackendPoolingLargeDataTimeSec'] = int(confOri['BackendPoolingLargeDataTimeSec'])
conf = {}
for confN in confOri.keys():
    tmpName = confN.upper()
    tmp = os.getenv(tmpName, confOri[confN])
    conf[confN] = tmp
    confOri[confN] = tmp

conf = SimpleNamespace(**conf)