import requests

url = 'https://dp4p6x0xfi5o9.cloudfront.net/ongeki/data.json'
req = requests.get(url)
with open('data.json', 'wb') as f:
    f.write(req.content)