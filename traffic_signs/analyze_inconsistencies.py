import json
import re
import os
from collections import Counter

def analyze_signs(file_path):
    with open(file_path, 'r') as f:
        signs = json.load(f)

    stats = {
        'total': len(signs),
        'case_patterns': Counter(),
        'sign_no_formats': Counter(),
        'mismatches': [],
        'image_extensions': Counter(),
        'thumb_vs_full': Counter(),
        'pdf_present': 0
    }

    for sign in signs:
        sign_no = sign.get('sign_no')
        image_url = sign.get('image_url')
        pdf_url = sign.get('pdf_url')

        if pdf_url:
            stats['pdf_present'] += 1

        if image_url:
            filename = os.path.basename(image_url).split('?')[0]
            ext = os.path.splitext(filename)[1].lower()
            stats['image_extensions'][ext] += 1
            if '_thumb' in filename:
                stats['thumb_vs_full']['thumb'] += 1
            else:
                stats['thumb_vs_full']['full'] += 1

        if sign_no:
            # Check case
            if sign_no.isupper():
                stats['case_patterns']['all_upper'] += 1
            elif sign_no.islower():
                stats['case_patterns']['all_lower'] += 1
            else:
                stats['case_patterns']['mixed'] += 1

            # Check for extra info
            clean_sign_no = re.split(r'\s|\(', sign_no)[0]
            if clean_sign_no != sign_no:
                stats['sign_no_formats']['has_extra_info'] += 1
            else:
                stats['sign_no_formats']['clean'] += 1

            # Match sign_no with image filename
            if image_url:
                img_name = os.path.splitext(filename)[0].replace('_thumb', '').lower()
                clean_no = clean_sign_no.lower()
                if img_name != clean_no:
                    stats['mismatches'].append({
                        'sign_no': sign_no,
                        'clean_no': clean_no,
                        'image_name': img_name,
                        'url': sign['url']
                    })

    print(f"Total signs: {stats['total']}")
    print(f"Case patterns: {stats['case_patterns']}")
    print(f"Sign No formats: {stats['sign_no_formats']}")
    print(f"Image extensions: {stats['image_extensions']}")
    print(f"Thumb vs Full: {stats['thumb_vs_full']}")
    print(f"PDFs present: {stats['pdf_present']}")
    print(f"Mismatches found: {len(stats['mismatches'])}")
    
    if stats['mismatches']:
        print("\nSample Mismatches:")
        for m in stats['mismatches'][:20]:
            print(f"  {m['sign_no']} vs {m['image_name']} ({m['url']})")

if __name__ == "__main__":
    analyze_signs('nsw_traffic_signs.json')
