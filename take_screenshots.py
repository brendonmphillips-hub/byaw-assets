#!/usr/bin/env python3
"""
BYAW Screenshot Script — Wave 01 (155 businesses)
Takes desktop (1440px) and mobile (390px) screenshots of all live preview URLs.

Output structure:
  postcards/2026-06-wave-01/CLAIMCODE/desktop.png
  postcards/2026-06-wave-01/CLAIMCODE/mobile.png

Usage (local):
  pip install playwright
  python -m playwright install chromium
  python take_screenshots.py

In GitHub Actions: triggered via workflow_dispatch.
"""

import csv
import os
import time
from playwright.sync_api import sync_playwright

# ── CONFIG ───────────────────────────────────────────────────────────────────
BASE_URL    = 'https://preview.builtyouawebsite.com'
CAMPAIGN    = '2026-06-wave-01'
OUT_DIR     = f'postcards/{CAMPAIGN}'
SCROLL_WAIT = 2.0    # seconds after load before screenshot
NAV_TIMEOUT = 45000  # ms

DESKTOP_W = 1440
DESKTOP_H = 900
MOBILE_W  = 390
MOBILE_H  = 844

# ── ALL 155 BUSINESSES: (claim_code, slug) ────────────────────────────────────
SITES = [
    ('27MWDR', 'd-v-electric-inc'),
    ('2A4T4W', 'cals-roofing'),
    ('2RYJFB', 'taiga-woods-tree-care'),
    ('32C4VC', 'panicola-electric'),
    ('36NV9V', 'willis-electric'),
    ('3C5HPE', 'mad-skills-contracting-llc'),
    ('3D4HBJ', 'eagle-garage-door-repair'),
    ('3NDVPP', 'mercawood-electric'),
    ('3RHZV9', 'bear-tree-service'),
    ('3SCPME', 'viewmont-tree-services'),
    ('42ZC4N', 'all-things-gutter'),
    ('4B823Q', 'brandon-kristel-plumbing'),
    ('4CR2JN', 'zachs-garage-door-service'),
    ('4MP2C7', 'moore-bridger-tree-service'),
    ('4UTX7D', 'roofing-solutions'),
    ('54ETK2', 'as-contracting'),
    ('56LYBR', 'bd-contracting'),
    ('5EEJPR', 'jj-electrical-construction'),
    ('5RT9RG', 'franchini-plumbing-heating-llc'),
    ('5U4QFN', 'adk-power-moves-llc'),
    ('5VEJBT', 'northern-heating-and-air'),
    ('5W654N', 'greene-garage-doors-inc'),
    ('5XXC2C', 'dz-garage-doors-llc'),
    ('656PPN', 'minimally-invasive-tree-removal'),
    ('67WV8W', 'all-phase-electrical'),
    ('68PL9Q', 'r-kiniry-heating-plumbing'),
    ('69R5S7', 'chamberlaine-tree-service'),
    ('6AZTRG', 'doxsee-roofing-inc'),
    ('6G7GDA', 'sand-lake-septic'),
    ('6JMNQ7', 'huntsmans-tree-works-llc'),
    ('6M5LFY', 'adirondack-landworx'),
    ('6SB3AV', 'paramount-construction-and-seamless-gutters'),
    ('78G8GG', 'main-ma-garage-door-repair'),
    ('7E32DU', 'gary-mecabe-plumbing-heating'),
    ('7LP2PX', 'patpro-construction'),
    ('7MCAFY', 'dj-hvac-electrical-plumbing'),
    ('7VF6HG', 'capital-overhead-doors'),
    ('7Y7CLC', 'alpha-tree-service'),
    ('88WMGC', 'resolute-builders'),
    ('89SYTQ', 'power-rooter'),
    ('8RPLP7', 'united-exterior-cleaning'),
    ('8SDZR9', 'k-l-electric'),
    ('8UQDVP', 'er-tree-service'),
    ('998J4V', 'cosselman-septic-pumping'),
    ('99ED7F', 'arts-garage-doors'),
    ('99K7BK', 'moore-fire-extinguisher'),
    ('9XZGXQ', 'the-plumbing-god'),
    ('A4MEFY', 'priority-sewer-drain'),
    ('A79GKK', 'jfb-roofing'),
    ('AUCGHA', 'troy-overhead-door-llc'),
    ('BGAAL3', 'glens-falls-heating-air-conditioning'),
    ('BNT2MT', 'lindsay-mechanical'),
    ('BU5QLC', 'tru-temp-heating-cooling'),
    ('BU8LAX', 'constable-tree-service'),
    ('BVF9BF', 'the-honey-do-list-man-llc'),
    ('BYRBJD', 'safeway-tree-care'),
    ('BZ8RBV', '518-handyman'),
    ('C9Z4EM', 'adirondack-homewerks'),
    ('CFSCDB', 'capital-air'),
    ('CH3URV', 'd-c-bucket-tree-services'),
    ('CR7WUU', 'pete-the-plumber-sewer-drain'),
    ('CWYDZP', 'r-d-tree-services'),
    ('CYGVZM', 'jim-halwick-seamless-gutters'),
    ('CYSCBB', 'garage-door-repair-of-midtown-east-inc'),
    ('D9ABZP', '518-plumbing-well-repair'),
    ('E5AXSX', 'aaron-goodspeed-soc-contracting'),
    ('EALZ9Z', 'adk-tree-services-and-excavation'),
    ('EARZC6', 'central-auto-detailing'),
    ('EBFQ8S', 'master-heating-ac-co'),
    ('EJE4DS', 'fordyce-plumbing-co-llc'),
    ('EQ4VR4', 'mr-ts-total-home-care'),
    ('EQBSGM', 'cpe-tree-service'),
    ('EY8J5Y', 'ace-constructors'),
    ('FFEYFM', 'girard-plumbing-heating'),
    ('FK8J3W', 'randy-cuthbert-plumbing'),
    ('FVF6QZ', 'mighty-clean'),
    ('G4KKBT', 'batavia-garage-door-inc'),
    ('GAEFPQ', 'bassett-heating-cooling'),
    ('GEWZW2', 'crew-garage-door-repair'),
    ('GH82VD', 'chris-walker-heating-and-cooling'),
    ('GHVQDE', 'prodor-inc'),
    ('GKCUXY', 'frank-adams-heating-cooling-plumbing'),
    ('GS56UE', 'countryside-overhead-doors'),
    ('GSH8KX', 'georges-electric-plumbing'),
    ('GW6BEJ', 'austerlitz-plumbing-heating'),
    ('GZVLGR', 'apex-plumbing-heating'),
    ('HKVMG9', 'houghtaling-electrical'),
    ('HQA7TU', 'craig-kurkela-arborist-inc'),
    ('HZFZ8T', 'd-b-roofing'),
    ('J63SUZ', 'tj-hvac-service-install'),
    ('KUAEFL', 'catamount-tree-service'),
    ('LPLMWJ', 'country-comfort-heating'),
    ('LUDNGC', 'standard-electrical-contracting'),
    ('M8QRVR', 'lawless-tree-service'),
    ('MKVWZR', 'done-right-roofing-inc'),
    ('ML7FEJ', 'hathaway-electric-inc'),
    ('MZ6KZ6', 'bradleys-septic'),
    ('NAGS54', 'conditioned-air-products'),
    ('NTQCVM', 'stash-n-dah-boyz-tree-service'),
    ('P6SMBS', 'consolidated-metal-roofing'),
    ('P9RNJB', 'lubrano-tree-care'),
    ('PJSK6M', 'vaillancourt-tree-landscape'),
    ('PTQU7W', 'affordable-tree-services'),
    ('PU5TGH', 'th-electrical-upgrades'),
    ('PZQ7UF', 'dmc-handyman-services'),
    ('Q6EUFD', 'lighthouse-electric-of-glens-falls'),
    ('Q96X8P', 'greenough-construction-co-llc'),
    ('QMSRVC', 'albany-saratoga-doors'),
    ('QN576D', 'kingston-heating-air-conditioning-contractor'),
    ('QVSY9C', 'miller-overhead-door'),
    ('QZDBN7', 'motivated-auto-detailing'),
    ('R32UN9', 'john-b-hull-inc'),
    ('RBBWLA', 'valley-tree-pros-and-excavation'),
    ('RLEX4Y', 'jb-sparkling-cleaning'),
    ('RM4NKF', 'door-doctor-inc'),
    ('RQKDM6', 'northeast-stump-grinding'),
    ('RR7DEP', 'air-conditioning-plumbing-heating'),
    ('RWH89Y', 'bold-heating-air-conditioning'),
    ('S7DVV6', 'a-simmons-electrical-services'),
    ('SHBVU4', 'starratt-plumbing-heating'),
    ('SHXJHW', 'shokan-electric'),
    ('T6EHJY', 'capital-district-seamless-gutters'),
    ('TJRXL6', 'einzig-electric-inc'),
    ('TJVLH3', 'roy-plumbing-heating'),
    ('U229GT', 'joseph-lapi-paving'),
    ('U86DLY', 'troys-tree-services'),
    ('U8BUQT', 'amsterdam-heating-ac'),
    ('UEP88S', 'hoffman-miller-heating'),
    ('UV4SHX', 'albert-adamkoski-roofing'),
    ('UWBSN2', 'campito-plumbing-heating-inc'),
    ('UZSWG3', 'pro-cleaning-services'),
    ('V62TVS', 'pittsfield-heating-air-conditioning'),
    ('V7HH9Z', 'ad-plumbing-and-heating-solutions'),
    ('V9LMZP', 'ram-electrical-services'),
    ('VEVNUK', 'albany-roofing-services'),
    ('VGY5SQ', 'linzey-plumbing-heating'),
    ('WGUGES', 'agape-home-improvement-inc'),
    ('WH9LNT', 'northville-septic-services'),
    ('WNRZXM', 'dt-sons-overhead-doors'),
    ('WTBU8D', 'prestige-sealcoating'),
    ('X6YQUX', 'kelly-plumbing-heating'),
    ('X8TQEV', 'franklin-family-plumbing'),
    ('X8WDYD', 'bens-tree-service-llc'),
    ('XKYFBL', 'thermaltech-heating-and-cooling'),
    ('XXYZ5N', 'upstate-plumbing-heating-cooling'),
    ('YA4YR6', 'design-contracting'),
    ('YD6NDB', 'hainiel-cleaning-service'),
    ('YGFHPW', 'colonial-overhead-doors-llc'),
    ('YGXYAN', 'lawlor-tree-service'),
    ('YRJHWA', 'bob-wheeler-seamless-gutters'),
    ('YS98U7', 'ck-electric'),
    ('YT8RY3', 'bill-elliott-tree-service'),
    ('YU3BMY', 'webster-electric-llc'),
    ('YXCDRH', 'garage-doors-repair-technologies-inc'),
    ('ZKDURV', 'just-service'),
]

# ── SCREENSHOT HELPER ────────────────────────────────────────────────────────
def shoot(browser, url, width, height, is_mobile, out_path):
    ctx = browser.new_context(
        viewport={'width': width, 'height': height},
        device_scale_factor=2 if is_mobile else 1,
        is_mobile=is_mobile,
        has_touch=is_mobile,
    )
    page = ctx.new_page()
    try:
        page.goto(url, wait_until='networkidle', timeout=NAV_TIMEOUT)
        # Scroll past the BYAW claim header so hero is first visible element
        try:
            header = page.query_selector('section.claim')
            if header:
                h = header.bounding_box()
                if h:
                    page.evaluate(f"window.scrollTo(0, {int(h['height'])})")
                    time.sleep(0.3)
        except Exception:
            pass
        time.sleep(SCROLL_WAIT)
        page.screenshot(path=out_path, full_page=False)
    finally:
        ctx.close()


# ── MAIN ─────────────────────────────────────────────────────────────────────
def take_screenshots():
    shot = 0
    skipped = 0
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for code, slug in SITES:
            url          = f'{BASE_URL}/{slug}/'
            folder       = os.path.join(OUT_DIR, code)
            desktop_path = os.path.join(folder, 'desktop.png')
            mobile_path  = os.path.join(folder, 'mobile.png')

            has_desktop = os.path.exists(desktop_path)
            has_mobile  = os.path.exists(mobile_path)

            if has_desktop and has_mobile:
                skipped += 1
                print(f'  – {code} / {slug} (both exist, skipping)')
                continue

            os.makedirs(folder, exist_ok=True)
            print(f'  → {code} / {slug}')

            if not has_desktop:
                try:
                    shoot(browser, url, DESKTOP_W, DESKTOP_H, False, desktop_path)
                    print(f'       ✓ desktop ({os.path.getsize(desktop_path)//1024}KB)')
                except Exception as e:
                    errors.append((code, slug, 'desktop', str(e)))
                    print(f'       ✗ desktop ERROR: {e}')

            if not has_mobile:
                try:
                    shoot(browser, url, MOBILE_W, MOBILE_H, True, mobile_path)
                    print(f'       ✓ mobile  ({os.path.getsize(mobile_path)//1024}KB)')
                except Exception as e:
                    errors.append((code, slug, 'mobile', str(e)))
                    print(f'       ✗ mobile  ERROR: {e}')

            shot += 1

        browser.close()

    print()
    print('─' * 60)
    print(f'Shot:    {shot}')
    print(f'Skipped: {skipped}')
    if errors:
        print(f'Errors:  {len(errors)}')
        for code, slug, kind, msg in errors:
            print(f'  [{code}] {slug}/{kind}: {msg}')
    else:
        print('No errors.')


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    start = time.time()
    take_screenshots()
    elapsed = time.time() - start
    print(f'\nTotal time: {elapsed/60:.1f} min')
