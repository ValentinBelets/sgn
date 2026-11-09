import json
import re
import os
import html


SIGN_CODE_RE = re.compile(r'^[A-Z]{1,3}\d+(?:-\d+)*(?:[A-Z])?$', re.I)

class Severity:
    CRITICAL = "Critical: Reference Mismatch"
    MAJOR = "Major: Variant/Modifier Error"
    MINOR = "Minor: Format Inconsistency"
    AMBIGUOUS = "Ambiguous Reference"
    GAP = "Reference Gap"

def _create_issue(severity, reasoning, details=None):
    return {
        "severity": severity,
        "reasoning": reasoning,
        "details": details
    }

def _sanitize_text(value: str) -> str:
    # Decode entities, normalize NBSP chars, and collapse repeated whitespace.
    text = html.unescape(str(value)).replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def _sanitize_deep(value):
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, list):
        return [_sanitize_deep(v) for v in value]
    if isinstance(value, dict):
        return {k: _sanitize_deep(v) for k, v in value.items()}
    return value

def normalize_sign_no(sign_no):
    if not sign_no:
        return None, [], {}
    
    issues = []
    metadata = {}
    
    # Preserve original for issue messages
    original_sign_no = sign_no

    # Decode HTML entities and normalize whitespace early.
    sign_no = _sanitize_text(sign_no)
    sign_no = sign_no.rstrip('-').strip()

    # Detect canonical code prefix and only normalize aggressively when one exists.
    code_match = re.match(r'^([A-Z]{1,3}\d+(?:-\d+)*(?:[A-Z])?)', sign_no, re.I)
    if not code_match:
        if sign_no != original_sign_no:
            issues.append(_create_issue(Severity.MINOR, f"Whitespace/entity cleanup: '{original_sign_no}' -> '{sign_no}'"))
        return sign_no, issues, metadata

    base_code = code_match.group(1)
    tail = sign_no[len(base_code):].strip()

    # Extract groups after base code. Short alnum groups become bracket modifiers.
    paren_groups = re.findall(r'\(([^)]+)\)', tail)
    tail_no_paren = re.sub(r'\s*\([^)]*\)', '', tail).strip()

    orientation_mods = []
    bracket_mods = []
    other_notes = []

    for g in paren_groups:
        g_clean = _sanitize_text(g)
        token = g_clean.upper().replace('/', '')
        if token in {'L', 'R', 'LR'}:
            orientation_mods.append(token)
        elif re.fullmatch(r'[A-Z0-9]{1,3}', token):
            bracket_mods.append(token)
        else:
            other_notes.append(g_clean)

    if tail_no_paren:
        other_notes.append(tail_no_paren)

    # De-duplicate while preserving order.
    dedup_orient = []
    seen_orient = set()
    for token in orientation_mods:
        if token == 'LR' or ('L' in seen_orient and 'R' in seen_orient):
            dedup_orient = ['LR']
            seen_orient = {'LR'}
            break
        if token not in seen_orient:
            seen_orient.add(token)
            dedup_orient.append(token)

    if 'L' in seen_orient and 'R' in seen_orient:
        dedup_orient = ['LR']

    dedup_mods = []
    seen = set()
    for token in bracket_mods:
        if token not in seen:
            seen.add(token)
            dedup_mods.append(token)

    if other_notes:
        metadata['notes'] = ', '.join(other_notes)

    normalized_base = base_code.upper()
    is_nsw_variant = False
    if normalized_base.endswith('N'):
        normalized_base = normalized_base[:-1] + 'n'
        is_nsw_variant = True

    orientation_suffix = ''.join(f'({token})' for token in dedup_orient)
    bracket_suffix = ''.join(f'[{token}]' for token in dedup_mods)
    suffix = orientation_suffix + bracket_suffix
    expected_case = normalized_base + suffix

    if sign_no != expected_case:
        severity = Severity.MINOR
        # If it's a major variant change (like adding 'n' or orientation)
        if (is_nsw_variant and 'n' not in sign_no.lower()) or (dedup_orient and not any(o in sign_no.upper() for o in dedup_orient)):
            severity = Severity.MAJOR
            
        issues.append(_create_issue(severity, f"Sign code normalized: '{original_sign_no}' -> '{expected_case}'"))

    return expected_case, issues, metadata

def normalize_reference(ref_text):
    if not ref_text:
        return 'NA', []
    
    issues = []
    original = ref_text
    
    # 1. Decode HTML entities and normalise whitespace
    clean = html.unescape(str(ref_text))
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    # 2. Standardize Nulls
    if clean.upper() in ['NA', 'N/A', '-', '', 'NULL', 'NONE']:
        if clean != 'NA':
            issues.append(_create_issue(Severity.MINOR, f"Null standardized: '{original}' -> 'NA'"))
        return 'NA', issues

    # 3. Handle "Not Used in NSW" early
    if 'not used in nsw' in clean.lower():
        norm = 'Not Used in NSW'
        if clean != norm: issues.append(_create_issue(Severity.MINOR, f"Standardized Not Used: '{original}'"))
        return norm, issues
        
    # 4. Handle "Superseded" early
    if 'superseded' in clean.lower() or 'superceded' in clean.lower():
        # Keep the "Use XXX" if present
        use_match = re.search(r'use\s+([A-Z0-9-]{2,})', clean, re.I)
        if use_match:
            norm = f"Superseded (Use {use_match.group(1).upper()})"
        else:
            norm = "Superseded"
        if clean != norm: issues.append(_create_issue(Severity.MINOR, f"Standardized Superseded: '{original}'"))
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
        if clean != norm: issues.append(_create_issue(Severity.MINOR, f"Normalized AS1742 reference: '{original}' -> '{norm}'"))
        return norm, issues

    # 6. Technical Directions (TD/TDT)
    td_match = re.search(r'(TD|TDT)\s?(\d{4})[/-](\d+)', clean, re.I)
    if td_match:
        norm = f"{td_match.group(1).upper()} {td_match.group(2)}/{td_match.group(3)}"
        if clean != norm: issues.append(_create_issue(Severity.MINOR, f"Normalized Tech Direction: '{original}' -> '{norm}'"))
        return norm, issues

    # 7. NSW Road Rules
    rr_match = re.search(r'NSW\s+Road\s+Rules?\s+(-?\s?Rules?\s+)?(\d+[A-Z]?)', clean, re.I)
    if rr_match:
        norm = f"NSW Road Rule {rr_match.group(2)}"
        if clean != norm: issues.append(_create_issue(Severity.MINOR, f"Normalized Road Rule: '{original}' -> '{norm}'"))
        return norm, issues

    # 8. Project Specific
    if 'project specific' in clean.lower():
        norm = "Project Specific"
        if clean != norm: issues.append(_create_issue(Severity.MINOR, f"Normalized Project Specific: '{original}'"))
        return norm, issues

    # 9. Austroads
    if 'austroads' in clean.lower():
        if 'Design' in clean or 'Part' in clean:
            norm = clean
        else:
            norm = "Austroads Guide"
        return norm, issues

    return clean, issues

def generate_patch(input_file, patch_file, unified_file):
    with open(input_file, 'r') as f:
        signs = json.load(f)

    patch = []
    unified_signs = []
    
    # Track sign_no usage for Ambiguous Reference detection
    no_to_signs = {}

    for sign in signs:
        orig_no = sign.get('sign_no')
        norm_no, sign_issues, meta = normalize_sign_no(orig_no)
        
        leg_ref = sign.get('legislative_reference')
        norm_leg, leg_issues = normalize_reference(leg_ref)
        
        tech_ref = sign.get('primary_technical_reference')
        norm_tech, tech_issues = normalize_reference(tech_ref)
        
        all_issues = sign_issues + leg_issues + tech_issues
        
        # Check Reference Gap
        pdf_url = sign.get('pdf_url')
        if pdf_url and norm_tech == 'NA':
            all_issues.append(_create_issue(Severity.GAP, "Technical reference is 'NA' despite Design Plan PDF being available. Reference likely exists within PDF drawing."))

        # Check image mismatch
        image_url = sign.get('image_url')
        if image_url:
            filename = os.path.basename(image_url).split('?')[0]
            img_base = os.path.splitext(filename)[0].replace('_thumb', '')
            
            check_norm = norm_no if norm_no else ""
            # Strip formatting for comparison
            clean_norm = check_norm.lower().replace('(', '').replace(')', '').replace('_', '-').replace('[', '').replace(']', '')
            clean_img = img_base.lower().replace('_', '-')
            
            if clean_img != clean_norm:
                # Special case for NSW 'n' suffix missing in image
                if clean_img == clean_norm.replace('n', ''):
                    all_issues.append(_create_issue(Severity.MAJOR, f"NSW Variant Suffix 'n' missing from image filename: '{filename}' vs normalized '{check_norm}'"))
                else:
                    all_issues.append(_create_issue(Severity.CRITICAL, f"Image filename mismatch: '{filename}' vs normalized '{check_norm}'"))

        # Check PDF mismatch
        if pdf_url:
            filename = os.path.basename(pdf_url).split('?')[0]
            pdf_base = os.path.splitext(filename)[0].lower().replace('-design-plan', '').replace('_design_plan', '')
            
            check_norm = (norm_no or "").lower().replace('(', '').replace(')', '').replace('[', '').replace(']', '')
            if not pdf_base.startswith(check_norm.replace('n', '')):
                all_issues.append(_create_issue(Severity.CRITICAL, f"PDF filename mismatch: '{filename}' vs normalized '{norm_no}'"))

        entry = {
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
            "pdf_url": pdf_url,
            "title": sign.get('title')
        }
        
        if all_issues or meta:
            patch.append(entry)
        
        if norm_no:
            if norm_no not in no_to_signs:
                no_to_signs[norm_no] = []
            no_to_signs[norm_no].append(entry)

        new_sign = sign.copy()
        if norm_no: new_sign['sign_no'] = norm_no
        if norm_leg: new_sign['legislative_reference'] = norm_leg
        if norm_tech: new_sign['primary_technical_reference'] = norm_tech
        if meta:
            new_sign['normalization_metadata'] = _sanitize_deep(meta)
        
        # Add normalization issues to the unified sign for the viewer to use
        if all_issues:
            new_sign['normalization_issues'] = _sanitize_deep(all_issues)

        new_sign = _sanitize_deep(new_sign)
        unified_signs.append(new_sign)

    # Second pass for Ambiguous References
    for norm_no, entries in no_to_signs.items():
        if len(entries) > 1:
            # Check if they point to different resources or have different titles
            unique_titles = {e.get('title') for e in entries}
            unique_images = {e.get('image_url') for e in entries}
            if len(unique_titles) > 1 or len(unique_images) > 1:
                reasoning = f"Code '{norm_no}' is used for multiple distinct sign entries."
                issue = _create_issue(Severity.AMBIGUOUS, reasoning, details=[e['original_url'] for e in entries])
                for e in entries:
                    if e in patch:
                        e['issues'].append(issue)
                    else:
                        e['issues'] = [issue]
                        patch.append(e)
                    # Also update unified signs
                    for s in unified_signs:
                        if s['url'] == e['original_url']:
                            if 'normalization_issues' not in s: s['normalization_issues'] = []
                            s['normalization_issues'].append(_sanitize_deep(issue))

    with open(patch_file, 'w') as f:
        json.dump(patch, f, indent=2)
    
    with open(unified_file, 'w') as f:
        json.dump(unified_signs, f, indent=2)
    
    print(f"Generated patch with {len(patch)} entries with issues/metadata at {patch_file}")
    print(f"Generated unified signs data at {unified_file}")

if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Generate normalization patch and unified signs JSON')
    parser.add_argument('--input', '-i', default='nsw_traffic_signs.json', help='Input raw signs JSON (relative to script dir)')
    parser.add_argument('--patch-out', '-p', default='naming_inconsistencies_patch.json', help='Output patch JSON (relative to script dir)')
    parser.add_argument('--unified-out', '-u', default='nsw_traffic_signs_unified.json', help='Output unified JSON (relative to script dir)')
    parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing unified output if present')
    args = parser.parse_args()

    # Resolve paths relative to this script's directory (traffic_signs/)
    base_dir = Path(__file__).resolve().parent
    def _resolve(p: str) -> str:
        return str(Path(p).resolve()) if os.path.isabs(p) else str((base_dir / p))

    input_path = _resolve(args.input)
    patch_out = _resolve(args.patch_out)
    unified_path = _resolve(args.unified_out)

    # If target unified file exists and user didn't pass --force, write to a new file instead
    if os.path.exists(unified_path) and not args.force:
        alt = unified_path + '.new.json'
        print(f"Note: '{unified_path}' already exists. Writing unified output to '{alt}' instead. Use --force to overwrite the existing file.")
        generate_patch(input_path, patch_out, alt)
        print("To update the HTML viewer from the new unified file, run:")
        print(f"  python3 traffic_signs/build_viewer.py {alt} interactive_catalogue_unified.html")
    else:
        generate_patch(input_path, patch_out, unified_path)
        print("To regenerate the HTML viewer from the unified JSON, run:")
        print(f"  python3 traffic_signs/build_viewer.py {unified_path} interactive_catalogue_unified.html")
