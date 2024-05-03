

from django.urls import path
from auth_app import views
urlpatterns = [

    path('', views.on_boarding),
    path('capturecode/',views.capture_code),
    path('contacts', views.ghl_get_contacts),
    path('webhook', views.custom_field_updator_test)
]
