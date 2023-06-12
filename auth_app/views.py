import json
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests

from .models import AuthInfo
from .utils import custom_requests


# Create your views here.
def on_boarding(request):
    if request.method == "GET":
        redirect_uri = 'http://127.0.0.1:8000/capturecode/'
        client_id = settings.CLIENT_ID
        scopes = 'contacts.readonly contacts.write locations.write locations.readonly locations/customFields.readonly locations/customFields.write locations/tags.write locations/tags.readonly businesses.readonly calendars.readonly calendars.write calendars/events.readonly calendars/events.write workflows.readonly users.readonly opportunities.readonly opportunities.write locations/tasks.readonly'

        base_url = 'https://marketplace.gohighlevel.com/oauth/chooselocation'
        params = {
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'scope': scopes
        }

        url = f"{base_url}?{urlencode(params, quote_via=quote)}"

        context = {
            "access_url": url,
        }
        return render(request, 'on-boarding.html', context=context)
    elif request.method == "POST":

        location_id = request.POST.get('location_id_id')
        access_code = request.POST.get('access_code_id')
        public_api_key = request.POST.get('public_api_key_id')
        print(location_id)
        print(public_api_key)
        print(access_code)

        url = "https://services.leadconnectorhq.com/oauth/token"

        payload = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": access_code,

        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        response = requests.post(url, data=payload, headers=headers)
        if response.status_code != 200:
            print("return 400")
            return JsonResponse({'error': "Invalid Credentials"}, status=400)
        response_data = response.json()
        print(response.json())
        print(response.status_code)
        print(response.text)

        location_id = location_id
        access_token = response_data['access_token']
        refresh_token = response_data['refresh_token']
        expires_in = response_data['expires_in']
        auth_info = AuthInfo.objects.create(location_id=location_id, refresh_token=refresh_token,
                                            access_token=access_token,
                                            expires_in=expires_in,
                                            created_at=timezone.now())

        return JsonResponse({'success': True, 'status_code': 200}, safe=False)


def capture_code(request):
    code = request.GET['code']
    url = f"/?code={code}"
    return redirect(url)


class ExpiredTokenException(Exception):
    pass


@csrf_exempt
def custom_field_updator(request):
    if request.method == 'POST':
        pass

        data = json.loads(request.body)
        print(data)
        location_id = data['location_id']
        # get access code
        try:
            location = AuthInfo.objects.get(location_id=location_id)
        except AuthInfo.DoesNotExist:
            return JsonResponse({"status_code": 400})
        try:
            current_datetime = timezone.now()
            exp_datetime = location.created_at + timedelta(seconds=location.expires_in)
            if exp_datetime < current_datetime:
                print(" expired")

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

            # getting contacts
            contact_url = "https://services.leadconnectorhq.com/contacts/"
            contact_headers = {
                "Authorization": f"Bearer {access_token}",
                "Version": "2021-07-28",
                "Accept": "application/json"
            }
            contacts = []
            count = 0
            while True:
                querystring = {"locationId": location_id, "limit": 100, } if count < 1 else {}

                try:
                    contact_response = requests.get(contact_url, headers=contact_headers, params=querystring)

                    contact_data = contact_response.json()
                    if contact_data['meta']['nextPageUrl'] is None:
                        break
                    contacts += contact_data['contacts']
                    contact_url = contact_data['meta']['nextPageUrl']
                except:
                    pass
                count += 1

            print(len(contacts))

            # Get the Custom Fields
            custom_field_url = f"https://services.leadconnectorhq.com/locations/{location_id}/customFields"
            custom_field_response = requests.get(custom_field_url, headers=contact_headers)
            print(custom_field_response.json())
            custom_fields = custom_field_response.json()['customFields']
            custom_field_id_names = {}  # id: name
            for custom_field in custom_fields:
                custom_field_id_names[custom_field.get('id', "")] = custom_field.get('name', "")

            count = 0
            result_dict = []

            for contact in contacts:
                custom_fields = contact.get('customFields', None)
                if custom_fields:

                    print(custom_fields)
                    print(count)
                    count += 1
                    if count == 10:
                        break
                    for custom_field in custom_fields:
                        test_data = {"id": custom_field['id'],
                                     "value": custom_field['value'],
                                     "name": custom_field_id_names[custom_field['id']]}
                        result_dict.append(test_data)
                        print(test_data)
                        print("--------------------------------")

                    print("________________________________")
        return JsonResponse(result_dict, safe=False)

        # get all locations

        # get custom field id
        # using the id get the name
        # perform  put using along with name


@csrf_exempt
def custom_field_updator_test(request):
    if request.method == 'POST':

        data = json.loads(request.body)
        print(data)
        location_id = data['location_id']
        # get access code

        # getting contacts
        contact_url = "https://services.leadconnectorhq.com/contacts/"
        contacts = []
        count = 0
        while True:
            print(count)
            querystring = {"locationId": location_id, "limit": 100, } if count < 1 else {}

            custom_requests_res = custom_requests(location_id=location_id, method="GET", url=contact_url,
                                                  params=querystring)

            print(custom_requests_res['status_code'])

            if custom_requests_res['status_code'] != 200:
                return JsonResponse(custom_requests_res, safe=False)
            contact_data = custom_requests_res['data']

            if contact_data['meta']['nextPageUrl'] is None:
                break
            contacts += contact_data['contacts']
            contact_url = contact_data['meta']['nextPageUrl']

            count += 1

        print(len(contacts))

        # Get the Custom Fields
        custom_field_url = f"https://services.leadconnectorhq.com/locations/{location_id}/customFields"

        custom_field_response = custom_requests(location_id=location_id, url=custom_field_url, method="GET")

        custom_fields = custom_field_response['data']['customFields']
        custom_field_id_names = {}  # id: name
        for custom_field in custom_fields:
            custom_field_id_names[custom_field.get('id', "")] = custom_field.get('name', "")

        count = 0
        result_dict = []

        for contact in contacts:
            custom_fields = contact.get('customFields', None)
            if custom_fields:

                print(custom_fields)
                print(count)
                count += 1
                if count == 10:
                    break
                for custom_field in custom_fields:
                    test_data = {"id": custom_field['id'],
                                 "value": custom_field['value'],
                                 "name": custom_field_id_names[custom_field['id']]}
                    result_dict.append(test_data)
                    print(test_data)
                    print("--------------------------------")

                print("________________________________")
        return JsonResponse(result_dict, safe=False)


def test(request):
    html = "<h1>hello</h1>"
    location_id = "jQyPKAp1Qi0mnFeTEWy5"
    auth_info = AuthInfo.objects.get(location_id=location_id)

    current_datetime = timezone.now()
    exp_datetime = auth_info.created_at + timedelta(seconds=86399)
    print(exp_datetime)
    print(current_datetime)
    if exp_datetime < current_datetime:
        print(" expired")

        pass
    else:
        print("not expired")
        # assuming expired

        url = "https://services.leadconnectorhq.com/oauth/token"

        payload = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": auth_info.refresh_token,

        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        response = requests.post(url, data=payload, headers=headers)
        response_data = response.json()
        auth_info.access_token = response_data['access_token']
        auth_info.refresh_token = response_data['refresh_token']
        auth_info.expires_in = response_data['expires_in']
        auth_info.created_at = timezone.now()
        auth_info.save(update_fields=['access_token', 'refresh_token', 'expires_in', 'created_at'])

    return HttpResponse(html)
