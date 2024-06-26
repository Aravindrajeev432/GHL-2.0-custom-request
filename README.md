
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)


# Custom Request Function for GHL 2.0 api 

How manage access token and refresh token 
when using go highlevel's 2.0 api

##  Create Model


    location_id = models.CharField(max_length=300)
    access_token = models.TextField(max_length=500)
    refresh_token = models.TextField(max_length=500)
    expires_in = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    last_updated_at = models.DateTimeField()
    

## Why!
This approach avoids the edge case of token expiration just before the request.
Dont worry about ratelimit.
Works for every situations.

## How?
We're creating a custom function in utils.py. 
This function accepts method, location id, url and params

We're going to use this function for every request.

This function checks token validity before request if token expired we're updating the token.
And alse checks for ratelimit using go highlevel  response's headers.

## Things to Note!
If you are using the custom request function inside Django's request response cycle,
It would be good to remove the rate limit management part to avoid Gunicorn timeout.

## Code 👨🏻‍💻
Checkout custom_request()
in  auth_app/utils.py