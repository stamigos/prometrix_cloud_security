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
    url(r'^sites/(?P<site_id>\d+)/(?P<objects>.*)/(?P<object_id>\d+)/enable/$',
        views.SiteObjectEnableView.as_view(), name='enable_object'),
    url(r'^sites/(?P<site_id>\d+)/(?P<objects>.*)/(?P<object_id>\d+)/disable/$',
        views.SiteObjectDisableView.as_view(), name='disable_object'),
    url(r'^sites/(?P<site_id>\d+)/alarm_zones/(?P<alarm_zone_id>\d+)/activate/$',
        views.AlarmZoneActivateView.as_view(), name='activate_alarm_zone'),
    url(r'^sites/(?P<site_id>\d+)/alarm_zones/(?P<alarm_zone_id>\d+)/deactivate/$',
        views.AlarmZoneDeactivateView.as_view(), name='deactivate_alarm_zone'),
    url(r'^sites/(?P<site_id>\d+)/cameras/(?P<camera_id>\d+)/images/$', views.CameraImagesList.as_view(),
        name='camera_images_list'),
    url(r'^sites/(?P<site_id>\d+)/(?P<objects>.*)/(?P<object_id>\d+)/$', views.SiteObjectDetailView.as_view(),
        name='object_detail_view'),
    url(r'^sites/(?P<site_id>\d+)/last-saved-image/$', views.LastSavedImageView.as_view(), name='last_saved_image'),
    url(r'^sites/(?P<site_id>\d+)/(?P<objects>.*)/$', views.SiteObjectsListView.as_view(), name='objects_list'),
    url(r'^rest-auth/', include('rest_auth.urls')),
    url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
