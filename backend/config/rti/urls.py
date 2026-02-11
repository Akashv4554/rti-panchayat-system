from django.urls import path
from . import views
from .views import CustomLoginView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.rti_list, name='rti_list'),
    path('create/', views.create_rti, name='create_rti'),
     path('dashboard/', views.dashboard, name='dashboard'),
    path('<int:pk>/', views.rti_detail, name='rti_detail'),
    path('api/rti/', views.RTIListAPI.as_view(), name='api_rti'),
     path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
