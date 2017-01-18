from django.conf.urls import url

from . import views

app_name = 'bgb_webcontract'
urlpatterns = [
    url(r'^$', views.index_view, name='index'),
    url(r'^backend/$', views.backend_view, name='backend'),
    url(r'^request/$', views.request_view, name='request'),
    url(r'^request/(?P<request_id>[0-9]+)/$', views.request_detail_view, name='request_detail'),
    url(r'^backend/request/(?P<request_id>[0-9]+)/$', views.request_detail_backend_view, name='request_detail_backend'),
    url(r'^backend/statistics/$', views.statistics_view, name='statistics'),
]