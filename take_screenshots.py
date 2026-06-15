#!/usr/bin/env python3
"""
BYAW Screenshot Script
Reads sites.csv, takes desktop + mobile screenshots of each preview URL.
Scrolls past the BYAW claim header before capturing so the hero is the
first thing visible — cleaner for postcard mockups.
Skips any business that already has both desktop.png and mobile.png.

To add a new business: add a row to sites.csv. That's it.

Output structure (matches asset server path):
  postcards/{campaign}/{claim_code}/desktop.png
  postcards/{campaign}/{claim_code}/mobile.png
"""

import csv
import os
import time
import zipfile
from playwright.sync_api import sync_playwright

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_URL    = 'https://builtyouawebsite.com'
SITES_CSV   = 'sites.csv'
SCROLL_WAIT = 2.0    # seconds after networkidle before screenshot
NAV_TIMEOUT = 30000  # ms

DESKTOP_W = 1440
DESKTOP_H = 900
MOBILE_W  = 390
MOBILE_H  = 844

# JS to measure and scroll past the BYAW claim header
# Falls back to 0 if the element isn't found
SCROLL_PAST_HEADER = """
() => {
    const selectors = ['section.claim', '.claim', '[aria-label="Built You A Website preview information"]'];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.offsetHeight > 0) {
            window.scrollTo(0, el.offsetHeight);
            return el.offsetHeight;
        }
    }
    // Fallback: scroll a fixed amount if we can't find the header
    window.scrollTo(0, 180);
    return 180;
}
"""


def load_sites(csv_path):
    sites = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sites.append({
                'code':     row['claim_code'].strip(),
                'slug':     row['slug'].strip(),
                'name':     row['business_name'].strip(),
                'campaign': row['campaign'].strip(),
            })
    return sites


def already_done(campaign, code):
    """Return True if both desktop.png and mobile.png already exist."""
    base = os.path.join('postcards', campaign, code)
    return (
        os.path.exists(os.path.join(base, 'desktop.png')) and
        os.path.exists(os.path.join(base, 'mobile.png'))
    )


def shoot(browser, url, viewport_w, viewport_h, scale, is_mobile, out_path):
    ctx = browser.new_context(
        viewport={'width': viewport_w, 'height': viewport_h},
        device_scale_factor=scale,
        is_mobile=is_mobile,
        has_touch=is_mobile,
    )
    page = ctx.new_page()
    page.goto(url, wait_until='networkidle', timeout=NAV_TIMEOUT)
    time.sleep(SCROLL_WAIT)

    # Scroll past the BYAW claim header
    scrolled_by = page.evaluate(SCROLL_PAST_HEADER)
    time.sleep(0.3)  # brief settle after scroll

    # Screenshot the current viewport (not full page) — hero is now at top
    page.screenshot(path=out_path, full_page=False)
    ctx.close()
    return scrolled_by


def take_screenshots():
    sites   = load_sites(SITES_CSV)
    total   = len(sites)
    errors  = []
    shot    = 0
    skipped = 0

    print(f'Loaded {total} sites from {SITES_CSV}')
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for i, site in enumerate(sites):
            code     = site['code']
            slug     = site['slug']
            name     = site['name']
            campaign = site['campaign']
            url      = f'{BASE_URL}/{slug}/'
            out_dir  = os.path.join('postcards', campaign, code)

            # ── SKIP CHECK ───────────────────────────────────────────────────
            if already_done(campaign, code):
                print(f'[{i+1:02d}/{total}] SKIP  {name} ({code})')
                skipped += 1
                continue

            print(f'[{i+1:02d}/{total}] SHOOT {name} ({code})')
            os.makedirs(out_dir, exist_ok=True)

            desktop_path = os.path.join(out_dir, 'desktop.png')
            mobile_path  = os.path.join(out_dir, 'mobile.png')

            # ── DESKTOP ──────────────────────────────────────────────────────
            if not os.path.exists(desktop_path):
                try:
                    scrolled = shoot(browser, url, DESKTOP_W, DESKTOP_H, 1, False, desktop_path)
                    print(f'         ✓ desktop ({os.path.getsize(desktop_path)//1024}KB, scrolled {scrolled}px past header)')
                except Exception as e:
                    errors.append((code, slug, 'desktop', str(e)))
                    print(f'         ✗ desktop ERROR: {e}')
            else:
                print(f'         – desktop exists, skipping')

            # ── MOBILE ───────────────────────────────────────────────────────
            if not os.path.exists(mobile_path):
                try:
                    scrolled = shoot(browser, url, MOBILE_W, MOBILE_H, 2, True, mobile_path)
                    print(f'         ✓ mobile  ({os.path.getsize(mobile_path)//1024}KB, scrolled {scrolled}px past header)')
                except Exception as e:
                    errors.append((code, slug, 'mobile', str(e)))
                    print(f'         ✗ mobile  ERROR: {e}')
            else:
                print(f'         – mobile exists, skipping')

            shot += 1

        browser.close()

    # ── SUMMARY ──────────────────────────────────────────────────────────────
    print()
    print('─' * 60)
    print(f'Shot:    {shot} sites')
    print(f'Skipped: {skipped} sites (already had both screenshots)')

    if errors:
        print(f'\nErrors ({len(errors)}):')
        for code, slug, kind, msg in errors:
            print(f'  [{code}] {slug} / {kind}: {msg}')
        exit(1)
    else:
        print('No errors.')


if __name__ == '__main__':
    start = time.time()
    take_screenshots()
    elapsed = time.time() - start
    print(f'\nTotal time: {elapsed/60:.1f} min')
