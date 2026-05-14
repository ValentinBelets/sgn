import json
import re
import os
import csv

def normalize_text(text):
    if not text or text.upper() in ['NA', '-', 'N/A', '']: return 'NA'
    clean = re.sub(r'\s+', ' ', text.strip())
    # Add project-specific regex here
    return clean

def process_dataset(input_json, output_json, patch_json):
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    patch = []
    unified = []
    
    for item in data:
        # Example logic
        original = item.get('id', '')
        normalized = normalize_text(original)
        
        if original != normalized:
            patch.append({"original": original, "normalized": normalized, "url": item.get('url')})
        
        new_item = item.copy()
        new_item['id'] = normalized
        unified.append(new_item)
        
    with open(output_json, 'w', encoding='utf-8') as f: json.dump(unified, f, indent=2)
    with open(patch_json, 'w', encoding='utf-8') as f: json.dump(patch, f, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        process_dataset(sys.argv[1], 'unified.json', 'patch.json')
