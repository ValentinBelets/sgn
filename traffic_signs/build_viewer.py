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
        def replace_with_link(match: re.Match[str]) -> str:
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
            --primary: #002664;
            --secondary: #d7153a;
            --bg: #f0f2f5;
            --card-bg: #ffffff;
            --text: #1a1a1b;
            --border: #e5e7eb;
            --sidebar-w: 252px;
            --series-R: #1d4ed8;
            --series-W: #d97706;
            --series-G: #15803d;
            --series-T: #c2410c;
            --series-GE: #7c3aed;
            --series-RM: #0e7490;
        }
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            line-height: 1.5;
            display: flex;
            min-height: 100vh;
        }
        /* ── SIDEBAR ── */
        #sidebar {
            width: var(--sidebar-w);
            min-width: var(--sidebar-w);
            background: #fff;
            border-right: 1px solid var(--border);
            padding: 18px 14px;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .sidebar-logo {
            padding-bottom: 14px;
            border-bottom: 2px solid var(--primary);
        }
        .sidebar-logo h1 {
            color: var(--primary);
            font-size: 1.05em;
            font-weight: 800;
            letter-spacing: -0.4px;
            margin: 0 0 2px;
        }
        .sidebar-logo span { font-size: 0.72em; color: #9ca3af; }
        .filter-section { display: flex; flex-direction: column; gap: 6px; }
        .filter-section.tech-flex {
            flex: 1 1 auto;
            min-height: 120px;
        }
        .section-label {
            font-size: 10px;
            font-weight: 800;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        input[type="text"] {
            width: 100%;
            padding: 7px 10px;
            border: 1.5px solid var(--border);
            border-radius: 6px;
            font-size: 13px;
            background: #f9fafb;
            transition: border-color 0.2s, box-shadow 0.2s;
            color: #111827;
        }
        input[type="text"]:focus {
            border-color: var(--primary);
            outline: none;
            background: #fff;
            box-shadow: 0 0 0 3px rgba(0,38,100,0.1);
        }
        select {
            width: 100%;
            padding: 6px 8px;
            border: 1.5px solid var(--border);
            border-radius: 6px;
            font-size: 12px;
            background: #f9fafb;
            color: #111827;
            transition: border-color 0.2s;
        }
        select:focus { border-color: var(--primary); outline: none; }
        select[multiple] { height: 82px; }
        .filter-section.tech-flex select[multiple] {
            height: auto;
            min-height: 120px;
            flex: 1 1 auto;
        }
        .checkbox-group { display: flex; flex-direction: column; gap: 2px; }
        .checkbox-item {
            display: flex;
            align-items: center;
            font-size: 12px;
            color: #374151;
            cursor: pointer;
            user-select: none;
            padding: 4px 6px;
            border-radius: 5px;
            transition: background 0.12s;
        }
        .checkbox-item:hover { background: #f3f4f6; }
        .checkbox-item input {
            margin-right: 7px;
            width: 14px;
            height: 14px;
            cursor: pointer;
            accent-color: var(--primary);
            flex-shrink: 0;
        }
        .series-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            margin-right: 6px;
            flex-shrink: 0;
        }
        .cb-count { margin-left: auto; font-size: 10px; color: #9ca3af; font-weight: 600; }
        .btn-reset {
            width: 100%;
            background: #fff;
            border: 1.5px solid var(--border);
            color: #374151;
            font-weight: 700;
            padding: 8px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.15s;
        }
        .btn-reset:hover { background: #f3f4f6; border-color: #9ca3af; }
        /* ── MAIN ── */
        #main {
            flex: 1;
            min-width: 0;
            padding: 18px 22px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        #top-bar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
        #stats {
            font-weight: 700;
            color: #4b5563;
            background: #fff;
            border: 1px solid var(--border);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            white-space: nowrap;
        }
        .sort-select {
            padding: 4px 8px;
            border: 1.5px solid var(--border);
            border-radius: 6px;
            font-size: 12px;
            background: #fff;
            color: #374151;
            font-weight: 600;
            cursor: pointer;
            width: auto;
        }
        .view-toggle {
            display: flex;
            border: 1.5px solid var(--border);
            border-radius: 6px;
            overflow: hidden;
            background: #fff;
        }
        .view-btn {
            border: none;
            background: transparent;
            padding: 4px 9px;
            cursor: pointer;
            font-size: 15px;
            color: #6b7280;
            transition: all 0.12s;
            line-height: 1;
        }
        .view-btn.active { background: var(--primary); color: #fff; }
        .view-btn:hover:not(.active) { background: #f3f4f6; }
        /* ── ACTIVE CHIPS ── */
        #active-chips { display: flex; flex-wrap: wrap; gap: 5px; min-height: 0; }
        .filter-chip {
            display: flex;
            align-items: center;
            gap: 4px;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1d4ed8;
            border-radius: 20px;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 600;
        }
        .chip-remove {
            cursor: pointer;
            font-size: 13px;
            line-height: 1;
            color: #93c5fd;
            margin-left: 2px;
            transition: color 0.12s;
        }
        .chip-remove:hover { color: var(--secondary); }
        /* ── GRID VIEW ── */
        #signGrid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(255px, 1fr));
            gap: 16px;
        }
        .sign-card {
            background: var(--card-bg);
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.07);
            overflow: hidden;
            transition: transform 0.18s, box-shadow 0.18s;
            display: flex;
            flex-direction: column;
            border: 1px solid var(--border);
        }
        .sign-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            border-color: var(--series-color, var(--primary));
        }
        .sign-card.highlight { border: 3px solid var(--secondary); background-color: #fff5f5; }
        .sign-image-container {
            height: 155px;
            background: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 12px;
            border-bottom: 3px solid var(--series-color, #e5e7eb);
            position: relative;
        }
        .sign-image-container img { max-width: 100%; max-height: 100%; object-fit: contain; }
        .series-badge {
            position: absolute;
            top: 7px;
            right: 7px;
            background: var(--series-color, #6b7280);
            color: #fff;
            font-size: 10px;
            font-weight: 800;
            padding: 2px 7px;
            border-radius: 4px;
            letter-spacing: 0.05em;
        }
        .img-error-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #9ca3af;
            font-size: 11px;
            gap: 3px;
            width: 100%;
            height: 100%;
        }
        .img-error-state .sign-no-placeholder {
            font-size: 1.4em;
            font-weight: 800;
            color: var(--series-color, #d1d5db);
        }
        .sign-info { padding: 13px; flex-grow: 1; display: flex; flex-direction: column; }
        .sign-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px; }
        .sign-no { font-weight: 800; color: var(--series-color, var(--secondary)); font-size: 1.15em; letter-spacing: -0.02em; }
        .sizes-container { display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 9px; }
        .size-badge {
            background: #f3f4f6;
            color: #374151;
            border: 1px solid var(--border);
            padding: 1px 5px;
            border-radius: 3px;
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 0.67em;
            display: flex;
            gap: 3px;
            align-items: center;
        }
        .size-label { font-weight: 600; color: #9ca3af; }
        .size-dims { font-weight: 700; }
        .sign-title {
            font-size: 0.87em;
            font-weight: 600;
            margin-bottom: 9px;
            line-height: 1.4;
            color: #111827;
            min-height: 2.45em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        .internal-link { color: var(--secondary); text-decoration: underline; cursor: pointer; font-weight: 700; }
        .detail-row { font-size: 0.71em; margin-bottom: 3px; display: flex; gap: 6px; align-items: baseline; }
        .detail-label { font-weight: 700; color: #9ca3af; min-width: 52px; text-transform: uppercase; font-size: 0.9em; }
        .detail-value { color: #374151; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .tags { margin-top: auto; padding-top: 9px; display: flex; flex-wrap: wrap; gap: 4px; }
        .tag { padding: 2px 8px; border-radius: 20px; font-size: 0.67em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; }
        .tag-standard { background: #dcfce7; color: #166534; }
        .tag-non-standard { background: #fef3c7; color: #92400e; }
        .tag-superseded { background: #f3e8ff; color: #6b21a8; }
        .tag-not-nsw { background: #fee2e2; color: #991b1b; }
        .tag-available { background: #e0f2fe; color: #075985; }
        .sign-links { padding: 9px 13px; background: #f9fafb; border-top: 1px solid #f3f4f6; display: flex; gap: 7px; }
        .btn { text-decoration: none; color: var(--primary); font-size: 0.77em; font-weight: 700; flex: 1; text-align: center; padding: 6px; border: 1.5px solid var(--primary); border-radius: 5px; cursor: pointer; transition: all 0.15s; }
        .btn:hover { background: var(--primary); color: #fff; }
        .btn-pdf { border-color: var(--secondary); color: var(--secondary); }
        .btn-pdf:hover { background: var(--secondary); color: #fff; }
        /* ── LIST VIEW ── */
        #signGrid.list-view {
            display: flex;
            flex-direction: column;
            gap: 0;
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
            background: #fff;
        }
        #signGrid.list-view .sign-card {
            border-radius: 0;
            border: none;
            border-bottom: 1px solid #f3f4f6;
            flex-direction: row;
            align-items: center;
            box-shadow: none;
        }
        #signGrid.list-view .sign-card:last-child { border-bottom: none; }
        #signGrid.list-view .sign-card:hover { transform: none; background: #f8faff; }
        #signGrid.list-view .sign-image-container {
            width: 72px;
            min-width: 72px;
            height: 54px;
            border-bottom: none;
            border-right: 3px solid var(--series-color, #e5e7eb);
            border-radius: 0;
        }
        #signGrid.list-view .series-badge { display: none; }
        #signGrid.list-view .sign-info {
            flex-direction: row;
            align-items: center;
            padding: 8px 12px;
            gap: 10px;
            flex-wrap: wrap;
        }
        #signGrid.list-view .sign-no { min-width: 72px; font-size: 0.9em; margin-bottom: 0; }
        #signGrid.list-view .sign-header { margin-bottom: 0; flex-shrink: 0; }
        #signGrid.list-view .sign-title {
            flex: 1;
            min-width: 160px;
            min-height: 0;
            -webkit-line-clamp: 1;
            margin-bottom: 0;
        }
        #signGrid.list-view .sizes-container { display: none; }
        #signGrid.list-view .detail-row { display: none; }
        #signGrid.list-view .tags { padding-top: 0; margin-top: 0; }
        #signGrid.list-view .sign-links {
            padding: 7px 10px;
            background: transparent;
            border-top: none;
            border-left: 1px solid #f3f4f6;
            flex-direction: column;
            min-width: 90px;
            gap: 3px;
        }
        /* ── EMPTY STATE ── */
        #empty-state {
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 60px 20px;
            color: #9ca3af;
            gap: 10px;
        }
        #empty-state .empty-icon { font-size: 44px; }
        #empty-state h3 { margin: 0; color: #374151; font-size: 1.05em; }
        #empty-state p { margin: 0; font-size: 0.83em; text-align: center; max-width: 280px; }
        #empty-state button {
            margin-top: 6px;
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 7px 18px;
            border-radius: 6px;
            font-weight: 700;
            cursor: pointer;
            font-size: 12px;
        }
        /* ── RESPONSIVE ── */
        @media (max-width: 768px) {
            body { flex-direction: column; }
            #sidebar { width: 100%; min-width: 0; position: relative; height: auto; border-right: none; border-bottom: 1px solid var(--border); }
            .filter-section.tech-flex { min-height: 0; }
            .filter-section.tech-flex select[multiple] { height: 82px; min-height: 82px; }
            #main { padding: 12px; }
        }
    </style>
</head>
<body>
<aside id="sidebar">
    <div class="sidebar-logo">
        <h1>NSW Traffic Signs</h1>
        <span>Interactive Catalogue</span>
    </div>
    <div class="filter-section">
        <label class="section-label">Search</label>
        <input type="text" id="searchBar" placeholder="Sign code, title, rule\u2026">
    </div>
    <div class="filter-section">
        <label class="section-label">Series</label>
        <div class="checkbox-group" id="seriesCheckboxes">
            <label class="checkbox-item"><input type="checkbox" value="R"><span class="series-dot" style="background:var(--series-R)"></span>Regulatory (R)<span class="cb-count" data-series="R"></span></label>
            <label class="checkbox-item"><input type="checkbox" value="W"><span class="series-dot" style="background:var(--series-W)"></span>Warning (W)<span class="cb-count" data-series="W"></span></label>
            <label class="checkbox-item"><input type="checkbox" value="G"><span class="series-dot" style="background:var(--series-G)"></span>Guide (G)<span class="cb-count" data-series="G"></span></label>
            <label class="checkbox-item"><input type="checkbox" value="T"><span class="series-dot" style="background:var(--series-T)"></span>Temporary (T)<span class="cb-count" data-series="T"></span></label>
            <label class="checkbox-item"><input type="checkbox" value="GE"><span class="series-dot" style="background:var(--series-GE)"></span>Motorway (GE)<span class="cb-count" data-series="GE"></span></label>
            <label class="checkbox-item"><input type="checkbox" value="RM"><span class="series-dot" style="background:var(--series-RM)"></span>Markings (RM)<span class="cb-count" data-series="RM"></span></label>
        </div>
    </div>
    <div class="filter-section">
        <label class="section-label">Standardisation</label>
        <select id="filterStandard" multiple>
            <option value="Yes">Standard Sign</option>
            <option value="No">Non-Standard</option>
            <option value="-">Undefined</option>
        </select>
    </div>
    <div class="filter-section">
        <label class="section-label">Usage Status</label>
        <select id="filterStatus" multiple>
            <option value="Active">Active</option>
            <option value="Superseded">Superseded</option>
        </select>
    </div>
    <div class="filter-section">
        <label class="section-label">NSW Usage</label>
        <select id="filterNSW">
            <option value="all">Any</option>
            <option value="used">Used in NSW</option>
            <option value="not-used">Not Used in NSW</option>
        </select>
    </div>
    <div class="filter-section tech-flex">
        <label class="section-label">Technical Reference</label>
        <select id="filterTech" multiple title="Hold Ctrl/Cmd for multi-select"></select>
    </div>
    <button class="btn-reset" onclick="clearFilters()">&#8635; Reset All Filters</button>
</aside>

<main id="main">
    <div id="top-bar">
        <span id="stats">\u2026</span>
        <select class="sort-select" id="sortSelect">
            <option value="sign_no">Sort: Sign #</option>
            <option value="series">Sort: Series</option>
            <option value="title">Sort: Title</option>
        </select>
        <div class="view-toggle">
            <button class="view-btn active" id="btnGrid" onclick="setView('grid')" title="Grid view">&#8862;</button>
            <button class="view-btn" id="btnList" onclick="setView('list')" title="List view">&#8801;</button>
        </div>
    </div>
    <div id="active-chips"></div>
    <div id="signGrid"></div>
    <div id="empty-state">
        <div class="empty-icon">&#x1F6A7;</div>
        <h3>No signs match your filters</h3>
        <p>Try adjusting or clearing your search criteria.</p>
        <button onclick="clearFilters()">Clear All Filters</button>
    </div>
</main>

<script>
    const SERIES_COLORS = { R:'#1d4ed8', W:'#d97706', G:'#15803d', T:'#c2410c', GE:'#7c3aed', RM:'#0e7490' };

    function getSeriesFromCode(code) {
        if (!code) return null;
        const c = code.toUpperCase();
        if (c.startsWith('RM')) return 'RM';
        if (c.startsWith('GE')) return 'GE';
        if (c.startsWith('R')) return 'R';
        if (c.startsWith('W')) return 'W';
        if (c.startsWith('G')) return 'G';
        if (c.startsWith('T')) return 'T';
        return null;
    }

    const allSigns = %DATA%;
    allSigns.forEach(s => {
        s._series = getSeriesFromCode(s.sign_no);
        s._isSuperseded = (s.title || '').toLowerCase().includes('superseded') || (s.sign_no || '').toLowerCase().includes('superseded');
        s._isNotNSW = (s.title || '').toLowerCase().includes('not used in nsw') ||
            (s.normalization_metadata && s.normalization_metadata.note && s.normalization_metadata.note.toLowerCase().includes('not used in nsw'));
    });

    const signGrid = document.getElementById('signGrid');
    const emptyState = document.getElementById('empty-state');
    const searchBar = document.getElementById('searchBar');
    const filterTech = document.getElementById('filterTech');
    const filterSeries = document.getElementById('seriesCheckboxes');
    const filterStandard = document.getElementById('filterStandard');
    const filterStatus = document.getElementById('filterStatus');
    const filterNSW = document.getElementById('filterNSW');
    const stats = document.getElementById('stats');
    const activeChips = document.getElementById('active-chips');
    let currentView = 'grid';

    function initCountBadges() {
        const counts = {};
        allSigns.forEach(s => { if (s._series) counts[s._series] = (counts[s._series] || 0) + 1; });
        document.querySelectorAll('.cb-count').forEach(el => {
            const s = el.dataset.series;
            el.textContent = counts[s] ? counts[s] : '';
        });
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
            opt.value = opt.textContent = ref;
            filterTech.appendChild(opt);
        });
    }

    function renderSigns(signs) {
        signGrid.innerHTML = '';
        if (signs.length === 0) {
            emptyState.style.display = 'flex';
            signGrid.style.display = 'none';
            return;
        }
        emptyState.style.display = 'none';
        if (currentView === 'list') {
            signGrid.style.display = 'flex';
            signGrid.classList.add('list-view');
        } else {
            signGrid.style.display = 'grid';
            signGrid.classList.remove('list-view');
        }

        const fragment = document.createDocumentFragment();
        signs.forEach(sign => {
            const seriesColor = SERIES_COLORS[sign._series] || '#6b7280';
            const card = document.createElement('div');
            card.className = 'sign-card';
            card.id = 'card-' + (sign.sign_no || '').replace(/[^a-zA-Z0-9]/g, '_');
            card.style.setProperty('--series-color', seriesColor);

            let sizesHtml = '';
            (sign.sizes || []).forEach(sz => {
                const label = (sz.label || '').replace(/&nbsp;/g, '').trim();
                const w = (sz.w || '').replace(/&nbsp;/g, '').trim();
                const h = (sz.h || '').replace(/&nbsp;/g, '').trim();
                const dims = (w && w !== '-' && h && h !== '-') ? w + '\\xd7' + h : '';
                const hasLabel = label && label !== '-';
                if (hasLabel || dims) {
                    sizesHtml += '<div class="size-badge"><span class="size-label">' + (hasLabel ? label : '') + '</span><span class="size-dims">' + (dims || '\\u2014') + '</span></div>';
                }
            });

            const imgSrc = sign.local_image || '';
            const remoteImg = sign.image_url || '';
            const signCode = sign.sign_no || 'TBD';
            const seriesBadge = sign._series ? '<div class="series-badge">' + sign._series + '</div>' : '';

            card.innerHTML =
                '<div class="sign-image-container">' +
                    '<img src="' + imgSrc + '" loading="lazy" alt="' + signCode + '" data-remote="' + remoteImg + '" onerror="if(this.dataset.remote&&this.src!==this.dataset.remote){this.src=this.dataset.remote;}else{this.style.display=\\\'none\\\';this.nextElementSibling.style.display=\\\'flex\\\';}">' +
                    '<div class="img-error-state" style="display:none"><div class="sign-no-placeholder">' + signCode + '</div><span>No image</span></div>' +
                    seriesBadge +
                '</div>' +
                '<div class="sign-info">' +
                    '<div class="sign-header"><div class="sign-no">' + signCode + '</div></div>' +
                    '<div class="sizes-container">' + sizesHtml + '</div>' +
                    '<div class="sign-title">' + (sign.title_html || 'Untitled') + '</div>' +
                    (sign.legislative_reference && sign.legislative_reference !== 'NA' ? '<div class="detail-row"><span class="detail-label">Leg</span><span class="detail-value" title="' + sign.legislative_reference + '">' + sign.legislative_reference + '</span></div>' : '') +
                    (sign.primary_technical_reference && sign.primary_technical_reference !== 'NA' ? '<div class="detail-row"><span class="detail-label">Tech</span><span class="detail-value" title="' + sign.primary_technical_reference + '">' + sign.primary_technical_reference + '</span></div>' : '') +
                    '<div class="tags">' +
                        (sign.standard_sign === 'Yes' ? '<span class="tag tag-standard">Standard</span>' : '<span class="tag tag-non-standard">Non-Standard</span>') +
                        (sign._isSuperseded ? '<span class="tag tag-superseded">Superseded</span>' : '') +
                        (sign._isNotNSW ? '<span class="tag tag-not-nsw">Not NSW</span>' : '') +
                        (sign.use_by_council && sign.use_by_council.toLowerCase().includes('available') ? '<span class="tag tag-available">Available</span>' : '') +
                    '</div>' +
                '</div>' +
                '<div class="sign-links">' +
                    '<a href="' + sign.url + '" target="_blank" rel="noopener" class="btn">Detail</a>' +
                    (sign.pdf_url ? '<a href="' + sign.pdf_url + '" target="_blank" rel="noopener" class="btn btn-pdf">PDF</a>' : '') +
                '</div>';
            fragment.appendChild(card);
        });
        signGrid.appendChild(fragment);
        stats.textContent = 'Showing ' + signs.length.toLocaleString() + ' of ' + allSigns.length.toLocaleString() + ' signs';
    }

    function renderChips(term, selectedTech, selectedSeries, selectedStd, selectedStatus, nswFilter) {
        activeChips.innerHTML = '';
        function add(label, onRemove) {
            const chip = document.createElement('div');
            chip.className = 'filter-chip';
            chip.innerHTML = label + '<span class="chip-remove" title="Remove">&times;</span>';
            chip.querySelector('.chip-remove').onclick = onRemove;
            activeChips.appendChild(chip);
        }
        if (term) add('"' + term + '"', function() { searchBar.value = ''; filterSigns(); });
        selectedSeries.forEach(function(s) { add('Series: ' + s, function() { filterSeries.querySelector('input[value="' + s + '"]').checked = false; filterSigns(); }); });
        selectedTech.forEach(function(t) { add('Ref: ' + t, function() { Array.from(filterTech.options).find(function(o){ return o.value === t; }).selected = false; filterSigns(); }); });
        selectedStd.forEach(function(v) { add('Std: ' + v, function() { Array.from(filterStandard.options).find(function(o){ return o.value === v; }).selected = false; filterSigns(); }); });
        selectedStatus.forEach(function(v) { add('Status: ' + v, function() { Array.from(filterStatus.options).find(function(o){ return o.value === v; }).selected = false; filterSigns(); }); });
        if (nswFilter !== 'all') add('NSW: ' + (nswFilter === 'used' ? 'Used' : 'Not Used'), function() { filterNSW.value = 'all'; filterSigns(); });
    }

    function getSelectedValues(sel) { return Array.from(sel.selectedOptions).map(function(o){ return o.value; }); }
    function getSelectedCheckboxes(container) { return Array.from(container.querySelectorAll('input:checked')).map(function(cb){ return cb.value; }); }

    function getSortedSigns(signs) {
        const by = document.getElementById('sortSelect').value;
        return signs.slice().sort(function(a, b) {
            if (by === 'title') return (a.title || '').localeCompare(b.title || '');
            if (by === 'series') {
                const sc = (a._series || 'ZZ').localeCompare(b._series || 'ZZ');
                if (sc !== 0) return sc;
            }
            return (a.sign_no || 'ZZZ').localeCompare(b.sign_no || 'ZZZ', undefined, {numeric: true});
        });
    }

    function filterSigns() {
        const term = searchBar.value.toLowerCase().trim();
        const selectedTech = getSelectedValues(filterTech);
        const nswFilter = filterNSW.value;
        const selectedSeries = getSelectedCheckboxes(filterSeries);
        const selectedStd = getSelectedValues(filterStandard);
        const selectedStatus = getSelectedValues(filterStatus);

        const filtered = allSigns.filter(function(s) {
            if (term) {
                const searchText = ((s.sign_no || '') + ' ' + (s.title || '') + ' ' + (s.legislative_reference || '') + ' ' + (s.primary_technical_reference || '')).toLowerCase();
                if (!searchText.includes(term)) return false;
            }
            if (selectedTech.length > 0 && (!s.primary_technical_reference || !selectedTech.some(function(t){ return s.primary_technical_reference.includes(t); }))) return false;
            if (selectedSeries.length > 0 && (!s._series || !selectedSeries.includes(s._series))) return false;
            if (selectedStd.length > 0 && !selectedStd.includes(s.standard_sign)) return false;
            if (selectedStatus.length > 0) {
                const status = s._isSuperseded ? 'Superseded' : 'Active';
                if (!selectedStatus.includes(status)) return false;
            }
            if (nswFilter === 'used' && s._isNotNSW) return false;
            if (nswFilter === 'not-used' && !s._isNotNSW) return false;
            return true;
        });
        renderChips(term, selectedTech, selectedSeries, selectedStd, selectedStatus, nswFilter);
        renderSigns(getSortedSigns(filtered));
    }

    function clearFilters() {
        searchBar.value = '';
        filterNSW.value = 'all';
        [filterTech, filterStandard, filterStatus].forEach(function(sel){ Array.from(sel.options).forEach(function(o){ o.selected = false; }); });
        filterSeries.querySelectorAll('input').forEach(function(cb){ cb.checked = false; });
        document.getElementById('sortSelect').value = 'sign_no';
        filterSigns();
    }

    function setView(mode) {
        currentView = mode;
        document.getElementById('btnGrid').classList.toggle('active', mode === 'grid');
        document.getElementById('btnList').classList.toggle('active', mode === 'list');
        filterSigns();
    }

    window.scrollToSign = function(signCode) {
        clearFilters();
        searchBar.value = signCode;
        filterSigns();
        setTimeout(function() {
            const card = document.getElementById('card-' + signCode.replace(/[^a-zA-Z0-9]/g, '_'));
            if (card) {
                card.classList.add('highlight');
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTimeout(function(){ card.classList.remove('highlight'); }, 3000);
            }
        }, 60);
    };

    allSigns.sort(function(a, b){ return (a.sign_no || 'ZZZ').localeCompare(b.sign_no || 'ZZZ', undefined, {numeric: true}); });
    initTechFilter();
    initCountBadges();
    renderSigns(allSigns);
    searchBar.addEventListener('input', filterSigns);
    filterSeries.addEventListener('change', filterSigns);
    [filterTech, filterStandard, filterStatus, filterNSW].forEach(function(el){ el.addEventListener('change', filterSigns); });
    document.getElementById('sortSelect').addEventListener('change', filterSigns);
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
