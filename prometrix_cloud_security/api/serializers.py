from rest_framework import serializers
from prometrix_cloud_security.models import Site, Sensor, Camera, AlarmZone, CameraImage


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


