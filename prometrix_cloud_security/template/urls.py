from django.conf.urls import url

import views

urlpatterns = [
    url(r'^login/$', views.LoginView.as_view(), name='login'),
]
