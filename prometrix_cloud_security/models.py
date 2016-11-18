import time
import json
from datetime import datetime
import urlparse

import StringIO

import cronex
import requests
from PIL import Image as PImage

from rest_framework.exceptions import APIException, NotFound


from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.serializers import serialize
from django.shortcuts import get_object_or_404

import utils
from prometrix_cloud_security.utils import ThreadedQueue, to_list
from settings import settings


class BaseModel(models.Model):
    index = models.IntegerField(null=True)  # index to be used for sorting in some lists
    enabled = models.BooleanField(default=True)  # if the site is enabled / disabled in the system
    description = models.TextField(null=True)  # Site description, like address or other.
    visible = models.BooleanField(default=True)  # Visible in the site list
    location = models.TextField(null=True)  # gps coordinate, perhaps for later presentation on google maps.
    type = models.IntegerField(null=True)  # hardware type

    class Meta:
        abstract = True

    def __unicode__(self):
        return '{model_name} (id={id})'.format(
            model_name=self.__class__.__name__, id=self.id
        )

    @classmethod
    def filter_user_site(cls, request, kwargs):
        """
            Filter objects of model for
            particular site which belongs to current user
        """
        return cls.objects.filter(site__id=kwargs['site_id'],
                                  site__users__in=[request.user.id])

    # TODO: remove all to_dict(s)
    def to_dict(self):
        """
        Convert object to dictonary where keys are names
        of attributes and values are values of attributes
        """
        return dict((key, value) for key, value in self.__dict__.iteritems()
                    if not callable(value)
                    and not key.startswith('__')
                    and not key.startswith('_s'))

    def serialize_to_dict(self):
        fields = json.loads(serialize('json', [self, ]))[0].get("fields")
        fields.update(dict(id=self.pk))
        return fields

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

    def __unicode__(self):
        return str('{description} - {status}'.format(description=self.description,
                                                     status="Activated" if self.enabled else "Deactivated"))

    def save_images(self, request, kwargs):
        for camera in self.cameras.all():
            image = CameraImage.objects.filter(site__id=kwargs['site_id'],
                                               site__users__in=[request.user.id],
                                               camera__id=camera.id).first()
            if image:
                image.save()

    def get_sensor(self, request, kwargs):
        sensor = Sensor.filter_user_site(request, kwargs).filter(alarm_zones__in=[kwargs['alarm_zone_id']]).first()
        if not sensor:
            raise NotFound("Sensor for alarm_zone (id={id}) not found".format(id=kwargs['alarm_zone_id']))
        return sensor

    def make_alarm_log_entry(self, request, kwargs):
        sensor = self.get_sensor(request, kwargs)
        alarm_log = AlarmLog(last_alarm=datetime.now(),
                             alarm_text="Some alarm text",
                             alarm_zone=self,
                             site=Site.objects.get(id=kwargs['site_id']),
                             sensor=sensor)
        alarm_log.save()
        return alarm_log

    def enable(self):
        job = cronex.CronExpression(str(self.enabledSchedule))
        if job.check_trigger(time.gmtime(time.time())[:5]) and (not self.enabled):
            self.enabled = True
            self.save()

    def activate(self, request, kwargs):
        if not self.enabled:
            return None, None

        # saving images from cameras
        self.save_images(request, kwargs)

        # create alarm_log
        alarm_log = self.make_alarm_log_entry(request, kwargs)

        # sending requests to URLs in separated threads
        threaded_queue = ThreadedQueue(concurrent=100)
        activated_actions = threaded_queue.run(to_list(self.activated_actions))
        return activated_actions, alarm_log

    def deactivate(self, request, kwargs):
        if self.enabled:
            return None, None

        # create alarm_log
        alarm_log = self.make_alarm_log_entry(request, kwargs)

        # deactivating in separated threads
        threaded_queue = ThreadedQueue(concurrent=100)
        deactivated_actions = threaded_queue.run(to_list(self.deactivated_actions))
        return deactivated_actions, alarm_log


class Sensor(BaseModel):
    heartbeat_updated = models.DateTimeField()  # timestamp for when the sensor heartbeat last communicated with the server
    mac_address = models.CharField(max_length=255)  #
    public_ip = models.CharField(max_length=255)
    alarm_zones = models.ManyToManyField(AlarmZone, related_name='sensors')
    last_alarm = models.DateTimeField()  # Last time sensor set an alarm
    alarm_enable = models.BooleanField() # is the sensor currently in alarm state or not.
    timeout = models.IntegerField()  # number of seconds before next alarm is allowed to trigger from this sensor
    site = models.ForeignKey(Site)  # The site the alarmzone belongs to.
    digital_output = models.IntegerField(null=True)  # (Binary value for the output port, 0=Off, 1=0000 0001, 2=0000 0010)
    ambient_light = models.IntegerField(null=True)  # amibent light between 0-100lux
    digital_inputs = models.IntegerField(null=True)  # (binary value for the digital inputs)
    temperature = models.FloatField(null=True)  # ambient temperature degrees(c)

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

    def to_dict(self):
        """
        Convert object to dictonary where keys are names
        of attributes and values are values of attributes
        """
        return dict((key, value) for key, value in self.__dict__.iteritems()
                    if not callable(value)
                    and not key.startswith('__')
                    and not key.startswith('_s'))

    def serialize_to_dict(self):
        fields = json.loads(serialize('json', [self, ]))[0].get("fields")
        fields.update(dict(id=self.pk))
        return fields


class Light(BaseModel):
    heartbeat_updated = models.DateTimeField()  # timestamp for when the sensor heartbeat last communicated with the server
    mac_address = models.CharField(max_length=255)  # Sensor hardware mac address
    public_ip = models.CharField(max_length=255)
    alarm_zone = models.ForeignKey(AlarmZone)
    status = models.BooleanField()  # is the light currently switched on/off ?
    light_intensity = models.IntegerField()  # light intensity between 0-100%
    site = models.ForeignKey(Site)  # The site the alarmzone belongs to.
    light_mode = models.IntegerField(null=True)  # (1=Standard, 2=Energy save, 3=Boost, 4=Strobe)
    digital_output = models.CharField(null=True, max_length=50)  # (Binary value for the output port, 0=Off, 1=0000 0001, 2=0000 0010)
    ambient_light = models.IntegerField(null=True)  # amibent light between 0-100lux
    digital_inputs = models.IntegerField(null=True)  # (binary value for the digital inputs)
    temperature = models.FloatField(null=True)  # ambient temperature degrees(c)


class LightGroup(BaseModel):
    status = models.BooleanField()  # is the lightgroup currently switched on/off ?
    light_intensity = models.IntegerField()  # lightgrup intensity between 0-100%
    site = models.ForeignKey(Site)  # The site it belongs to
    light = models.ManyToManyField(Light, related_name='lights')  # All the lights in this light group


class CameraImage(models.Model):
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

    @classmethod
    def filter_camera_images(cls, request, kwargs):
        """
            Filter objects of model for particular
            site and camera which belongs to current user
        """
        return cls.objects.filter(site__id=kwargs['site_id'],
                                  site__users__in=[request.user.id],
                                  camera__id=kwargs['camera_id'])

    @classmethod
    def get_last_saved_image(cls, request, site_id):
        return cls.objects.filter(site__id=site_id,
                                  site__users__in=[request.user.id]).order_by("-id").first()
