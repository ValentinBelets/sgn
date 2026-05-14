import json
import os
import re

def analyze_pdfs(file_path):
    with open(file_path, 'r') as f:
        signs = json.load(f)

    pdf_issues = []
    for sign in signs:
        pdf_url = sign.get('pdf_url')
        sign_no = sign.get('sign_no')
        
        if pdf_url and sign_no:
            filename = os.path.basename(pdf_url).split('?')[0]
            pdf_base = os.path.splitext(filename)[0].upper()
            
            # Remove common prefixes/suffixes in PDFs
            clean_pdf = pdf_base.replace('-DESIGN-PLAN', '').replace('_DESIGN_PLAN', '')
            
            # Normalize sign_no for comparison (simplistic version of what I did before)
            clean_no = re.split(r'\s|\(', sign_no)[0].upper().replace('(R)', '_R').replace('(L)', '_L')
            
            if clean_pdf != clean_no:
                pdf_issues.append({
                    "sign_no": sign_no,
                    "pdf_filename": filename,
                    "url": sign['url']
                })

    print(f"Total PDFs analyzed: {len([s for s in signs if s.get('pdf_url')])}")
    print(f"PDF naming mismatches: {len(pdf_issues)}")
    if pdf_issues:
        print("\nSample PDF Mismatches:")
        for issue in pdf_issues[:20]:
            print(f"  {issue['sign_no']} -> {issue['pdf_filename']}")

if __name__ == "__main__":
    analyze_pdfs('nsw_traffic_signs_unified.json')
