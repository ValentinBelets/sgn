import urllib.request
import re
import json
import time
from pathlib import Path

BASE_URL = "https://www.transport.nsw.gov.au"
SEARCH_URL = BASE_URL + "/operations/roads-and-waterways/traffic-signs?page={}"
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "nsw_traffic_signs.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def get_html(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_sign_urls(html):
    pattern = r'<h3 class="meta--compact reset--heading"><b><a href="([^"]+)"'
    return re.findall(pattern, html)

def extract_field(html, label):
    tables = re.findall(r'<table.*?>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    for table_html in tables:
        patterns = [
            rf'<strong>{re.escape(label)}</strong></td><td>(.*?)</td>',
            rf'<td><strong>{re.escape(label)}</strong></td><td>(.*?)</td>'
        ]
        for p in patterns:
            match = re.search(p, table_html, re.DOTALL | re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                val = re.sub(r'<[^>]+>', '', val).strip()
                return val
    return None

def extract_sizes(html):
    tables = re.findall(r'<table.*?>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    for table_html in tables:
        if 'height' in table_html.lower() or 'width' in table_html.lower():
            row_pattern = r'<tr>(.*?)</tr>'
            rows = re.findall(row_pattern, table_html, re.DOTALL | re.IGNORECASE)
            data = {}
            for row in rows:
                cells = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if not cells: continue
                label_text = re.sub(r'<[^>]+>', '', cells[0]).strip().lower()
                values = [re.sub(r'<[^>]+>', '', c).strip() for c in cells[1:]]
                if 'size' in label_text: data['size'] = values
                elif 'height' in label_text: data['height'] = values
                elif 'width' in label_text: data['width'] = values
            
            if not data.get('height') and not data.get('width'): continue
            
            sizes = []
            labels = data.get('size', [])
            heights = data.get('height', [])
            widths = data.get('width', [])
            count = max(len(labels), len(heights), len(widths))
            for i in range(count):
                sizes.append({
                    "label": labels[i] if i < len(labels) else "-",
                    "h": heights[i] if i < len(heights) else "-",
                    "w": widths[i] if i < len(widths) else "-"
                })
            return sizes
    return []

def extract_pdf(html):
    pattern = r'<a href="([^"]+\.pdf)">[^<]*design plan</a>'
    match = re.search(pattern, html, re.IGNORECASE)
    return match.group(1) if match else None

def extract_image(html):
    # Try og:image first as it's more reliable
    og_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    if og_match:
        return og_match.group(1)
    
    # Fallback to gallery item
    pattern = r'data-media-url="([^ ?"]+)'
    match = re.search(pattern, html)
    if match:
        url = match.group(1).split()[0]
        if url.startswith('/'): url = BASE_URL + url
        return url
    return None

def scrape_all():
    all_signs = []
    page = 0
    total_found = 0
    
    while True:
        print(f"Scraping search page {page}...")
        html = get_html(SEARCH_URL.format(page))
        if not html: break
        urls = extract_sign_urls(html)
        if not urls: break
        for url in urls:
            if not url.startswith('http'): url = BASE_URL + url
            print(f"  Scraping detail: {url}")
            detail_html = get_html(url)
            if not detail_html: continue
            sign_data = {
                "url": url,
                "title": extract_field(detail_html, "Descriptions") or extract_field(detail_html, "Description"),
                "sign_no": extract_field(detail_html, "Sign No:"),
                "standard_sign": extract_field(detail_html, "Standard sign?"),
                "use_by_council": extract_field(detail_html, "Use by council"),
                "legislative_reference": extract_field(detail_html, "Legislative Reference"),
                "primary_technical_reference": extract_field(detail_html, "Primary Technical Reference"),
                "sizes": extract_sizes(detail_html),
                "image_url": extract_image(detail_html),
                "pdf_url": extract_pdf(detail_html)
            }
            if sign_data["sizes"]:
                sign_data["height"] = sign_data["sizes"][0]["h"]
                sign_data["width"] = sign_data["sizes"][0]["w"]
            else:
                sign_data["height"] = "-"
                sign_data["width"] = "-"
            all_signs.append(sign_data)
            total_found += 1
            if total_found % 10 == 0:
                with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
                    json.dump(all_signs, f, indent=2)
            time.sleep(0.3)
        page += 1
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_signs, f, indent=2)
    print(f"Finished! Total: {total_found}")

if __name__ == "__main__":
    scrape_all()
