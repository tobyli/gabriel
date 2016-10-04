#!/usr/bin/env python
#
# Cloudlet Infrastructure for Mobile Computing
#
#   Author: Kiryong Ha <krha@cmu.edu>
#
#   Copyright (C) 2011-2013 Carnegie Mellon University
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import multiprocessing
import time
import Queue
from optparse import OptionParser
import threading
import re
from os import curdir
from os import sep
from BaseHTTPServer import BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer

import os
import sys
if os.path.isdir("../../gabriel"):
    sys.path.insert(0, "../..")
if os.path.isdir("../gabriel"):
    sys.path.insert(0, "..")
import gabriel
import gabriel.proxy
#from gabriel.proxy.common import AppProxyStreamingClient
#from gabriel.proxy.common import AppProxyThread
#from gabriel.proxy.common import ResultpublishClient
#from gabriel.proxy.common import get_service_list
from gabriel.common.config import ServiceMeta as SERVICE_META


share_queue = Queue.Queue()

def process_command_line(argv):
    VERSION = 'gabriel proxy : %s' % gabriel.Const.VERSION
    DESCRIPTION = "Gabriel cognitive assistance"

    parser = OptionParser(usage='%prog [option]', version=VERSION,
            description=DESCRIPTION)

    parser.add_option(
            '-s', '--address', action='store', dest='address',
            help="(IP address:port number) of directory server")
    settings, args = parser.parse_args(argv)
    if len(args) >= 1:
        parser.error("invalid arguement")

    if hasattr(settings, 'address') and settings.address is not None:
        if settings.address.find(":") == -1:
            parser.error("Need address and port. Ex) 10.0.0.1:8081")
    return settings, args

class DummyVideoApp(gabriel.proxy.CognitiveProcessThread):
    def handle(self, header, data):
        global share_queue
        share_queue.put_nowait(data)
        ret = ""
        return ret


class MJPEGStreamHandler(BaseHTTPRequestHandler, object):
    def do_GET(self):
        global share_queue
        self.data_queue = share_queue
        self.result_queue = Queue.Queue()

        try:
            self.path = re.sub('[^.a-zA-Z0-9]', "", str(self.path))
            if self.path== "" or self.path is None or self.path[:1] == ".":
                return
            if self.path.endswith(".html"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type',	'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            if self.path.endswith(".mjpeg"):
                self.send_response(200)
                self.wfile.write("Content-Type: multipart/x-mixed-replace; boundary=--aaboundary")
                self.wfile.write("\r\n\r\n")
                while 1:
                    if self.data_queue.empty() == False:
                        image_data = self.data_queue.get()
                        self.wfile.write("--aaboundary\r\n")
                        self.wfile.write("Content-Type: image/jpeg\r\n")
                        self.wfile.write("Content-length: " + str(len(image_data)) + "\r\n\r\n")
                        self.wfile.write(image_data)
                        self.wfile.write("\r\n\r\n\r\n")
                        time.sleep(0.001)
                return
            if self.path.endswith(".jpeg"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            return
        except IOError:
            self.send_error(404,'File Not Found: %s' % curdir + sep + self.path)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    stopped = False
    #class ThreadedHTTPServer(HTTPServer):
    """Handle requests in a separate thread."""
    def serve_forever(self):
        while not self.stopped:
            self.handle_request()

    def terminate(self):
        self.server_close()
        self.stopped = True

        # close all thread
        if self.socket != -1:
            self.socket.close()


if __name__ == "__main__":
    result_queue = multiprocessing.Queue()
    print result_queue._reader

    settings, args = process_command_line(sys.argv[1:])
    ip_addr, port = gabriel.network.get_registry_server_address(settings.address)
    service_list = gabriel.network.get_service_list(ip_addr, port)

    video_ip = service_list.get(gabriel.ServiceMeta.VIDEO_TCP_STREAMING_IP)
    video_port = service_list.get(gabriel.ServiceMeta.VIDEO_TCP_STREAMING_PORT)
    ucomm_ip = service_list.get(gabriel.ServiceMeta.UCOMM_SERVER_IP)
    ucomm_port = service_list.get(gabriel.ServiceMeta.UCOMM_SERVER_PORT)

    # image receiving and processing threads
    image_queue = Queue.Queue(gabriel.Const.APP_LEVEL_TOKEN_SIZE)
    print "TOKEN SIZE OF OFFLOADING ENGINE: %d" % gabriel.Const.APP_LEVEL_TOKEN_SIZE # TODO
    video_client = gabriel.proxy.SensorReceiveClient((video_ip, video_port), image_queue)
    video_client.start()
    video_client.isDaemon = True

    # dummy video app
    app_thread = DummyVideoApp(image_queue, result_queue, engine_id = 'http_server')
    app_thread.start()
    app_thread.isDaemon = True

    http_server = ThreadedHTTPServer(('0.0.0.0', 7070), MJPEGStreamHandler)
    http_server_thread = threading.Thread(target=http_server.serve_forever)
    http_server_thread.daemon = True
    http_server_thread.start()

    # result pub/sub
    result_pub = gabriel.proxy.ResultPublishClient((ucomm_ip, ucomm_port), result_queue)
    result_pub.start()
    result_pub.isDaemon = True

    try:
        while True:
            time.sleep(1)
    except Exception as e:
        pass
    except KeyboardInterrupt as e:
        sys.stdout.write("user exits\n")
    finally:
        video_client.terminate()
        app_thread.terminate()
        result_pub.terminate()

