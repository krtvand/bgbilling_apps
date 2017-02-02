from django.conf.urls import url

from . import views

app_name = 'bgb_webcontract'
urlpatterns = [
    url(r'^$', views.index_view, name='index'),
    url(r'^backend/$', views.backend_view, name='backend'),
    url(r'^request/create/$', views.RequestCreate.as_view(), name='request_create'),
    url(r'^request/(?P<pk>[0-9]+)/$', views.request_update_redirect, name='request_update_redirect'),
    url(r'^request/(?P<pk>[0-9]+)/update/$', views.RequestUpdate.as_view(), name='request_update'),
    url(r'^request/update/(?P<pk>[0-9]+)/$', views.RequestUpdate.as_view(), name='request_update2'),
    url(r'^request/create/success$', views.request_create_success, name='request_create_success'),
    url(r'^request/(?P<request_id>[0-9]+)/$', views.request_detail_view, name='request_detail'),
    url(r'^backend/request/(?P<request_id>[0-9]+)/$', views.request_detail_backend_view, name='request_detail_backend'),
    url(r'^backend/statistics/$', views.statistics_view, name='statistics'),
]