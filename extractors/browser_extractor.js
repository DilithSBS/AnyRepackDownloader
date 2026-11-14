/**
 * Universal FuckingFast & Repack Direct Link Extractor
 * 
 * HOW TO USE:
 * 1. Open your browser and visit https://fuckingfast.co (or open any FuckingFast link).
 * 2. Complete the Cloudflare verification if prompted ("Verify you are human").
 * 3. Press F12 (or Right-Click -> Inspect) and select the "Console" tab.
 * 4. Paste this entire script into the Console and press Enter.
 * 5. A floating extraction panel will appear!
 *    - Paste your share links (or click "Auto-Detect Page Links" if on a repack page).
 *    - Click "Extract Direct Links".
 *    - Once complete, it will automatically download "direct_links.txt" for AnyRepackDownloader!
 */

(function() {
    // Prevent duplicate overlays
    if (document.getElementById('anyrepack-overlay')) {
        document.getElementById('anyrepack-overlay').remove();
    }

    const overlay = document.createElement('div');
    overlay.id = 'anyrepack-overlay';
    overlay.style.cssText = [
        'position: fixed',
        'top: 15px',
        'right: 15px',
        'z-index: 2147483647',
        'width: 380px',
        'max-width: 90vw',
        'background: #0f172a',
        'color: #f8fafc',
        'border: 1px solid #38bdf8',
        'border-radius: 12px',
        'box-shadow: 0 12px 30px rgba(0,0,0,0.6)',
        'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        'font-size: 13px',
        'padding: 16px',
        'box-sizing: border-box'
    ].join(';');

    // Look for any links on current page
    const foundPageLinks = Array.from(document.querySelectorAll('a[href*="fuckingfast.co/"]'))
        .map(a => a.href)
        .filter((href, idx, self) => self.indexOf(href) === idx && !href.includes('/dl/'));

    overlay.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div style="font-weight:bold; font-size:15px; color:#38bdf8; display:flex; align-items:center; gap:6px;">
                <span>🚀</span> AnyRepack Link Extractor
            </div>
            <button id="ar-close" style="background:transparent; border:none; color:#94a3b8; font-size:16px; cursor:pointer;">✕</button>
        </div>
        <p style="margin:0 0 10px; color:#94a3b8; font-size:12px; line-height:1.4;">
            Extracts Cloudflare-cleared direct CDN links for <b>AnyRepackDownloader</b>.
        </p>
        <textarea id="ar-links-input" placeholder="Paste your FuckingFast share links here (one per line)..." style="
            width: 100%;
            height: 120px;
            background: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 8px;
            font-family: monospace;
            font-size: 11px;
            box-sizing: border-box;
            resize: vertical;
        "></textarea>
        <div style="display:flex; justify-content:space-between; align-items:center; margin: 10px 0;">
            <label style="font-size:12px; color:#cbd5e1;">Concurrency: 
                <select id="ar-concurrency" style="background:#1e293b; color:#fff; border:1px solid #475569; border-radius:4px; padding:2px 6px;">
                    <option value="2">2 threads</option>
                    <option value="3" selected>3 threads</option>
                    <option value="5">5 threads</option>
                </select>
            </label>
            <span id="ar-detected-count" style="font-size:11px; color:#38bdf8;">${foundPageLinks.length > 0 ? foundPageLinks.length + ' links on page' : ''}</span>
        </div>
        <div id="ar-progress-box" style="display:none; margin-bottom:10px;">
            <div id="ar-status-text" style="font-size:12px; margin-bottom:4px; color:#a5f3fc;">Processing...</div>
            <div style="background:#1e293b; border-radius:6px; height:8px; overflow:hidden;">
                <div id="ar-progress-bar" style="background:#10b981; height:100%; width:0%; transition:width 0.2s;"></div>
            </div>
        </div>
        <button id="ar-start-btn" style="
            width: 100%;
            background: #0284c7;
            color: white;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            padding: 9px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        ">⚡ Extract Direct Links</button>
    `;

    document.body.appendChild(overlay);

    const txtInput = document.getElementById('ar-links-input');
    const startBtn = document.getElementById('ar-start-btn');
    const closeBtn = document.getElementById('ar-close');
    const progressBox = document.getElementById('ar-progress-box');
    const progressBar = document.getElementById('ar-progress-bar');
    const statusText = document.getElementById('ar-status-text');

    // Pre-fill if links found on page
    if (foundPageLinks.length > 0) {
        txtInput.value = foundPageLinks.join('\n');
    }

    closeBtn.onclick = () => overlay.remove();

    function fileIdOf(link) {
        try {
            return new URL(link, location.origin).pathname.split('/').filter(Boolean).pop();
        } catch {
            return null;
        }
    }

    function readRedirect(headers) {
        return headers.get('hx-redirect') || headers.get('HX-Redirect')
            || headers.get('hx-location') || headers.get('location');
    }

    async function resolveSingle(link, id) {
        // Strategy 1: Relative HTMX POST to /f/{id}/go
        try {
            const res = await fetch(`/f/${id}/go`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'HX-Request': 'true',
                    'HX-Current-URL': location.href,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: '',
            });
            if (res.ok) {
                const direct = readRedirect(res.headers);
                if (direct) {
                    try { return new URL(direct, location.origin).href; } catch { return direct; }
                }
            }
        } catch {}

        // Strategy 2: GET landing page and match dl.fuckingfast.co URL
        try {
            const pageRes = await fetch(`/${id}`, { credentials: 'include' });
            if (pageRes.ok) {
                const html = await pageRes.text();
                const m = html.match(/https?:\/\/dl\.fuckingfast\.co[^\s"'>]+/i);
                if (m) return m[0];
            }
        } catch {}

        return null;
    }

    startBtn.onclick = async () => {
        const rawLines = txtInput.value.split('\n').map(l => l.strip ? l.strip() : l.trim()).filter(Boolean);
        if (rawLines.length === 0) {
            alert('Please paste at least one FuckingFast share link!');
            return;
        }

        if (!location.hostname.includes('fuckingfast')) {
            const proceed = confirm('Notice: For best results, this script should run on https://fuckingfast.co so Cloudflare cookies are present.\n\nDo you want to continue anyway?');
            if (!proceed) return;
        }

        const concurrency = parseInt(document.getElementById('ar-concurrency').value) || 3;
        startBtn.disabled = true;
        startBtn.style.opacity = '0.5';
        progressBox.style.display = 'block';

        const results = new Array(rawLines.length);
        let completed = 0;
        let cursor = 0;

        async function worker() {
            while (cursor < rawLines.length) {
                const idx = cursor++;
                const link = rawLines[idx];
                const id = fileIdOf(link);

                let direct = null;
                if (id) {
                    direct = await resolveSingle(link, id);
                }

                results[idx] = direct;
                completed++;

                const pct = Math.round((completed / rawLines.length) * 100);
                progressBar.style.width = pct + '%';
                statusText.innerHTML = `[${completed}/${rawLines.length}] ${direct ? '✅ Success' : '❌ Failed'}`;
                console.log(`[${completed}/${rawLines.length}] ${direct ? '✅' : '❌'} ${link} -> ${direct || 'Failed'}`);

                await new Promise(r => setTimeout(r, 600));
            }
        }

        const workers = Array.from({ length: concurrency }, () => worker());
        await Promise.all(workers);

        const validResults = results.filter(Boolean);
        progressBar.style.background = '#38bdf8';
        statusText.innerHTML = `<b>🎉 Done! Extracted ${validResults.length}/${rawLines.length} links.</b>`;

        if (validResults.length > 0) {
            const textContent = validResults.join('\n');

            // Copy to clipboard
            try {
                await navigator.clipboard.writeText(textContent);
                statusText.innerHTML += '<br><small style="color:#67e8f9;">✓ Copied to clipboard!</small>';
            } catch {}

            // Trigger file download
            const blob = new Blob([textContent], { type: 'text/plain' });
            const dlLink = document.createElement('a');
            dlLink.href = URL.createObjectURL(blob);
            dlLink.download = 'direct_links.txt';
            dlLink.click();
            URL.revokeObjectURL(dlLink.href);

            startBtn.textContent = '✓ Saved to direct_links.txt!';
            startBtn.style.background = '#10b981';
        } else {
            alert('Failed to resolve links. Please make sure you are on https://fuckingfast.co and have completed any human verification checks.');
            startBtn.disabled = false;
            startBtn.style.opacity = '1';
        }
    };
})();

