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
from playwright.sync_api import sync_playwright

BASE_URL    = 'https://builtyouawebsite.com'
SITES_CSV   = 'sites.csv'
SCROLL_WAIT = 2.0
NAV_TIMEOUT = 30000

DESKTOP_W = 1440
DESKTOP_H = 900
MOBILE_W  = 390
MOBILE_H  = 844

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
                'code':     row['claim_code'].strip(),
                'slug':     row['slug'].strip(),
                'name':     row['business_name'].strip(),
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
    sites   = load_sites(SITES_CSV)
    total   =
