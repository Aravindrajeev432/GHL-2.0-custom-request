
#  GHL PRIVATE API

How manage access token and refresh token 


##  Create Model


    location_id = models.CharField(max_length=300)
    access_token = models.TextField(max_length=500)
    refresh_token = models.TextField(max_length=500)
    expires_in = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    


## Why!
This approach avoids the edge case of token expiration just before the request.
after the first token validity check.
## How?
We're creating a custom function in utils.py. This function accepts method, location id , url and params

we're going to use this function for every request

this function checks token validity before request if token expired we're updating the token 
## Code 👨🏻‍💻
Checkout custom_requests()
in utils.py /auth_app 