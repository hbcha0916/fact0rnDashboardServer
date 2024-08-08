import multiprocessing
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import requests
from lib import \
    Config, \
    Logger

conf = Config.conf
log = Logger.log()
class ProxyServer(multiprocessing.Process):
    def __init__(self,heartBeat_queue:multiprocessing.Queue):
        super().__init__()
        self.heartBeat_queue = heartBeat_queue

    def sendHeartBeat(self):
        while True:
            self.heartBeat_queue.put({"psName": "proxyServer"})
            time.sleep(2)

    def run(self):
        proxyServerHeartBeatSender = threading.Thread(target=self.sendHeartBeat, args=()).start()
        try:
            httpd = HTTPServer((conf.WebServer_host, conf.ProxyServerPort), ProxyHandler)
            httpd.serve_forever()
        except Exception as e:
            log.error("ProxyServer ERR 0 | {}".format(e))
            pass


class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request()

    def do_POST(self):
        self.proxy_request()

    def proxy_request(self):
        try:
            parsed_url = urlparse(self.path)
            if parsed_url.path.startswith('/api'):
                target_url = f'http://127.0.0.1:2648{self.path}'
            else:
                target_url = f'http://127.0.0.1:2649{self.path}'

            method = self.command
            headers = {key: value for key, value in self.headers.items()}
            body = None
            if method == 'POST':
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)

            response = requests.request(method, target_url, headers=headers, data=body)

            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        except Exception as e:
            log.error("ProxyServer ERR 1 | {}".format(e))
            pass


