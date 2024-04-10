import time
import requests
from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from .models import AuthInfo



def custom_request(
    method: str,
    url: str,
    location_id: str,
    params: dict[str, str] = None,
    data: dict[str, str] = None,
) -> requests.Response:
    """Sends a request to GHL API.
    :param method: HTTP method (e.g. 'GET', 'POST', 'PUT', 'PATCH', 'DELETE')
    :param url: URL of the GHL API endpoint
    :param location_id: Location ID
    :param params: Query parameters
    :param data: Request body
    """

    auth = AuthInfo.objects.get(location_id=location_id)
    current_datetime = timezone.now()
    exp_datetime = auth.last_updated_at + timedelta(seconds=auth.expires_in)
    if exp_datetime < current_datetime:
        # expired
        auth_url = "https://services.leadconnectorhq.com/oauth/token"
        
        payload = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": auth.refresh_token,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        response = requests.post(auth_url, data=payload, headers=headers)

        auth.access_token = response.json()["access_token"]
        auth.refresh_token = response.json()["refresh_token"]
        auth.expires_in = response.json()["expires_in"]
        auth.last_updated_at = timezone.now()
        auth.save()
    headers = {
        "Authorization": f"Bearer {auth.access_token}",
        "Version": "2021-07-28",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    while True:
        response = requests.request(
            method, url, headers=headers, params=params, json=data
        )
        rate_limit_remaining = response.headers.get("x-ratelimit-remaining")
        rate_limit_interval = response.headers.get("x-ratelimit-interval-milliseconds")
        try:
            if int(rate_limit_remaining) <= 3:
                time.sleep(rate_limit_interval / 1000)
            else:
                break
        except Exception as e:

            raise (e)

    return response
