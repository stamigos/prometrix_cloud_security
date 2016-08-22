"""prometrix_cloud_security URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from . import views

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
    # url(r'^login/$', views.LoginView.as_view(), name='login'),
    # url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    # url(r'^sites/$', login_required(views.SiteListView.as_view(), login_url='/login/'), name='sites'),
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

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/', admin.site.urls),
]
