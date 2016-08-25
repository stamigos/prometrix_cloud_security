from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .models import Site, Sensor, Camera, AlarmZone


class SitesListView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        content = {
            'user': unicode(request.user),  # `django.contrib.auth.User` instance.
            'auth': unicode(request.auth),  # None
        }
        sites = {"sites": [{"index": site.index,
                            "enabled": site.enabled,
                            "description": site.description,
                            "visible": site.location,
                            "type": site.type,
                            "users": [user.id for user in site.users.all()]
                            } for site in Site.objects.filter(users__in=[self.request.user.id])
                           ]}

        return Response(sites)


class SiteDetailView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id):
        site = Site.objects.filter(users__in=[self.request.user.id], pk=site_id).first()
        return Response(site.to_dict()) if site else Response({}, status=status.HTTP_404_NOT_FOUND)


class SensorsListView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id):
        sensors = Sensor.objects.filter(site__id=site_id, site__users__in=[self.request.user.id])
        return Response({"sensors": [sensor.to_dict() for sensor in sensors]})


class SensorDetailView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, sensor_id):
        sensor = Sensor.objects.filter(site__id=site_id, site__users__in=[self.request.user.id], pk=sensor_id).first()
        return Response(sensor.to_dict()) if sensor else Response({}, status=status.HTTP_404_NOT_FOUND)


class CameraListView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id):
        return Response({"cameras": [camera.to_dict() for camera in Camera.objects.filter(site__id=site_id)]})


class CameraDetailView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, camera_id):
        camera = Camera.objects.filter(site__id=site_id).filter(site__users__in=[self.request.user.id]).filter(pk=camera_id).first()
        return Response(camera.to_dict()) if camera else Response({}, status=status.HTTP_404_NOT_FOUND)


class AlarmZonesListView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id):
        return Response({"alarm_zones":
                        [alarm_zone.to_dict() for alarm_zone in AlarmZone.objects.filter(site__id=site_id)]})


class AlarmZoneDetailView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, alarm_zone_id):
        alarm_zone = AlarmZone.objects.filter(site__id=site_id).filter(site__users__in=[self.request.user.id]).filter(pk=alarm_zone_id).first()
        return Response(alarm_zone.to_dict()) if alarm_zone else Response({}, status=status.HTTP_404_NOT_FOUND)


class ObjectEnableView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, objects, object_id):
        model_class = self._verify_model(objects)
        if not model_class:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        _object = model_class.objects.filter(id=object_id).first()
        if _object:
            _object.enable()
            return Response({_object.__class__.__name__: {"id": _object.id, "enabled": _object.enabled}})
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    def _verify_model(self, objects):
        base_models = {"alarm_zones": AlarmZone, "cameras": Camera, "sensors": Sensor, "sites": Site}
        return base_models.get(objects)


class ObjectDisableView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, objects, object_id):
        model_class = self._verify_model(objects)
        if not model_class:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        _object = model_class.objects.filter(id=object_id).first()
        if _object:
            _object.disable()
            return Response({_object.__class__.__name__: {"id": _object.id, "enabled": _object.enabled}})
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    def _verify_model(self, objects):
        base_models = {"alarm_zones": AlarmZone, "cameras": Camera, "sensors": Sensor, "sites": Site}
        return base_models.get(objects)
