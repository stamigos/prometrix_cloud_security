import os
# import sys
from datetime import datetime
# from urlparse import urlparse
from threading import Thread
# import httplib
from Queue import Queue

import requests
from settings import settings


def ensure_dir(f):
    if not os.path.exists(f):
        os.makedirs(f)


def gen_save_path(instance, filename):
    path = r'cam/pictures/{cam_id}'.format(cam_id=str(instance.camera.id))
    ensure_dir(settings.MEDIA_ROOT + "/" + path + "/")
    dt_now = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    return '{path}/{fname}.{extension}'.format(path=path, fname=dt_now, extension='jpg')


def gen_save_path_thumb(instance, filename):
    path = r'cam/pictures/{cam_id}'.format(cam_id=str(instance.camera.id))
    ensure_dir(settings.MEDIA_ROOT + "/" + path + "/")
    dt_now = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    return '{path}/{fname}.{extension}'.format(path=path, fname="150x150_"+dt_now, extension='jpg')


class ThreadedQueue(object):
    def __init__(self, concurrent=None):
        self.concurrent = concurrent or 200
        self.queue = Queue(concurrent * 2)
        self.result = {}

    def do_work(self):
        while True:
            url = self.queue.get()
            status, url = self.get_status(url)
            self.result.update({url: status})
            # self.do_something_with_result(status, url)
            self.queue.task_done()

    def get_status(self, ourl):
        try:
            r = requests.get(ourl)
            return r.status_code, ourl
        except requests.exceptions.RequestException as e:
            return e, ourl

    # def do_something_with_result(self, status, url):
    #     print status, url

    def run(self, urls_list):
        for i in range(self.concurrent):
            t = Thread(target=self.do_work)
            t.daemon = True
            t.start()
        # try:
        for url in urls_list:
            self.queue.put(url.strip())
        self.queue.join()

        return self.result
        # except KeyboardInterrupt:
        #     sys.exit(1)
