import urllib.request

url = 'https://www.transport.nsw.gov.au/operations/roads-and-waterways/traffic-signs?page=0'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        status = response.getcode()
        data = response.read().decode('utf-8')
        print(f"Status: {status}")
        with open('first_page.html', 'w', encoding='utf-8') as f:
            f.write(data)
        print("First page saved to first_page.html")
except Exception as e:
    print(f"Error: {e}")
