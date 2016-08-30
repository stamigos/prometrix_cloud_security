from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.models import User
from django.conf.urls.static import static

import views

from rest_framework import routers, serializers, viewsets


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    url(r'^sites/$', views.SitesListView.as_view(), name='sites_list'),
    url(r'^sites/(?P<site_id>\d+)/$', views.SiteDetailView.as_view(), name='site_detail'),
    url(r'^sites/(?P<site_id>\d+)/sensors/$', views.SensorsListView.as_view(), name='sensors_list'),
    url(r'^sites/(?P<site_id>\d+)/sensors/(?P<sensor_id>\d+)/$', views.SensorDetailView.as_view(),
        name='sensor_detail'),
    url(r'^sites/(?P<site_id>\d+)/cameras/$', views.CameraListView.as_view(), name='cameras_list'),
    url(r'^sites/(?P<site_id>\d+)/cameras/(?P<camera_id>\d+)/$', views.CameraDetailView.as_view(),
        name='camera_detail'),
    url(r'^sites/(?P<site_id>\d+)/alarm_zones/$', views.AlarmZonesListView.as_view(), name='alarm_zones_list'),
    url(r'^sites/(?P<site_id>\d+)/alarm_zones/(?P<alarm_zone_id>\d+)/$', views.AlarmZoneDetailView.as_view(),
        name='alarm_zone_detail'),
    url(r'^sites/(?P<site_id>\d+)/(?P<objects>.*)/(?P<object_id>\d+)/enable/$',
        views.ObjectEnableView.as_view(), name='enable_object'),
    url(r'^sites/(?P<site_id>\d+)/(?P<objects>.*)/(?P<object_id>\d+)/disable/$',
        views.ObjectDisableView.as_view(), name='disable_object'),
    url(r'^sites/(?P<site_id>\d+)/alarm_zones/(?P<object_id>\d+)/activate/$', views.ActivateAlarmZoneView,
        name='activate_alarm_zone'),
    url(r'^sites/(?P<site_id>\d+)/cameras/(?P<camera_id>\d+)/images/$', views.CameraImagesList.as_view(),
        name='camera_images_list'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
