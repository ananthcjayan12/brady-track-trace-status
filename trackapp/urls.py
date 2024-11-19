"""
URL configuration for bradyicc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home, name='home'),
    path('upload_csv/', views.upload_item_and_moq, name='upload_csv'),
    path('scan_fcg/', views.fcg_scan_qr, name='scan_fcg'),
    path('generate_qr/', views.generate_qr, name='generate_qr'),
    path('view_pdf/<str:filename>/', views.view_pdf, name='view_pdf'),
    path('export/', views.export_screen, name='export_screen'),
    path('ukimport/', views.ukimport, name='ukimport'),
    path('ukexport/', views.ukexport, name='ukexport'),
    path('admin_screen/', views.admin_screen, name='admin_screen'),
    path('get_mcodes/<str:item_code>/', views.get_mcodes_for_item, name='get_mcodes'),
    path('upload_moq/', views.upload_item_and_moq, name='upload_moq'),
    path('get_item_by_qr/', views.get_item_by_qr, name='get_item_by_qr'),
    path('login/', views.CustomLoginView.as_view(), name='agent_login'),
    path('logout/', views.agent_logout, name='agent_logout'),
    path('download_excel/', views.download_excel, name='download_excel')
    # path('admin-screen-temp/', views.admin_screen_temp, name='admin_screen_temp'),

    # in urls.py



]
