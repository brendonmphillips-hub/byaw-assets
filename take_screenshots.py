import csv
import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = 'https://builtyouawebsite.com'
SITES_CSV = 'sites.csv'
SCROLL_WAIT = 2.0
NAV_TIMEOUT = 30000
DESKTOP_W = 1440
DESKTOP_H = 900
MOBILE_W = 390
MOBILE_H = 844

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
                'code': row['claim_code'].strip(),
                'slug': row['slug'].strip(),
                'name': row['business_name'].strip(),
                'campaign': row['campaign'].strip(),
            })
    return sites

def already_done(campaign, code):
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
    scrolled_by = page.evaluate(SCROLL_PAST_HEADER)
    time.sleep(0.3)
    page.screenshot(path=out_path, full_page=False)
    ctx.close()
    return scrolled_by

def take_screenshots():
    sites = load_sites(SITES_CSV)
    total = len(sites)
    errors = []
    shot = 0
    skipped = 0

    print(f'Loaded {total} sites from {SITES_CSV}')
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for i, site in enumerate(sites):
            code = site['code']
            slug = site['slug']
            name = site['name']
            campaign = site['campaign']
            url = f'{BASE_URL}/{slug}/'
            out_dir = os.path.join('postcards', campaign, code)

            if already_done(campaign, code):
                print(f'[{i+1:02d}/{total}] SKIP {name} ({code})')
                skipped += 1
                continue

            print(f'[{i+1:02d}/{total}] SHOOT {name} ({code})')
            os.makedirs(out_dir, exist_ok=True)

            desktop_path = os.path.join(out_dir, 'desktop.png')
            mobile_path = os.path.join(out_dir, 'mobile.png')

            if not os.path.exists(desktop_path):
                try:
                    scrolled = shoot(browser, url, DESKTOP_W, DESKTOP_H, 1, False, desktop_path)
                    print(f'         desktop OK ({os.path.getsize(desktop_path)//1024}KB, scrolled {scrolled}px)')
                except Exception as e:
                    errors.append((code, slug, 'desktop', str(e)))
                    print(f'         desktop ERROR: {e}')

            if not os.path.exists(mobile_path):
                try:
                    scrolled = shoot(browser, url, MOBILE_W, MOBILE_H, 2, True, mobile_path)
                    print(f'         mobile OK ({os.path.getsize(mobile_path)//1024}KB, scrolled {scrolled}px)')
                except Exception as e:
                    errors.append((code, slug, 'mobile', str(e)))
                    print(f'         mobile ERROR: {e}')

            shot += 1

        browser.close()

    print()
    print(f'Shot: {shot}  Skipped: {skipped}')

    if errors:
        print(f'Errors ({len(errors)}):')
        for code, slug, kind, msg in errors:
            print(f'  [{code}] {slug} / {kind}: {msg}')
        exit(1)

if __name__ == '__main__':
    start = time.time()
    take_screenshots()
    print(f'Total time: {(time.time()-start)/60:.1f} min')
