import json

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics

from prometrix_cloud_security.models import Site, Sensor, Camera, AlarmZone, CameraImage
from .serializers import SiteSerializer, SensorSerializer, CameraSerializer,\
    AlarmZoneSerializer, CameraImageSerializer
from prometrix_cloud_security.utils import ThreadedQueue


class SitesListView(generics.ListAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = SiteSerializer

    def get_queryset(self):
        return Site.objects.filter(users__in=[self.request.user.id])


class SiteDetailView(generics.RetrieveAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = SiteSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = Site.objects.filter(users__in=[self.request.user.id],
                                       pk=kwargs['site_id']).first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)  # if instance else Response({}, status=status.HTTP_404_NOT_FOUND)


class SensorsListView(generics.ListAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = SensorSerializer

    def get_queryset(self):
        return Sensor.objects.filter(site__id=self.kwargs['site_id'],
                                     site__users__in=[self.request.user.id])


class SensorDetailView(generics.RetrieveAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = SensorSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = Sensor.objects.filter(site__id=kwargs['site_id'],
                                         site__users__in=[request.user.id],
                                         pk=kwargs['sensor_id']).first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)  # if instance else Response({}, status=status.HTTP_404_NOT_FOUND)


class CameraListView(generics.ListAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = CameraSerializer

    def get_queryset(self):
        return Camera.objects.filter(site__id=self.kwargs['site_id'],
                                     site__users__in=[self.request.user.id])


class CameraDetailView(generics.RetrieveAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = CameraSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = Camera.objects.filter(site__id=kwargs['site_id'],
                                         site__users__in=[request.user.id],
                                         pk=kwargs['camera_id']).first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)  # if camera else Response({}, status=status.HTTP_404_NOT_FOUND)


class AlarmZonesListView(generics.ListAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = AlarmZoneSerializer

    def get_queryset(self):
        return AlarmZone.objects.filter(site__id=self.kwargs['site_id'],
                                        site__users__in=[self.request.user.id])


class AlarmZoneDetailView(generics.RetrieveAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = AlarmZoneSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = AlarmZone.objects.filter(site__id=kwargs['site_id'],
                                            site__users__in=[request.user.id],
                                            pk=kwargs['alarm_zone_id']).first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class CameraImagesList(generics.ListAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = CameraImageSerializer

    def get_queryset(self):
        return CameraImage.objects.filter(site__id=self.kwargs['site_id'],
                                          site__users__in=[self.request.user.id],
                                          camera__id=self.kwargs['camera_id'])


class ObjectEnableView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, objects, object_id):
        model_class = self._verify_model(objects)
        if not model_class:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        _object = model_class.objects.filter(site__id=site_id,
                                             site__users__in=[request.user.id],
                                             id=object_id).first()
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

        _object = model_class.objects.filter(site__id=site_id,
                                             site__users__in=[request.user.id],
                                             id=object_id).first()
        if _object:
            _object.disable()
            return Response({_object.__class__.__name__: {"id": _object.id, "enabled": _object.enabled}})
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    def _verify_model(self, objects):
        base_models = {"alarm_zones": AlarmZone, "cameras": Camera, "sensors": Sensor, "sites": Site}
        return base_models.get(objects)


class ActivateAlarmZoneView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, alarm_zone_id):
        alarm_zone = AlarmZone.objects.filter(site__id=site_id,
                                              site__users__in=[request.user.id],
                                              id=alarm_zone_id).first()
        if alarm_zone.enabled:
            threaded_queue = ThreadedQueue(concurrent=100)
            activated_actions = json.loads(alarm_zone.activated_actions) if alarm_zone.activated_actions else []
            result = threaded_queue.run(activated_actions)
            return Response({"id": alarm_zone.id, "activated": True, "result": result})
        return Response({"id": alarm_zone.id, "activated": False, "result": None})


class DeactivateAlarmZoneView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, alarm_zone_id):
        alarm_zone = AlarmZone.objects.filter(site__id=site_id,
                                              site__users__in=[request.user.id],
                                              id=alarm_zone_id).first()
        if not alarm_zone.enabled:
            threaded_queue = ThreadedQueue(concurrent=100)
            deactivated_actions = json.loads(alarm_zone.deactivated_actions) if alarm_zone.deactivated_actions else []
            result = threaded_queue.run(deactivated_actions)
            return Response({"id": alarm_zone.id, "activated": True, "result": result})
        return Response({"id": alarm_zone.id, "activated": False, "result": None})


