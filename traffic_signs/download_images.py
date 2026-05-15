import json
import urllib.request
import time
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / 'images'
JSON_PATH = BASE_DIR / 'nsw_traffic_signs.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Referer': 'https://www.transport.nsw.gov.au/operations/roads-and-waterways/traffic-signs',
}

def download_image(sign):
    url = sign.get('image_url')
    if not url:
        return False
    
    filename = url.split('/')[-1].split('?')[0]
    if not filename:
        return False
        
    save_path = IMAGES_DIR / filename
    
    if save_path.exists() and save_path.stat().st_size > 0:
        return True
        
    try:
        # Random sleep to be more human-like
        time.sleep(random.uniform(0.1, 0.5))
        
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(save_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        # print(f"Error downloading {url}: {e}")
        return False

def main():
    if not JSON_PATH.exists():
        print("JSON file not found.")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Starting enriched download of {len(data)} images...")
    
    # Using fewer workers and sequential download to avoid 403
    success_count = 0
    for i, sign in enumerate(data):
        if download_image(sign):
            success_count += 1
        
        if (i + 1) % 50 == 0:
            print(f"Downloaded {success_count}/{i+1}...")
            # Periodic save/check is not needed for images, but good for progress
            
    print(f"Finished! Successfully downloaded {success_count} images.")

if __name__ == "__main__":
    main()
