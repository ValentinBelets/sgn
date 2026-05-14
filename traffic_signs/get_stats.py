import json

with open('naming_inconsistencies_patch.json', 'r') as f:
    patch = json.load(f)

counts = {
    'sign_no': 0,
    'leg_ref': 0,
    'tech_ref': 0,
    'image': 0,
    'pdf': 0,
    'metadata': 0
}

for p in patch:
    issues = p.get('issues', [])
    if any('Casing' in i or 'Extra info' in i for i in issues):
        counts['sign_no'] += 1
    
    # Check if leg_ref actually changed
    if p.get('original_leg_ref') != p.get('normalized_leg_ref'):
        counts['leg_ref'] += 1
        
    # Check if tech_ref actually changed
    if p.get('original_tech_ref') != p.get('normalized_tech_ref'):
        counts['tech_ref'] += 1
        
    if any('Image filename mismatch' in i for i in issues):
        counts['image'] += 1
        
    if any('PDF filename mismatch' in i for i in issues):
        counts['pdf'] += 1
        
    if p.get('metadata'):
        counts['metadata'] += 1

print(json.dumps(counts, indent=2))
