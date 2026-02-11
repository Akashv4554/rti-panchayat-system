from django.urls import path
from . import views

urlpatterns = [
    path('', views.rti_list, name='rti_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create_rti, name='create_rti'),
    path('<int:pk>/', views.rti_detail, name='rti_detail'),
]
