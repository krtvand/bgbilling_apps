from django.conf.urls import url
from . import views

app_name = 'recalculation'
urlpatterns = [
   
    url('^recalculate/$', views.recalculate_view, name = "recalculate"),
 
]