import time
import requests
from datetime import timedelta
from typing import Dict, Optional
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from auth_app.exceptions import LocationNotFound
from .models import AuthInfo


def custom_request(
    method: str,
    url: str,
    location_id: str,
    params: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, str]] = None,
) -> requests.Response:
    """Sends a request to GHL API.

    :param method: HTTP method (e.g. 'GET', 'POST', 'PUT', 'PATCH', 'DELETE')
    :param url: URL of the GHL API endpoint
    :param location_id: Location ID
    :param params: Query parameters
    :param data: Request body
    :return: Response from the API
    """
    with transaction.atomic():
        try:
            auth = AuthInfo.objects.get(location_id=location_id)
        except AuthInfo.DoesNotExist:
            raise LocationNotFound  
        current_datetime = timezone.now()
        exp_datetime = auth.last_updated_at + timedelta(seconds=auth.expires_in)
        if exp_datetime < current_datetime:
            # expired
            auth_url: str = "https://services.leadconnectorhq.com/oauth/token"
            payload: Dict[str, str] = {
                "client_id": settings.CLIENT_ID,
                "client_secret": settings.CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": auth.refresh_token,
            }
            headers: Dict[str, str] = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
            response: requests.Response = requests.post(
                auth_url, data=payload, headers=headers
            )

            auth.access_token = response.json()["access_token"]
            auth.refresh_token = response.json()["refresh_token"]
            auth.expires_in = response.json()["expires_in"]
            auth.last_updated_at = timezone.now()
            auth.save()

        headers: Dict[str, str] = {
            "Authorization": f"Bearer {auth.access_token}",
            "Version": "2021-07-28",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        while True:
            response: requests.Response = requests.request(
                method, url, headers=headers, params=params, json=data
            )
            rate_limit_remaining: Optional[str] = response.headers.get(
                "x-ratelimit-remaining", "0"
            )
            rate_limit_interval: Optional[str] = response.headers.get(
                "x-ratelimit-interval-milliseconds", "10000"
            )
            try:
                if rate_limit_remaining and int(rate_limit_remaining) <= 3:
                    time.sleep(int(rate_limit_interval) / 1000)
                else:
                    break
            except Exception as e:

                raise (e)

        return response
