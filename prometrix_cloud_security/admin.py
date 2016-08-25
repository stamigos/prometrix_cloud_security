from django.contrib import admin
from .models import Site, Sensor, AlarmZone, AlarmLog, Camera, Light, LightGroup, CameraImage

admin.site.register([Site, Sensor, AlarmLog, AlarmZone, Camera, Light, LightGroup, CameraImage])

