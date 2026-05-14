import json
from collections import Counter
import re

def analyze_references(file_path):
    with open(file_path, 'r') as f:
        signs = json.load(f)

    leg_refs = Counter()
    tech_refs = Counter()
    
    for sign in signs:
        leg = sign.get('legislative_reference')
        tech = sign.get('primary_technical_reference')
        
        if leg:
            leg_refs[leg] += 1
        if tech:
            tech_refs[tech] += 1

    print("--- Top Legislative References ---")
    for ref, count in leg_refs.most_common(20):
        print(f"{count:4} | {ref}")
        
    print("\n--- Top Technical References ---")
    for ref, count in tech_refs.most_common(20):
        print(f"{count:4} | {ref}")

    # Look for specific AS patterns to see variety
    as_patterns = Counter()
    for ref in tech_refs:
        matches = re.findall(r'AS\s?\d+(?:\.\d+)?', str(ref), re.I)
        for m in matches:
            as_patterns[m.upper().replace(" ", "")] += 1
            
    print("\n--- AS Standard Patterns Found ---")
    for pat, count in as_patterns.most_common(10):
        print(f"{count:4} | {pat}")

if __name__ == "__main__":
    analyze_references('nsw_traffic_signs_unified.json')
