from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.loginUser, name='login'),
    path('logout', views.logoutUser, name='logout'),
    path('dashboard', views.index, name='index'),
    path('copyTemp', views.copyTemp, name='copyTemp'),
    path('fetch_Temp', views.fetch_Temp, name='fetch_Temp'),
    path('get_tempJson', views.get_tempJson, name='get_tempJson'),
    path('create_Temp', views.create_Temp, name='create_Temp'),
    path('AdminTemp', views.manageTemp, name='manageTemp'),
    path('settings', views.settings, name='settings'),
    path('addSettings', views.addSettings, name='addSettings'),
    path('editSettings', views.editSettings, name='editSettings'),
    path('delete_Settings', views.delete_setting, name='delete_setting'),
    path('checkTemp', views.get_CheckJSOn, name='get_CheckJSOn'),
]