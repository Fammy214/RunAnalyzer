import requests

CLIENT_ID = '167815'
CLIENT_SECRET = '8b868cd57010e08192a8bbd44edb841a1f0c9b59'
CODE = '19711e68213b5044150423fbf844c85ba34aecca'

res = requests.post('https://www.strava.com/oauth/token', data={
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'code': CODE,
    'grant_type': 'authorization_code'
})

print(res.json())
