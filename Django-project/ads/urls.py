from django.urls import path
from .views import new_vehicle_ad

app_name = 'ads'
urlpatterns = [
    path('ads/new', new_vehicle_ad, name='new_vehicle_ad'),
    # path('vehicle/ads/<int:ad_id>', get_vehicle_ad, name='get_vehicle_ad'),
]