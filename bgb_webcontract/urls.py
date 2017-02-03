from django.conf.urls import url

from . import views

app_name = 'bgb_webcontract'
urlpatterns = [
    url(r'^$', views.index_view, name='index'),
    url(r'^backend/$', views.backend_view, name='backend'),
    url(r'^request/create/$', views.RequestCreate.as_view(), name='request_create'),
    url(r'^request/(?P<pk>[0-9]+)/$', views.request_update_redirect, name='request_update_redirect'),
    url(r'^request/(?P<pk>[0-9]+)/update/$', views.RequestUpdate.as_view(), name='request_update'),
    url(r'^request/create/success$', views.request_create_success, name='request_create_success'),
    url(r'^backend/request/(?P<pk>[0-9]+)/$', views.backend_request_update_redirect, name='backend_request_update_redirect'),
    url(r'^backend/request/(?P<pk>[0-9]+)/update/$', views.BackendRequestUpdate.as_view(), name='backend_request_update'),
    #url(r'^backend/request/(?P<request_id>[0-9]+)/$', views.request_detail_backend_view, name='request_detail_backend'),
    url(r'^backend/statistics/$', views.statistics_view, name='statistics'),
]