import json
from datetime import timedelta
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
            return JsonResponse({'error': "Invalid Credentials"}, status=400)
        response_data = response.json()

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



def ghl_get_contacts(request):
    try:
        auth = AuthInfo.objects.latest()
    except AuthInfo.DoesNotExist:
        return JsonResponse({"data": [], "status_code": 200}, safe=False)
    ghl_contact_response = custom_requests("GET", "https://services.leadconnectorhq.com/contacts/", auth)
    return JsonResponse({"data": ghl_contact_response.json(), "status_code": 200}, safe=False)