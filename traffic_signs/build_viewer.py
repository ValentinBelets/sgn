import json
import os
import re
from pathlib import Path

def build_viewer(json_path: str = 'nsw_traffic_signs_unified.json', output_path: str = 'interactive_catalogue_unified.html') -> None:
    base_dir = Path(__file__).resolve().parent
    json_file = Path(json_path)
    output_file = Path(output_path)

    if not json_file.is_absolute():
        json_file = base_dir / json_file
    if not output_file.is_absolute():
        output_file = base_dir / output_file

    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Pre-process data
    sign_map = {}
    for sign in data:
        if sign.get('sign_no'):
            key = sign['sign_no'].strip().upper()
            sign_map[key] = sign

    for sign in data:
        if sign.get('primary_technical_reference'):
            sign['primary_technical_reference'] = str(sign['primary_technical_reference']).replace('&amp;', '&').replace('&nbsp;', ' ').strip()
        if sign.get('legislative_reference'):
            sign['legislative_reference'] = str(sign['legislative_reference']).replace('&amp;', '&').replace('&nbsp;', ' ').strip()
        
        if sign.get('image_url'):
            filename = sign['image_url'].split('/')[-1].split('?')[0]
            sign['local_image'] = f'images/{filename}'
        else:
            sign['local_image'] = ''
        
        title_text = sign.get('title') or ""
        pattern = r'([A-Z]{1,2}\d+-\d+[a-z]?|[A-Z]{1,2}\d+-\d+|[A-Z]{1,2}\d+[a-z]?)'
        def replace_with_link(match):
            found_code = match.group(1).upper()
            if found_code in sign_map:
                return f'<a href="#" class="internal-link" onclick="window.scrollToSign(\'{found_code}\'); return false;">{match.group(1)}</a>'
            return match.group(1)
        
        if title_text and any(word in title_text.lower() for word in ['use', 'superseded', 'longer used']):
            sign['title_html'] = re.sub(pattern, replace_with_link, title_text)
        else:
            sign['title_html'] = title_text

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NSW Traffic Signs Catalogue</title>
    <style>
        :root {
            --primary-color: #002664;
            --secondary-color: #d7153a;
            --bg-color: #f0f2f5;
            --card-bg: #ffffff;
            --text-color: #1a1a1b;
            --border-color: #d1d5db;
        }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg-color); color: var(--text-color); margin: 0; padding: 20px; line-height: 1.5; }
        
        header { 
            margin-bottom: 24px; 
            padding-bottom: 12px; 
            border-bottom: 3px solid var(--primary-color); 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        h1 { color: var(--primary-color); margin: 0; font-size: 1.75em; font-weight: 800; letter-spacing: -0.5px; }
        
        .controls { 
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 24px;
            background: #ffffff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            align-items: flex-start;
            border: 1px solid #e5e7eb;
        }
        
        .control-item { display: flex; flex-direction: column; gap: 6px; }
        .control-item label { font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
        
        input[type="text"], select { 
            padding: 8px 12px; 
            border: 1.5px solid #e5e7eb; 
            border-radius: 6px; 
            font-size: 14px; 
            background-color: #f9fafb;
            transition: all 0.2s;
            color: #111827;
        }
        input[type="text"]:focus, select:focus { border-color: var(--primary-color); outline: none; background-color: #fff; box-shadow: 0 0 0 3px rgba(0,38,100,0.1); }
        
        select[multiple] { height: 100px; min-width: 180px; }
        #searchBar { width: 260px; }

        .series-container {
            background: #f9fafb;
            border: 1.5px solid #e5e7eb;
            border-radius: 6px;
            padding: 10px;
            min-width: 280px;
        }
        .checkbox-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px 16px;
        }
        .checkbox-item {
            display: flex;
            align-items: center;
            font-size: 13px;
            color: #374151;
            cursor: pointer;
            user-select: none;
            font-weight: 500;
        }
        .checkbox-item input { 
            margin-right: 8px; 
            width: 16px; 
            height: 16px; 
            cursor: pointer; 
            accent-color: var(--primary-color);
        }
        .checkbox-item:hover { color: var(--primary-color); }

        .filter-group-vertical { display: flex; flex-direction: column; gap: 12px; }

        .sign-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); 
            gap: 20px; 
        }
        
        .sign-card { 
            background: var(--card-bg); 
            border-radius: 12px; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
            overflow: hidden; 
            transition: transform 0.2s, box-shadow 0.2s; 
            display: flex; 
            flex-direction: column; 
            border: 1px solid #e5e7eb;
        }
        .sign-card:hover { transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); border-color: var(--primary-color); }
        .sign-card.highlight { border: 3px solid var(--secondary-color); background-color: #fff5f5; }
        
        .sign-image-container { 
            height: 180px; 
            background: #fff; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            padding: 12px; 
            border-bottom: 1px solid #f3f4f6;
            position: relative;
        }
        .sign-image-container img { 
            max-width: 100%; 
            max-height: 100%; 
            object-fit: contain; 
        }

        .sign-info { padding: 16px; flex-grow: 1; display: flex; flex-direction: column; }
        .sign-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
        .sign-no { font-weight: 800; color: var(--secondary-color); font-size: 1.25em; letter-spacing: -0.02em; }
        
        .sizes-container {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-bottom: 12px;
        }
        .size-badge { 
            background: #374151; 
            color: #fff; 
            padding: 2px 6px; 
            border-radius: 4px;
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 0.7em;
            display: flex;
            gap: 4px;
            align-items: center;
        }
        .size-label { font-weight: 600; color: #9ca3af; }
        .size-dims { font-weight: 700; }

        .sign-title { font-size: 0.95em; font-weight: 700; margin-bottom: 12px; line-height: 1.4; color: #111827; min-height: 2.8em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
        .internal-link { color: var(--secondary-color); text-decoration: underline; cursor: pointer; font-weight: 700; }
        
        .detail-row { font-size: 0.75em; margin-bottom: 4px; display: flex; gap: 8px; align-items: baseline; }
        .detail-label { font-weight: 700; color: #6b7280; min-width: 60px; text-transform: uppercase; font-size: 0.9em; }
        .detail-value { color: #1f2937; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }

        .tags { margin-top: auto; padding-top: 12px; display: flex; flex-wrap: wrap; gap: 6px; }
        .tag { padding: 2px 8px; border-radius: 6px; font-size: 0.7em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.02em; }
        .tag-standard { background-color: #dcfce7; color: #166534; }
        .tag-non-standard { background-color: #fef3c7; color: #92400e; }
        .tag-superseded { background-color: #f3e8ff; color: #6b21a8; }
        .tag-not-nsw { background-color: #fee2e2; color: #991b1b; }
        .tag-available { background-color: #e0f2fe; color: #075985; }

        .sign-links { padding: 12px 16px; background: #f9fafb; border-top: 1px solid #f3f4f6; display: flex; gap: 8px; }
        .btn { text-decoration: none; color: var(--primary-color); font-size: 0.8em; font-weight: 700; flex: 1; text-align: center; padding: 8px; border: 1.5px solid var(--primary-color); border-radius: 6px; cursor: pointer; transition: all 0.2s; }
        .btn:hover { background: var(--primary-color); color: white; }
        .btn-pdf { border-color: var(--secondary-color); color: var(--secondary-color); }
        .btn-pdf:hover { background: var(--secondary-color); color: white; }
        
        .btn-clear { background: #fff; border: 1.5px solid #d1d5db; color: #374151; font-weight: 600; padding: 10px 20px; border-radius: 6px; }
        .btn-clear:hover { background: #f3f4f6; border-color: #9ca3af; color: #111827; }

        #stats { font-weight: 700; color: #4b5563; background: #fff; border: 1px solid #e5e7eb; padding: 6px 12px; border-radius: 20px; font-size: 0.85em; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        
        @media (max-width: 1200px) {
            .controls { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 768px) {
            body { padding: 10px; }
            .controls { flex-direction: column; width: 100%; box-sizing: border-box; }
            #searchBar, .series-container { width: 100%; min-width: 0; }
        }
    </style>
</head>
<body>
<header>
    <h1>NSW Traffic Signs</h1>
    <div id="stats">...</div>
</header>

<div class="controls">
    <div class="filter-group-vertical">
        <div class="control-item">
            <label>Search Signs</label>
            <input type="text" id="searchBar" placeholder="Search Code, Title, Rule...">
        </div>
        <div class="control-item">
            <select id="filterNSW">
                <option value="all">Any NSW Usage</option>
                <option value="used">Used in NSW</option>
                <option value="not-used">Not Used in NSW</option>
            </select>
        </div>
    </div>
    
    <div class="control-item">
        <label>Filter by Series</label>
        <div class="series-container">
            <div class="checkbox-group" id="seriesCheckboxes">
                <label class="checkbox-item"><input type="checkbox" value="R"> Regulatory (R)</label>
                <label class="checkbox-item"><input type="checkbox" value="W"> Warning (W)</label>
                <label class="checkbox-item"><input type="checkbox" value="G"> Guide (G)</label>
                <label class="checkbox-item"><input type="checkbox" value="T"> Temporary (T)</label>
                <label class="checkbox-item"><input type="checkbox" value="GE"> Motorway (GE)</label>
                <label class="checkbox-item"><input type="checkbox" value="RM"> Markings (RM)</label>
            </div>
        </div>
    </div>

    <div class="control-item">
        <label>Technical Reference</label>
        <select id="filterTech" multiple title="Hold Ctrl to multi-select"></select>
    </div>

    <div class="control-item">
        <label>Standardization</label>
        <select id="filterStandard" multiple>
            <option value="Yes">Standard Sign</option>
            <option value="No">Non-Standard</option>
            <option value="-">Undefined</option>
        </select>
    </div>

    <div class="control-item">
        <label>Usage Status</label>
        <select id="filterStatus" multiple>
            <option value="Active">Active Only</option>
            <option value="Superseded">Superseded</option>
        </select>
    </div>

    <div class="control-item" style="align-self: center; margin-left: auto;">
        <button class="btn btn-clear" onclick="clearFilters()">Reset All</button>
    </div>
</div>

<div class="sign-grid" id="signGrid"></div>

<script>
    const allSigns = %DATA%;
    const signGrid = document.getElementById('signGrid');
    const searchBar = document.getElementById('searchBar');
    const filterTech = document.getElementById('filterTech');
    const filterSeries = document.getElementById('seriesCheckboxes');
    const filterStandard = document.getElementById('filterStandard');
    const filterStatus = document.getElementById('filterStatus');
    const filterNSW = document.getElementById('filterNSW');
    const stats = document.getElementById('stats');

    window.scrollToSign = function(signCode) {
        clearFilters();
        searchBar.value = signCode;
        filterSigns();
        setTimeout(() => {
            const card = Array.from(document.querySelectorAll('.sign-card')).find(c => c.querySelector('.sign-no').innerText.toUpperCase() === signCode.toUpperCase());
            if (card) {
                card.classList.add('highlight');
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTimeout(() => card.classList.remove('highlight'), 3000);
            }
        }, 50);
    };

    function clearFilters() {
        searchBar.value = '';
        filterNSW.value = 'all';
        [filterTech, filterStandard, filterStatus].forEach(sel => {
            Array.from(sel.options).forEach(opt => opt.selected = false);
        });
        filterSeries.querySelectorAll('input').forEach(cb => cb.checked = false);
        filterSigns();
    }

    function initTechFilter() {
        const refs = new Set();
        allSigns.forEach(s => {
            const ref = s.primary_technical_reference;
            if (ref && ref !== '-' && ref !== 'NA' && ref.length > 2) {
                const core = ref.split('(')[0].split('-')[0].trim();
                if (core.length > 2) refs.add(core);
            }
        });
        Array.from(refs).sort().forEach(ref => {
            const opt = document.createElement('option');
            opt.value = opt.innerText = ref;
            filterTech.appendChild(opt);
        });
    }

    function renderSigns(signs) {
        signGrid.innerHTML = '';
        const fallbackImg = 'https://www.transport.nsw.gov.au/themes/tfnsw_corp_theme/source/tfnsw/components/header/images/logo-TfNSW.png';
        
        signs.forEach(sign => {
            const card = document.createElement('div');
            card.className = 'sign-card';
            
            const isSuperseded = (sign.title || '').toLowerCase().includes('superseded') || (sign.sign_no || '').toLowerCase().includes('superseded');
            const isNotNSW = (sign.title || '').toLowerCase().includes('not used in nsw') || (sign.normalization_metadata && sign.normalization_metadata.note && sign.normalization_metadata.note.toLowerCase().includes('not used in nsw'));

            let sizesHtml = '';
            (sign.sizes || []).forEach(sz => {
                const label = (sz.label || '').replace(/&nbsp;/g, '').trim();
                const w = (sz.w || '').replace(/&nbsp;/g, '').trim();
                const h = (sz.h || '').replace(/&nbsp;/g, '').trim();
                
                const dims = (w !== '-' && h !== '-' && w !== '' && h !== '') ? `${w}x${h}` : '';
                const hasLabel = (label !== '-' && label !== '');
                
                if (hasLabel || dims) {
                    sizesHtml += `<div class="size-badge"><span class="size-label">${hasLabel ? label : ''}</span><span class="size-dims">${dims || 'TBD'}</span></div>`;
                }
            });

            const imgSrc = sign.local_image;
            const remoteImg = sign.image_url;

            card.innerHTML = `
                <div class="sign-image-container">
                    <img src="${imgSrc}" loading="lazy" onerror="this.onerror=null; this.src='${remoteImg}'; this.onerror=function(){this.src='${fallbackImg}'; this.style.opacity='0.1'}">
                </div>
                <div class="sign-info">
                    <div class="sign-header"><div class="sign-no">${sign.sign_no || 'TBD'}</div></div>
                    <div class="sizes-container">${sizesHtml}</div>
                    <div class="sign-title">${sign.title_html || 'Untitled'}</div>
                    ${sign.legislative_reference && sign.legislative_reference !== 'NA' ? `<div class="detail-row"><span class="detail-label">Leg:</span><span class="detail-value" title="${sign.legislative_reference}">${sign.legislative_reference}</span></div>` : ''}
                    ${sign.primary_technical_reference && sign.primary_technical_reference !== 'NA' ? `<div class="detail-row"><span class="detail-label">Tech:</span><span class="detail-value" title="${sign.primary_technical_reference}">${sign.primary_technical_reference}</span></div>` : ''}
                    <div class="tags">
                        ${sign.standard_sign === 'Yes' ? '<span class="tag tag-standard">Std</span>' : '<span class="tag tag-non-standard">Non</span>'}
                        ${isSuperseded ? '<span class="tag tag-superseded">Sup</span>' : ''}
                        ${isNotNSW ? '<span class="tag tag-not-nsw">Not NSW</span>' : ''}
                        ${sign.use_by_council && sign.use_by_council.toLowerCase().includes('available') ? '<span class="tag tag-available">OK</span>' : ''}
                    </div>
                </div>
                <div class="sign-links">
                    <a href="${sign.url}" target="_blank" class="btn">Detail</a>
                    ${sign.pdf_url ? `<a href="${sign.pdf_url}" target="_blank" class="btn btn-pdf">PDF</a>` : ''}
                </div>`;
            signGrid.appendChild(card);
        });
        stats.innerText = `Showing ${signs.length} of ${allSigns.length}`;
    }

    function getSelectedValues(select) {
        return Array.from(select.selectedOptions).map(opt => opt.value);
    }

    function getSelectedCheckboxes(container) {
        return Array.from(container.querySelectorAll('input:checked')).map(cb => cb.value);
    }

    function filterSigns() {
        const term = searchBar.value.toLowerCase();
        const selectedTech = getSelectedValues(filterTech);
        const nswFilter = filterNSW.value;
        
        const selectedSeries = getSelectedCheckboxes(filterSeries);
        const selectedStd = getSelectedValues(filterStandard);
        const selectedStatus = getSelectedValues(filterStatus);

        const filtered = allSigns.filter(s => {
            const searchText = `${s.sign_no || ''} ${s.title || ''} ${s.legislative_reference || ''} ${s.primary_technical_reference || ''}`.toLowerCase();
            if (term && !searchText.includes(term)) return false;
            
            if (selectedTech.length > 0) {
                if (!s.primary_technical_reference || !selectedTech.some(t => s.primary_technical_reference.includes(t))) return false;
            }
            
            if (selectedSeries.length > 0) {
                const sCode = (s.sign_no || '').toUpperCase();
                if (!selectedSeries.some(prefix => sCode.startsWith(prefix))) return false;
            }
            
            if (selectedStd.length > 0) {
                if (!selectedStd.includes(s.standard_sign)) return false;
            }
            
            const isSup = (s.title || '').toLowerCase().includes('superseded') || (s.sign_no || '').toLowerCase().includes('superseded');
            if (selectedStatus.length > 0) {
                const status = isSup ? 'Superseded' : 'Active';
                if (!selectedStatus.includes(status)) return false;
            }
            
            const isNotNSW = (s.title || '').toLowerCase().includes('not used in nsw');
            if (nswFilter === 'used' && isNotNSW) return false;
            if (nswFilter === 'not-used' && !isNotNSW) return false;

            return true;
        });
        renderSigns(filtered);
    }

    searchBar.addEventListener('input', filterSigns);
    filterSeries.addEventListener('change', filterSigns);
    [filterTech, filterStandard, filterStatus, filterNSW].forEach(el => el.addEventListener('change', filterSigns));
    allSigns.sort((a, b) => (a.sign_no || 'ZZZ').localeCompare(b.sign_no || 'ZZZ', undefined, {numeric: true}));
    initTechFilter();
    renderSigns(allSigns);
</script>
</body>
</html>"""

    final_html = html_template.replace('%DATA%', json.dumps(data))
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"Successfully created {output_file} with local image support and Clear button.")

if __name__ == "__main__":
    import sys
    inp = sys.argv[1] if len(sys.argv) > 1 else 'nsw_traffic_signs_unified.json'
    out = sys.argv[2] if len(sys.argv) > 2 else 'interactive_catalogue_unified.html'
    build_viewer(inp, out)
