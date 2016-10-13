from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.exceptions import APIException

from django.shortcuts import get_object_or_404, get_list_or_404

from prometrix_cloud_security.models import Site, Sensor, Camera, AlarmZone, CameraImage, AlarmLog
from .serializers import SiteSerializer, SensorSerializer, CameraSerializer,\
    AlarmZoneSerializer, CameraImageSerializer, serializer_classes
from prometrix_cloud_security.utils import ThreadedQueue, to_list


def verify_model(objects):
    base_models = dict(alarm_zones=AlarmZone, cameras=Camera, sensors=Sensor, sites=Site)
    try:
        return base_models[objects]
    except KeyError:
        raise APIException("Not found")


class SitesListView(generics.ListAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = SiteSerializer

    def get_queryset(self):
        return get_list_or_404(Site.objects.filter(users__in=[self.request.user.id]))


class SiteDetailView(generics.RetrieveAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = SiteSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = Site.objects.filter(users__in=[self.request.user.id],
                                       pk=kwargs['site_id']).first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class CameraImagesList(generics.ListAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = CameraImageSerializer

    def get_queryset(self):
        return get_list_or_404(CameraImage.filter_camera_images(self.request, self.kwargs))


class SiteObjectsListView(generics.ListAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        model_class = verify_model(self.kwargs['objects'])
        return get_list_or_404(model_class.filter_user_site(self.request, self.kwargs))

    def get_serializer_class(self, *args, **kwargs):
        serializer_class = serializer_classes[self.kwargs['objects']]
        return serializer_class


class SiteObjectDetailView(generics.RetrieveAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        model_class = verify_model(kwargs['objects'])
        query = model_class.filter_user_site(request, kwargs)
        instance = get_object_or_404(query, pk=kwargs['object_id'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_class(self, *args, **kwargs):
        serializer_class = serializer_classes[self.kwargs['objects']]
        return serializer_class


class SiteObjectEnableView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, objects, object_id):
        model_class = verify_model(objects)
        query = model_class.filter_user_site(request, self.kwargs)
        _object = get_object_or_404(query, id=object_id)
        _object.enable()
        return Response({_object.__class__.__name__: dict(id=_object.id, enabled=_object.enabled)})


class SiteObjectDisableView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, objects, object_id):
        model_class = verify_model(objects)

        query = model_class.filter_user_site(request, self.kwargs)
        _object = get_object_or_404(query, id=object_id)
        _object.disable()
        return Response({_object.__class__.__name__: dict(id=_object.id, enabled=_object.enabled)})


class AlarmZoneActivateView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, alarm_zone_id):
        query = AlarmZone.filter_user_site(request, self.kwargs)
        alarm_zone = get_object_or_404(query, id=alarm_zone_id)
        activated_actions, alarm_log = alarm_zone.activate(self.request, self.kwargs)
        if activated_actions and alarm_log:
            return Response(dict(id=alarm_zone.id,
                                 activated=True,
                                 result=dict(
                                     activated_actions=activated_actions,
                                     alarm_log=alarm_log.serialize_to_dict()
                                            )
                                 )
                            )
        return Response(dict(id=alarm_zone.id, activated=False, result={}))


class AlarmZoneDeactivateView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, site_id, alarm_zone_id):
        query = AlarmZone.filter_user_site(request, self.kwargs)
        alarm_zone = get_object_or_404(query, id=alarm_zone_id)
        deactivated_actions, alarm_log = alarm_zone.deactivate(self.request, self.kwargs)
        print deactivated_actions, alarm_log
        if deactivated_actions and alarm_log:
            return Response(dict(id=alarm_zone.id,
                                 deactivated=True,
                                 result=dict(
                                     deactivated_actions=deactivated_actions,
                                     alarm_log=alarm_log.serialize_to_dict()
                                            )
                                 )
                            )
        return Response(dict(id=alarm_zone.id, deactivated=False, result={}))


