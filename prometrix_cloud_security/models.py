import time
from datetime import datetime
import urlparse

import StringIO

import cronex
import requests
from PIL import Image as PImage


from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

import utils
from settings import settings


class BaseModel(models.Model):
    index = models.IntegerField()  # index to be used for sorting in some lists
    enabled = models.BooleanField()  # if the site is enabled / disabled in the system
    description = models.TextField()  # Site description, like address or other.
    visible = models.BooleanField()  # Visible in the site list
    location = models.TextField()  # gps coordinate, perhaps for later presentation on google maps.
    type = models.IntegerField()  # hardware type

    class Meta:
        abstract = True

    def to_dict(self):
        """
        Convert object to dictonary where keys are names
        of attributes and values are values of attributes
        """
        return dict((key, value) for key, value in self.__dict__.iteritems()
                    if not callable(value)
                    and not key.startswith('__')
                    and not key.startswith('_s'))

    def enable(self):
        if not self.enabled:
            self.enabled = True
            self.save()

    def disable(self):
        if self.enabled:
            self.enabled = False
            self.save()


class Site(BaseModel):
    users = models.ManyToManyField(User)

    def __unicode__(self):
        return self.description


class Camera(BaseModel):
    heartbeat_updated = models.DateTimeField()  # timestamp for when the camera heartbeat last communicated with the server
    username = models.CharField(max_length=255)  # IP camera username
    password = models.CharField(max_length=255)  # IP camera password
    public_ip = models.CharField(max_length=255)  # IP to access the camera "online"
    site = models.ForeignKey(Site)  # The alarmzone a sensor can trigger
    image_url = models.CharField(max_length=255, default='http://185.70.145.75/jpg/image.jpg')
    # save_schedule =


class AlarmZone(BaseModel):
    last_alarm = models.DateTimeField()  # Last time the alarmzone was in alarm
    enabledSchedule = models.CharField(max_length=150, default='* * * * *')
    priority = models.IntegerField()  # Different alarmzones can have different priorities
    site = models.ForeignKey(Site)  # The site the alarmzone belongs to.
    cameras = models.ManyToManyField(Camera, related_name='alarm_zones')
    activated_actions = models.TextField(blank=True)  #  a list of custom URLs that will be requested when the alarmzone activated API command is triggered
    deactivated_actions = models.TextField(blank=True) #  a list of custom URLs that will be requested when the alarmzone deactivated API command is triggered

    def to_dict(self):
        result = dict((key, value) for key, value in self.__dict__.iteritems()
                      if not callable(value)
                      and not key.startswith('__')
                      and not key.startswith('_s'))
        result.update({"sensors": [snr.id for snr in self.sensors.all()]})
        result.update({"cameras": [snr.id for snr in self.cameras.all()]})
        return result

    def enable(self):
        job = cronex.CronExpression(str(self.enabledSchedule))
        if job.check_trigger(time.gmtime(time.time())[:5]) and (not self.enabled):
            self.enabled = True
            self.save()

    def __unicode__(self):
        return str('{description} - {status}'.format(description=self.description,
                                                     status="Activated" if self.enabled else "Deactivated"))


class Sensor(BaseModel):
    heartbeat_updated = models.DateTimeField()  # timestamp for when the sensor heartbeat last communicated with the server
    mac_address = models.CharField(max_length=255)  #
    public_ip = models.CharField(max_length=255)
    alarm_zones = models.ManyToManyField(AlarmZone, related_name='sensors')
    last_alarm = models.DateTimeField()  # Last time sensor set an alarm
    alarm_enable = models.BooleanField() # is the sensor currently in alarm state or not.
    timeout = models.IntegerField()  # number of seconds before next alarm is allowed to trigger from this sensor
    site = models.ForeignKey(Site)  # The site the alarmzone belongs to.

    def to_dict(self):
        result = dict((key, value) for key, value in self.__dict__.iteritems()
                      if not callable(value)
                      and not key.startswith('__')
                      and not key.startswith('_s'))
        result.update({"alarm_zones": [amz.id for amz in self.alarm_zones.all()]})
        return result


class AlarmLog(BaseModel):
    last_alarm = models.DateTimeField()  # Last time the alarmzone was in alarm
    alarm_text = models.TextField()  # Text desription for the alarm
    site = models.ForeignKey(Site)
    sensor = models.ForeignKey(Sensor)
    alarm_zone = models.ForeignKey(AlarmZone)
    # images =


class Light(BaseModel):
    heartbeat_updated = models.DateTimeField()  # timestamp for when the sensor heartbeat last communicated with the server
    mac_address = models.CharField(max_length=255)  # Sensor hardware mac address
    public_ip = models.CharField(max_length=255)
    alarm_zone = models.ForeignKey(AlarmZone)
    status = models.BooleanField()  # is the light currently switched on/off ?
    light_intensity = models.IntegerField()  # light intensity between 0-100%
    site = models.ForeignKey(Site)  # The site the alarmzone belongs to.


class LightGroup(BaseModel):
    status = models.BooleanField()  # is the lightgroup currently switched on/off ?
    light_intensity = models.IntegerField()  # lightgrup intensity between 0-100%
    site = models.ForeignKey(Site)  # The site it belongs to


class CameraImage(models.Model):
    # IMAGE_PATH = settings.MEDIA_ROOT + '/cam/pictures'
    # IMAGE_THUMB_PATH = settings.MEDIA_ROOT + '/cam/pictures'

    camera = models.ForeignKey(Camera)
    image_data = models.ImageField(upload_to=utils.gen_save_path, blank=True)
    image_data_thumb = models.ImageField(upload_to=utils.gen_save_path_thumb, blank=True)
    site = models.ForeignKey(Site)
    logged = models.DateTimeField(auto_now_add=True)
    meta = models.CharField(max_length=400, blank=True)

    def save(self, *args, **kwargs):
        parsed_url = urlparse.urlparse(self.camera.image_url)
        if parsed_url.username and parsed_url.password:
            r = requests.get(self.camera.image_url,
                             auth=(parsed_url.username, parsed_url.password))
        else:
            r = requests.get(self.camera.image_url)

        filename = "temp.jpg"

        self.image_data.save(
            filename,
            ContentFile(r.content),
            save=False
        )
        self.create_thumb(self.image_data.path)

        super(CameraImage, self).save(*args, **kwargs)

    def create_thumb(self, image_path):
        filename = image_path
        im = PImage.open(image_path)
        im.thumbnail((150, 150), PImage.ANTIALIAS)
        temp_handle = StringIO.StringIO()
        im.save(temp_handle, 'jpeg')
        temp_handle.seek(0)

        self.image_data_thumb.save(
            filename,
            ContentFile(temp_handle.read()),
            save=False
        )

    def delete(self, *args, **kwargs):
        print "delete file"
        storage_image, path = self.image_data.storage, self.image_data.path
        storage_thumb, path = self.image_data_thumb.storage, self.image_data_thumb.path
        super(CameraImage, self).delete(*args, **kwargs)
        storage_image.delete(path)
        storage_thumb.delete(path)

    def __unicode__(self):
        return settings.MEDIA_URL + self.image_data.name

    def to_dict(self):
        return dict((key, value) for key, value in self.__dict__.iteritems()
                    if not callable(value)
                    and not key.startswith('__')
                    and not key.startswith('_s'))
