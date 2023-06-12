import requests
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from .models import AuthInfo


class ExpiredTokenException(Exception):
    pass


def custom_requests(location_id, method, url, data=None, params=None):

    try:
        location = AuthInfo.objects.get(location_id=location_id)
    except AuthInfo.DoesNotExist:
        return JsonResponse({"status_code": 400})
    try:
        current_datetime = timezone.now()
        exp_datetime = location.created_at + timedelta(seconds=location.expires_in)
        if exp_datetime < current_datetime:
            # expired

            raise ExpiredTokenException
        access_token = location.access_token

    except ExpiredTokenException:
        # update access code
        url = "https://services.leadconnectorhq.com/oauth/token"

        payload = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": location.refresh_token,

        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        response = requests.post(url, data=payload, headers=headers)
        response_data = response.json()
        location.access_token = response_data['access_token']
        location.refresh_token = response_data['refresh_token']
        location.expires_in = response_data['expires_in']
        location.created_at = timezone.now()
        location.save(update_fields=['access_token', 'refresh_token', 'expires_in', 'created_at'])

        access_token = response_data['access_token']

    finally:

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Version": "2021-07-28",
            "Accept": "application/json"
        }
        if method == "POST":
            response = requests.post(url, json=data, headers=headers, params=params)
            if response.status_code != 200:
                return {"status_code": response.status_code, "message": response.text}
            return {"data": response.json(), "status_code": 200, "message": response.text}
        elif method == "GET":
            print("GET request")
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(response.text)
                return {"status_code": response.status_code, "message": response.text}

            return {"data": response.json(), "status_code": 200, "message": "response.text"}
