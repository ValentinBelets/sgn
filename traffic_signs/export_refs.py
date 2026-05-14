import json
import csv

def export_refs():
    try:
        with open('nsw_traffic_signs_unified.json', 'r', encoding='utf-8') as f:
            signs = json.load(f)
    except FileNotFoundError:
        print("Source JSON not found.")
        return

    # Extract unique non-null references
    refs = set()
    for s in signs:
        ref = s.get('primary_technical_reference')
        if ref and ref != 'NA':
            refs.add(ref)
    
    sorted_refs = sorted(list(refs))

    with open('tech_references_mapping.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Original Reference', 'Proposed Normalized Reference'])
        for r in sorted_refs:
            writer.writerow([r, r])
    
    print(f"Exported {len(sorted_refs)} unique references to tech_references_mapping.csv")

if __name__ == "__main__":
    export_refs()
