import urllib.request
import json

url = 'https://www.transport.nsw.gov.au/jsonapi/node/signage?page[limit]=1'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        status = response.getcode()
        data = response.read().decode('utf-8')
        print(f"Status: {status}")
        print(data[:1000])
except Exception as e:
    print(f"Error: {e}")
