import os
from datetime import datetime
import settings


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
