import multiprocessing, threading
import time
from gunicorn.app.base import BaseApplication
from flask import Flask, render_template
from flask_cors import CORS
from lib import \
    UnitFunctions as unit,\
    Config,\
    Logger

conf = Config.conf
log = Logger.log()

class ViewServer(multiprocessing.Process):
    def __init__(self,heartBeat_queue:multiprocessing.Queue):
        super().__init__()
        self.heartBeat_queue = heartBeat_queue

    def run(self):
        viewServerHeartBeatSender = threading.Thread(target=self.sendHeartBeat, args=()).start()
        try:
            app = Flask(__name__, template_folder="templates")
            CORS(app)
            log.info("View Server started.")
            options = {
                'bind': "{}:{}".format(conf.WebServer_host,conf.ViewServer_port),
                'workers': conf.ViewServer_core,
            }

            @app.route("/")
            @app.route("/dashboard")
            def rootPage():
                return render_template("rootPage.html")

            @app.route("/dashboard-detail/<string:workerID>")
            def dashboardDetail(workerID):
                return render_template("dashboardDetail.html", node=workerID)

            # GunicornFlaskApp(app, options).run()
            app.run(host=conf.WebServer_host, port=conf.ViewServer_port, debug=False)
        except Exception as e:
            log.error("ViewServer ERR | {}".format(e))

    def sendHeartBeat(self):
        while True:
            self.heartBeat_queue.put({"psName": "viewServer"})
            time.sleep(2)

# class GunicornFlaskApp(BaseApplication):
#     def __init__(self, app, options=None):
#         self.options = options or {}
#         self.application = app
#         super().__init__()
#
#     def load_config(self):
#         config = {key: value for key, value in self.options.items()
#                   if key in self.cfg.settings and value is not None}
#         for key, value in config.items():
#             self.cfg.set(key.lower(), value)
#
#     def load(self):
#         return self.application