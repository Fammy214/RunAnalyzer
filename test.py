import requests

CLIENT_ID = ''
CLIENT_SECRET = ''
CODE = ''

res = requests.post('https://www.strava.com/oauth/token', data={
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'code': CODE,
    'grant_type': 'authorization_code'
})

print(res.json())
