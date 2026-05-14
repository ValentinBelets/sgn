import json
import re
import os

def normalize_sign_no(sign_no):
    if not sign_no:
        return None, [], {}
    
    issues = []
    metadata = {}
    
    # Extract metadata from notes like (Superseded Use W3-3-1)
    note_match = re.search(r'\s*\(([^)]+)\)', sign_no)
    if note_match:
        note = note_match.group(1)
        if 'Superseded' in note or 'Use' in note:
            metadata['note'] = note
            # Try to extract the reference sign
            ref_match = re.search(r'[A-Z]+\d+[-\d]*[a-z]?', note)
            if ref_match:
                metadata['replacement_ref'] = ref_match.group(0)
    
    # Clean sign_no: strip extra notes but keep legitimate parts
    parts = re.split(r'\s+', sign_no)
    clean = parts[0]
    
    # Keep (L)/(R) if they exist but were stripped by split
    direction_match = re.search(r'\(([LR])\)', sign_no)
    if direction_match:
        dir_suffix = direction_match.group(0)
        if dir_suffix not in clean:
            clean += dir_suffix
    
    if clean != sign_no:
        issues.append(f"Extra info stripped from sign_no: '{sign_no}' -> '{clean}'")
    
    # Casing logic: Uppercase everything EXCEPT the 'n' suffix
    # The 'n' suffix is always at the end of the code part, before any bracketed direction
    
    base_part = clean
    direction_suffix = ""
    if '(' in clean:
        base_part = clean.split('(')[0]
        direction_suffix = '(' + clean.split('(')[1]
        
    normalized_base = base_part.upper()
    if normalized_base.endswith('N'):
        # Check if original had 'n'
        if base_part.endswith('n'):
            normalized_base = normalized_base[:-1] + 'n'
        else:
            # If it was capital N, user said 'n' is correct for NSW signage
            # We'll assume if it's there, it should be lowercase
            normalized_base = normalized_base[:-1] + 'n'
            
    expected_case = normalized_base + direction_suffix.upper()
        
    if clean != expected_case:
        issues.append(f"Casing issue: '{clean}' -> '{expected_case}'")
    
    return expected_case, issues, metadata

def normalize_reference(ref_text):
    if not ref_text:
        return 'NA', []
    
    issues = []
    original = ref_text
    
    # 1. Clean HTML and whitespace
    clean = ref_text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"').strip()
    clean = re.sub(r'\s+', ' ', clean)
    
    # 2. Standardize Nulls
    if clean.upper() in ['NA', 'N/A', '-', '', 'NULL', 'NONE']:
        if clean != 'NA':
            issues.append(f"Null standardized: '{original}' -> 'NA'")
        return 'NA', issues

    # 3. Handle "Not Used in NSW" early
    if 'not used in nsw' in clean.lower():
        norm = 'Not Used in NSW'
        if clean != norm: issues.append(f"Standardized Not Used: '{original}'")
        return norm, issues
        
    # 4. Handle "Superseded" early
    if 'superseded' in clean.lower() or 'superceded' in clean.lower():
        # Keep the "Use XXX" if present
        use_match = re.search(r'use\s+([A-Z0-9-]{2,})', clean, re.I)
        if use_match:
            norm = f"Superseded (Use {use_match.group(1).upper()})"
        else:
            norm = "Superseded"
        if clean != norm: issues.append(f"Standardized Superseded: '{original}'")
        return norm, issues

    # 5. AS1742 Mapping
    as_1742_match = re.search(r'AS\s?1742\.(\d+)', clean, re.I)
    if as_1742_match:
        part = as_1742_match.group(1)
        descriptions = {
            "1": "General Index",
            "2": "Traffic Control Devices",
            "3": "Traffic Control for Works on Roads",
            "4": "Speed Controls",
            "6": "Tourist and Service Signs",
            "7": "Railway Crossings",
            "9": "Bicycle Facilities",
            "10": "Pedestrian Control and Protection",
            "11": "Parking Controls",
            "12": "Bus, Transit, Tram and Truck Lanes",
            "13": "Local Area Traffic Management",
            "14": "Traffic Signals",
            "15": "Direction Signs"
        }
        desc = descriptions.get(part, "")
        norm = f"AS1742.{part}" + (f" ({desc})" if desc else "")
        if clean != norm: issues.append(f"Normalized AS1742 reference: '{original}' -> '{norm}'")
        return norm, issues

    # 6. Technical Directions (TD/TDT)
    td_match = re.search(r'(TD|TDT)\s?(\d{4})[/-](\d+)', clean, re.I)
    if td_match:
        norm = f"{td_match.group(1).upper()} {td_match.group(2)}/{td_match.group(3)}"
        if clean != norm: issues.append(f"Normalized Tech Direction: '{original}' -> '{norm}'")
        return norm, issues

    # 7. NSW Road Rules
    rr_match = re.search(r'NSW\s+Road\s+Rules?\s+(-?\s?Rules?\s+)?(\d+[A-Z]?)', clean, re.I)
    if rr_match:
        norm = f"NSW Road Rule {rr_match.group(2)}"
        if clean != norm: issues.append(f"Normalized Road Rule: '{original}' -> '{norm}'")
        return norm, issues

    # 8. Project Specific
    if 'project specific' in clean.lower():
        norm = "Project Specific"
        if clean != norm: issues.append(f"Normalized Project Specific: '{original}'")
        return norm, issues

    # 9. Austroads
    if 'austroads' in clean.lower():
        # Just unify to "Austroads Guide" if too messy?
        if 'Design' in clean or 'Part' in clean:
            norm = clean # Keep for now but unify casing if needed
        else:
            norm = "Austroads Guide"
        return norm, issues

    return clean, issues

def generate_patch(input_file, patch_file, unified_file):
    with open(input_file, 'r') as f:
        signs = json.load(f)

    patch = []
    unified_signs = []
    for sign in signs:
        orig_no = sign.get('sign_no')
        norm_no, sign_issues, meta = normalize_sign_no(orig_no)
        
        leg_ref = sign.get('legislative_reference')
        norm_leg, leg_issues = normalize_reference(leg_ref)
        
        tech_ref = sign.get('primary_technical_reference')
        norm_tech, tech_issues = normalize_reference(tech_ref)
        
        all_issues = sign_issues + leg_issues + tech_issues
        
        # Check image mismatch
        image_url = sign.get('image_url')
        if image_url:
            filename = os.path.basename(image_url).split('?')[0]
            img_base = os.path.splitext(filename)[0].replace('_thumb', '')
            
            check_norm = norm_no if norm_no else ""
            if img_base.lower() != check_norm.lower().replace('(', '').replace(')', '').replace('_', '-'):
                alt_img_base = check_norm.lower().replace('(', '_').replace(')', '').replace('-', '-')
                if img_base.lower() != alt_img_base and img_base.lower() != check_norm.lower().replace('n', ''):
                    all_issues.append(f"Image filename mismatch: '{filename}' vs normalized '{check_norm}'")

        # Check PDF mismatch
        pdf_url = sign.get('pdf_url')
        if pdf_url:
            filename = os.path.basename(pdf_url).split('?')[0]
            pdf_base = os.path.splitext(filename)[0].lower().replace('-design-plan', '').replace('_design_plan', '')
            
            check_norm = (norm_no or "").lower().replace('(', '').replace(')', '')
            if not pdf_base.startswith(check_norm.replace('n', '')):
                all_issues.append(f"PDF filename mismatch: '{filename}' vs normalized '{norm_no}'")

        if all_issues or meta:
            patch.append({
                "original_url": sign['url'],
                "original_sign_no": orig_no,
                "normalized_sign_no": norm_no,
                "original_leg_ref": leg_ref,
                "normalized_leg_ref": norm_leg,
                "original_tech_ref": tech_ref,
                "normalized_tech_ref": norm_tech,
                "metadata": meta,
                "issues": all_issues,
                "image_url": image_url,
                "pdf_url": pdf_url
            })
        
        new_sign = sign.copy()
        if norm_no: new_sign['sign_no'] = norm_no
        if norm_leg: new_sign['legislative_reference'] = norm_leg
        if norm_tech: new_sign['primary_technical_reference'] = norm_tech
        if meta: new_sign['normalization_metadata'] = meta
        unified_signs.append(new_sign)

    with open(patch_file, 'w') as f:
        json.dump(patch, f, indent=2)
    
    with open(unified_file, 'w') as f:
        json.dump(unified_signs, f, indent=2)
    
    print(f"Generated patch with {len(patch)} entries with issues/metadata at {patch_file}")
    print(f"Generated unified signs data at {unified_file}")

if __name__ == "__main__":
    generate_patch('nsw_traffic_signs.json', 'naming_inconsistencies_patch.json', 'nsw_traffic_signs_unified.json')
