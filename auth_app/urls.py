

from django.urls import path
from auth_app import views
urlpatterns = [

    path('', views.on_boarding),
    path('capturecode/',views.capture_code),
    path('test', views.test),
    path('webhook', views.custom_field_updator_test)
]
