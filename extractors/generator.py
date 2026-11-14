"""
Link Extractor Generator
Generates a customized extract_links.js script with the user's specific URLs pre-loaded,
ready to be pasted directly into DevTools on the file host.
"""

import json
from pathlib import Path
from typing import List

def generate_extractor_script(urls: List[str], output_path: Path) -> Path:
    """
    Generates an extract_links.js file with pre-loaded URLs.
    """
    clean_urls = [u.strip() for u in urls if u.strip() and not u.strip().startswith("#")]
    urls_json = json.dumps(clean_urls, indent=4)

    js_template = f"""/**
 * AnyRepackDownloader - Pre-Configured Direct Link Extractor
 * Pre-loaded with {len(clean_urls)} files.
 *
 * HOW TO USE:
 * 1. Open your browser and visit: {clean_urls[0] if clean_urls else 'https://fuckingfast.co'}
 * 2. If Cloudflare prompts you ('Verify you are human'), complete it once in the browser.
 * 3. Press F12 to open Developer Tools, and switch to the 'Console' tab.
 * 4. Paste this entire script into the Console and press Enter.
 * 5. Wait for it to process all links.
 *    A file named 'direct_links.txt' will be downloaded automatically!
 * 6. Feed 'direct_links.txt' into AnyRepackDownloader.
 */

(async function() {{
    const links = {urls_json};

    const CONFIG = {{
        concurrency: 3,
        delayMs: 600
    }};

    const sleep = ms => new Promise(r => setTimeout(r, ms));

    console.clear();
    console.log('%c🚀 Starting Direct Link Extractor ({len(clean_urls)} Parts)...', 'color:#38bdf8;font-weight:bold;font-size:14px;');

    if (!location.hostname.includes('fuckingfast')) {{
        alert('Notice: Please run this script while on https://fuckingfast.co so your verified Cloudflare session is active!');
    }}

    function fileIdOf(link) {{
        return new URL(link, location.origin).pathname.split('/').filter(Boolean).pop();
    }}

    function readRedirect(headers) {{
        return headers.get('hx-redirect') || headers.get('HX-Redirect')
            || headers.get('hx-location') || headers.get('location');
    }}

    // Visual Overlay UI
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:20px;right:20px;z-index:999999;background:rgba(15,23,42,0.95);color:#fff;padding:18px;border-radius:12px;font-family:sans-serif;box-shadow:0 10px 25px rgba(0,0,0,0.5);border:1px solid #38bdf8;width:340px;';
    overlay.innerHTML = '<h3 style=\"margin:0 0 10px;color:#38bdf8;font-size:15px;\">🚀 AnyRepack Extractor</h3><div id=\"ar-prog\" style=\"font-size:13px;margin-bottom:8px;\">Starting extraction...</div><div style=\"background:#334155;border-radius:6px;height:10px;overflow:hidden;\"><div id=\"ar-bar\" style=\"background:#10b981;height:100%;width:0%;transition:width 0.2s;\"></div></div>';
    document.body.appendChild(overlay);

    const progText = document.getElementById('ar-prog');
    const progBar = document.getElementById('ar-bar');

    async function resolveSingle(link, index) {{
        const id = fileIdOf(link);
        const partMatch = link.match(/part\\d+\\.rar/i) || link.match(/part[_-]?\\d+/i);
        const partName = partMatch ? partMatch[0] : `Item ${{index + 1}}`;

        try {{
            const res = await fetch(`/f/${{id}}/go`, {{
                method: 'POST',
                credentials: 'include',
                headers: {{
                    'HX-Request': 'true',
                    'HX-Current-URL': location.href,
                    'Content-Type': 'application/x-www-form-urlencoded',
                }},
                body: '',
            }});
            if (res.ok) {{
                const direct = readRedirect(res.headers);
                if (direct) {{
                    const fullUrl = new URL(direct, location.origin).href;
                    return fullUrl;
                }}
            }}
        }} catch (e) {{}}

        // Fallback: scrape page text
        try {{
            const pageRes = await fetch(`/${{id}}`, {{ credentials: 'include' }});
            if (pageRes.ok) {{
                const html = await pageRes.text();
                const m = html.match(/https?:\\/\\/dl\\.fuckingfast\\.co[^\"\\'\\s]+/i);
                if (m) return m[0];
            }}
        }} catch (e) {{}}

        return null;
    }}

    let completed = 0;
    const resolvedUrls = new Array(links.length);
    let cursor = 0;

    async function worker() {{
        while (cursor < links.length) {{
            const idx = cursor++;
            const direct = await resolveSingle(links[idx], idx);
            resolvedUrls[idx] = direct;
            completed++;

            const pct = Math.round((completed / links.length) * 100);
            progText.textContent = `[${{completed}}/${{links.length}}] ${{direct ? '✓ Extracted' : '✗ Failed'}}: Item ${{idx + 1}}`;
            progBar.style.width = pct + '%';
            console.log(`[${{completed}}/${{links.length}}] ${{direct ? '✅' : '❌'}} ${{links[idx]}} -> ${{direct || 'Failed'}}`);

            await sleep(CONFIG.delayMs);
        }}
    }}

    const pool = Array.from({{ length: CONFIG.concurrency }}, () => worker());
    await Promise.all(pool);

    const validUrls = resolvedUrls.filter(Boolean);
    progText.innerHTML = `<b>🎉 Done! Extracted ${{validUrls.length}}/${{links.length}} links</b>`;
    progBar.style.background = '#38bdf8';

    if (validUrls.length > 0) {{
        const textData = validUrls.join('\\n');
        try {{
            await navigator.clipboard.writeText(textData);
            progText.innerHTML += '<br><small style=\"color:#67e8f9;\">✓ Copied to clipboard!</small>';
        }} catch (e) {{}}

        const blob = new Blob([textData], {{ type: 'text/plain' }});
        const downloadLink = document.createElement('a');
        downloadLink.href = URL.createObjectURL(blob);
        downloadLink.download = 'direct_links.txt';
        downloadLink.click();
        URL.revokeObjectURL(downloadLink.href);
    }} else {{
        alert('Could not resolve links. Please make sure you are logged in or on the file host page with human verification passed.');
    }}
}})();
"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(js_template)

    return output_path
