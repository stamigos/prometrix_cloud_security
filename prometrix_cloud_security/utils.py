import os
import json
from datetime import datetime
from threading import Thread
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


def to_list(str_list):
    """
        Converts string '[item1, item2]' to list [item1, item2]
    """
    return json.loads(str_list) if str_list else []


class ThreadedQueue(object):
    """
        Class for running queues tasks in separated threads
    """
    def __init__(self, concurrent=None):
        self.concurrent = concurrent or 200
        self.queue = Queue(concurrent * 2)
        self.result = {}

    def do_work(self):
        while True:
            url = self.queue.get()
            status, url = self.get_status(url)
            self.result.update({url: status})
            self.queue.task_done()

    def get_status(self, ourl):
        try:
            r = requests.get(ourl)
            return r.status_code, ourl
        except requests.exceptions.RequestException as e:
            return e, ourl

    def run(self, urls_list):
        for i in range(self.concurrent):
            t = Thread(target=self.do_work)
            t.daemon = True
            t.start()

        for url in urls_list:
            self.queue.put(url.strip())
        self.queue.join()

        return self.result

