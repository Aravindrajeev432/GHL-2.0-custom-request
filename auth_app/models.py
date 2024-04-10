from django.db import models


# Create your models here.
class AuthInfo(models.Model):
    location_id = models.CharField(max_length=300)
    access_token = models.TextField(max_length=500)
    refresh_token = models.TextField(max_length=500)
    expires_in = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    last_updated_at = models.DateTimeField()
