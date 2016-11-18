from rest_framework import serializers
from prometrix_cloud_security.models import Site, Sensor, Camera, AlarmZone, CameraImage, AlarmLog, Light


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera


class AlarmZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlarmZone


class CameraImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraImage


class AlarmLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlarmLog


class LightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Light

serializer_classes = dict(sites=SiteSerializer, sensors=SensorSerializer, cameras=CameraSerializer,
                          alarm_zones=AlarmZoneSerializer, camera_images=CameraImageSerializer,
                          alarm_logs=AlarmLogSerializer, lights=LightSerializer)


