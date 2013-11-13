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

import sys
sys.path.insert(0, "../common")
import time
import Queue

from app_proxy import AppProxyThread
from app_proxy import AppProxyStreamingClient
from app_proxy import get_service_list
from app_proxy import SERVICE_META
import ocr_server


class OCRThread(AppProxyThread):

    def handle(self, header, data):
        ret_str = ocr_server.run_ocr(data)
        if ret_str is not None and len(ret_str.strip()) > 0:
            return ret_str.strip()


if __name__ == "__main__":
    sys.stdout.write("Start OCR proxy\n")
    image_queue = Queue.Queue(1)
    output_queue = Queue.Queue()

    service_list = get_service_list()
    video_ip = service_list.get(SERVICE_META.VIDEO_TCP_STREAMING_ADDRESS)
    video_port = service_list.get(SERVICE_META.VIDEO_TCP_STREAMING_PORT)

    client = AppProxyStreamingClient((video_ip, video_port), image_queue, output_queue)
    client.start()
    client.isDaemon = True
    app_thread = OCRThread(image_queue, output_queue)
    app_thread.start()
    app_thread.isDaemon = True

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        sys.stdout.write("user exits\n")
        client.terminate()
        app_thread.terminate()
    except Exception as e:
        client.terminate()
        app_thread.terminate()
