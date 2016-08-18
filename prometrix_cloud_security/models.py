from django.db import models


class BaseModel(models.Model):
    class Meta:
        abstract = True

    index = models.IntegerField()  # index to be used for sorting in some lists
    enabled = models.BooleanField()  # if the site is enabled / disabled in the system
    description = models.TextField()  # Site description, like address or other.
    visible = models.BooleanField()  # Visible in the site list
    location = models.TextField()  # gps coordinate, perhaps for later presentation on google maps.
    type = models.IntegerField()  # hardware type


class Site(BaseModel):
    pass


class Sensor(BaseModel):
    heartbeat_updated = models.DateTimeField()  # timestamp for when the sensor heartbeat last communicated with the server
    mac_address = models.CharField()  #
    public_ip = models.CharField()
    alarm_zones = models.ForeignKey(AlarmZone)
    last_alarm = models.DateTimeField()  # Last time sensor set an alarm
    alarm_enable = models.BooleanField() # is the sensor currently in alarm state or not.
    timeout = models.IntegerField()  # number of seconds before next alarm is allowed to trigger from this sensor
    site = models.ForeignKey(Site)  # The site the alarmzone belongs to.


class AlarmZone(BaseModel):
    last_alarm = models.DateTimeField()  # Last time the alarmzone was in alarm
    # enabledSchedule =
    priority = models.IntegerField()  # Different alarmzones can have different priorities
    site = models.ForeignKey(Site)  # The site the alarmzone belongs to.
    # cameras = models.ForeignKey(???)
    # sensors = models.ForeignKey(???)


class AlarmLog(BaseModel):
    last_alarm = models.DateTimeField()  # Last time the alarmzone was in alarm
    alarm_text = models.TextField()  # Text desription for the alarm
    site = models.ForeignKey(Site)
    sensor = models.ForeignKey(Sensor)
    alarm_zone = models.ForeignKey(AlarmZone)
    # images =


class Camera(BaseModel):
    heartbeat_updated = models.DateTimeField()  # timestamp for when the camera heartbeat last communicated with the server
    username = models.CharField()  # IP camera username
    password = models.CharField()  # IP camera password
    public_ip = models.CharField()  # IP to access the camera "online"
    alarm_zone = models.ForeignKey(AlarmZone)  # The alarmzone a sensor can trigger
    site = models.ForeignKey(Site)  # The alarmzone a sensor can trigger
    # save_schedule =


class Light(BaseModel):
    heartbeat_updated = models.DateTimeField()  # timestamp for when the sensor heartbeat last communicated with the server
    mac_address = models.CharField()  # Sensor hardware mac address
    public_ip = models.CharField()
    alarm_zone = models.ForeignKey(AlarmZone)
    status = models.BooleanField()  # is the light currently switched on/off ?
    light_intensity = models.IntegerField()  # light intensity between 0-100%
    site = models.ForeignKey(Site)  # The site the alarmzone belongs to.


class LightGroup(BaseModel):
    status = models.BooleanField()  # is the lightgroup currently switched on/off ?
    light_intensity = models.IntegerField()  # lightgrup intensity between 0-100%
    site = models.ForeignKey(Site)  # The site it belongs to
