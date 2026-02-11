from django.urls import path
from . import views

urlpatterns = [
    path('', views.rti_list, name='rti_list'),
    path('create/', views.create_rti, name='create_rti'),
     path('dashboard/', views.dashboard, name='dashboard'),
    path('<int:pk>/', views.rti_detail, name='rti_detail'),
]
