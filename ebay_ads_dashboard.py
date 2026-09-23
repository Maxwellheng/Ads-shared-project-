import streamlit as st
import requests
import re
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd
from io import BytesIO

plt.rcParams['axes.unicode_minus'] = False

def _setup_cjk_font():
    """Download and register a CJK font for Linux/cloud environments."""
    import os
    from matplotlib import font_manager
    font_path = '/tmp/NotoSansSC-Regular.otf'
    if not os.path.exists(font_path):
        try:
            _r = requests.get(
                'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansSC-Regular.otf',
                timeout=20)
            if _r.status_code == 200:
                with open(font_path, 'wb') as _f:
                    _f.write(_r.content)
        except Exception:
            pass
    if os.path.exists(font_path):
        font_manager.fontManager.addfont(font_path)
        plt.rcParams['font.family'] = ['Noto Sans SC', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    else:
        plt.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']

_setup_cjk_font()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}


def _ebay_get(url: str, timeout: int = 15):
    """Route www.ebay.com page requests through ScraperAPI when key is available."""
    try:
        key = st.secrets.get("SCRAPER_API_KEY", "")
    except Exception:
        key = ""
    if key:
        proxy = (f"http://api.scraperapi.com"
                 f"?api_key={key}&url={requests.utils.quote(url, safe='')}")
        return requests.get(proxy, timeout=timeout + 15)
    return requests.get(url, headers=HEADERS, timeout=timeout)


CATEGORY_KEYWORDS = {
    # Parts & Accessories
    'Auto Parts & Accessories': [
        'car', 'auto', 'truck', 'motor', 'engine', 'engines', 'vehicle', 'automotive',
        'oem', 'bumper', 'headlight', 'brake', 'brakes', 'suspension', 'exhaust', 'obd',
        'oil', 'fuel', 'filter', 'steering', 'gear', 'gearbox', 'transmission', 'differential',
        'radiator', 'gasket', 'alternator', 'starter', 'coolant', 'thermostat', 'wiper',
        'throttle', 'caliper', 'rotor', 'strut', 'axle', 'intake', 'timing', 'spark',
        'valve', 'piston', 'cylinder', 'manifold', 'sensor', 'diesel', 'carburetor',
        'muffler', 'catalytic', 'horsepower', 'rpm',
        'chevrolet', 'chevy', 'ford', 'dodge', 'toyota', 'honda', 'jeep', 'subaru',
        'bmw', 'mercedes', 'audi', 'nissan', 'hyundai', 'kia', 'ram', 'gmc',
    ],
    'Cycling Parts & Accessories': ['shimano', 'sram', 'derailleur', 'handlebar', 'saddle', 'cassette',
                                     'chainring', 'pedal', 'fork', 'stem', 'crankset'],
    'Electric Bikes': ['electric bike', 'ebike', 'e-bike', 'electric bicycle', 'electric scooter'],
    # Home & Garden
    'Home & Garden': ['furniture', 'chair', 'table', 'lamp', 'decor', 'sofa', 'rug', 'curtain',
                       'garden', 'outdoor', 'patio', 'pillow', 'bedding', 'mattress', 'shelf'],
    'Plants & Succulents': ['succulent', 'cactus', 'aloe', 'echeveria', 'haworthia', 'sedum',
                             'lithops', 'plant', 'live plant', 'bonsai', 'orchid'],
    # Electronics
    'Electronics': ['phone', 'laptop', 'tablet', 'camera', 'computer', 'monitor', 'keyboard',
                     'gpu', 'cpu', 'motherboard', 'iphone', 'samsung', 'apple', 'gaming', 'console', 'ps5', 'xbox'],
    # Business & Industrial
    'Business & Industrial': ['industrial', 'commercial', 'machinery', 'equipment', 'cnc',
                               'pneumatic', 'hydraulic', 'forklift', 'compressor', 'generator', 'welder'],
    # Lifestyle — Sports
    'Sports & Outdoors': ['fitness', 'gym', 'treadmill', 'dumbbell', 'yoga', 'running', 'weight',
                           'hiking', 'camping', 'fishing', 'hunting', 'ski', 'golf'],
    # Lifestyle — Health & Beauty
    'Health & Beauty': ['skincare', 'makeup', 'perfume', 'vitamin', 'supplement', 'hair',
                         'serum', 'moisturizer', 'shampoo', 'nail'],
    # Lifestyle — Toys & Hobbies
    'Toys & Hobbies': ['toy', 'lego', 'diecast', 'model kit', 'hobby', 'puzzle', 'board game',
                        'action figure', 'funko', 'barbie'],
    # Fashion
    'Clothing & Shoes': ['shirt', 'dress', 'pants', 'jacket', 'shoes', 'hoodie', 'sneaker',
                          'jeans', 'coat', 'boots', 'sandal', 'nike', 'adidas'],
    'Jewelry & Watches': ['ring', 'necklace', 'bracelet', 'earring', 'gold', 'silver', 'diamond',
                           'watch', 'rolex', 'cartier', 'pendant', 'gemstone'],
    # Collectibles
    'Trading Cards': ['card', 'pokemon', 'psa', 'bgs', 'cgc', 'graded', 'tcg', 'mtg', 'yugioh',
                       'rookie', 'holo', 'booster', 'sealed', 'sports card', 'charizard', 'refractor'],
    'Coins & Paper Money': ['coin', 'silver dollar', 'gold coin', 'bullion', 'numismatic',
                             'pcgs', 'ngc', 'proof', 'mint', 'currency', 'banknote'],
    'Comics & Memorabilia': ['comic', 'marvel', 'dc comics', 'autograph', 'signed', 'memorabilia',
                              'vintage', 'antique', 'stamp', 'collectible'],
    # Musical Instruments
    'Musical Instruments': ['guitar', 'bass', 'piano', 'keyboard', 'drum', 'violin', 'fender',
                             'gibson', 'marshall', 'amp', 'amplifier', 'saxophone'],
    # Books & Media
    'Books & Media': ['book', 'dvd', 'blu-ray', 'vinyl', 'record', 'magazine', 'novel', 'textbook'],
}

COMPETITOR_MAP = {
    'Electric Bikes': {
        'single': ['Rad Power Bikes', 'Aventon', 'Lectric', 'Himiway', 'Velotric', 'Juiced'],
        'multi': [('Trek', 'electric bike'), ('Yamaha', 'electric bike'), ('Specialized', 'electric bike')],
    },
    'Succulents & Cacti': {
        'single': ['Leaf & Clay', 'Mountain Crest Gardens', 'Succulents Box', 'Planet Desert'],
        'multi': [],
    },
}

QUADRANT_INFO = {
    '右上': {
        'label': '高ASP + 垂直',
        'strategy': 'PLP手动 + PLP自动 + OA',
        'reason': '高利润支撑CPC，垂直品类关键词集中；手动词精准控ACOS，自动词补长尾，OA引外站高价流量',
    },
    '左上': {
        'label': '高ASP + 铺货',
        'strategy': 'PLG + PLP自动(高价品) + OA',
        'reason': 'SKU多品类杂，手动关键词维护成本极高；PLG全覆盖+Smart Targeting托管高价品，OA整店推广',
    },
    '右下': {
        'label': '低ASP + 垂直',
        'strategy': 'PLG → PLP手动(爆款) + PLP自动',
        'reason': '低单价CPC风险高；先用PLG测爆款，有出单记录后对爆款单独开手动词，Smart Targeting补量',
    },
    '左下': {
        'label': '低ASP + 铺货',
        'strategy': 'PLG + OA',
        'reason': 'CPC几乎无利润空间；PLG按出单付费控风险，OA整店维度推广补充站外曝光',
    },
}

# eBay brand colors: Blue #0064D2 / Green #86B817 / Yellow #F5AF02 / Red #E53238
_EBAY_BLUE   = '#0064D2'
_EBAY_GREEN  = '#86B817'
_EBAY_YELLOW = '#F5AF02'
_EBAY_RED    = '#E53238'

# Quadrant → eBay accent color
QUADRANT_COLOR = {
    '右上': _EBAY_BLUE,
    '左上': _EBAY_GREEN,
    '右下': _EBAY_YELLOW,
    '左下': _EBAY_RED,
}

# (name, pct, hex_color, description_zh)
QUADRANT_ALLOCATION = {
    '右上': [
        ('PLP手动', 50, _EBAY_GREEN,  '精准关键词控ACOS，高利润品类主力'),
        ('PLP自动', 30, _EBAY_YELLOW, 'Smart Targeting补长尾流量'),
        ('PLG',    10, _EBAY_BLUE,   'CPS全量兜底覆盖'),
        ('OA',     10, _EBAY_RED,    '引外站高价值买家'),
    ],
    '左上': [
        ('PLG',    50, _EBAY_BLUE,   'CPS全量覆盖，多品类SKU必选'),
        ('PLP自动', 30, _EBAY_YELLOW, '高价品Smart Targeting精准抢量'),
        ('OA',     20, _EBAY_RED,    '整店站外推广'),
    ],
    '右下': [
        ('PLG',    60, _EBAY_BLUE,   'CPS测爆款，低单价低风险起步'),
        ('PLP手动', 25, _EBAY_GREEN,  '有出单记录的爆款开手动词'),
        ('PLP自动', 15, _EBAY_YELLOW, 'Smart Targeting补量'),
    ],
    '左下': [
        ('PLG',    80, _EBAY_BLUE,  'CPS按出单付费，铺货首选'),
        ('OA',     20, _EBAY_RED,   '整店维度站外曝光'),
    ],
}

SEED_MAP = {
    'Electric Bikes': ['electric bike', 'ebike', 'electric bicycle', 'fat tire electric bike', 'electric mountain bike'],
    'Succulents & Cacti': ['succulent plant', 'live succulent', 'cactus plant', 'rare succulent', 'indoor succulent'],
    'Auto Parts': ['auto parts', 'car accessories', 'truck parts'],
    'Electronics': ['electronics', 'gadgets'],
    'Clothing': ['clothing', 'fashion'],
    'Jewelry': ['jewelry', 'accessories'],
    'Home & Garden': ['home decor', 'furniture'],
    'Sports & Fitness': ['fitness equipment', 'sports gear'],
    'Trading Cards': ['tcg booster box', 'trading card hobby box', 'pokemon booster box', 'sports card graded', 'card sealed case'],
}


# ── Scraping ──────────────────────────────────────────────────────────────────

def extract_seller_id(raw_input: str) -> str:
    """Normalize seller input: handle full URLs or plain usernames."""
    raw = raw_input.strip().rstrip('/')
    for prefix in ['https://www.ebay.com/str/', 'https://www.ebay.com/usr/',
                   'ebay.com/str/', 'ebay.com/usr/']:
        if prefix in raw:
            return raw.split(prefix)[-1].split('/')[0].split('?')[0]
    return raw.split('/')[-1]


def fetch_pages_for_sid(sid: str, sold_filter: str) -> list[str]:
    """Fetch up to 3 pages for a given seller ID and filter."""
    pages = []
    for page in range(1, 4):
        url = (f"https://www.ebay.com/sch/i.html"
               f"?_ssn={sid}&_pgn={page}&_ipg=120&_stpos=10001{sold_filter}")
        try:
            r = _ebay_get(url, timeout=15)
            pages.append(r.text)
            time.sleep(0.3)
        except:
            pass
    return pages


def fetch_listings_html(seller_id: str) -> tuple[list[str], str]:
    """Fetch both sold and current listings, combine for richer data."""
    candidates = [seller_id, seller_id.replace('-', ''), seller_id.replace('_', '')]
    candidates = list(dict.fromkeys(candidates))

    # Find the working seller ID first (try sold listings as probe)
    working_sid = None
    for sid in candidates:
        url = f"https://www.ebay.com/sch/i.html?_ssn={sid}&_pgn=1&_ipg=60&_stpos=10001"
        try:
            r = _ebay_get(url, timeout=15)
            # Accept if page has any prices OR any listing links (handles low-volume sellers)
            raw = re.findall(r'\$([0-9][0-9,]*\.?[0-9]*)', r.text)
            prices = [float(p.replace(',', '')) for p in raw if 0.99 < float(p.replace(',', '')) < 50000]
            has_listings = bool(re.search(r'/itm/\d+', r.text))
            if len(prices) >= 1 or has_listings:
                working_sid = sid
                break
        except:
            pass
        time.sleep(0.3)

    if not working_sid:
        return [], '无数据'

    # Fetch both sold and current in parallel via sequential calls
    all_pages = []
    sold_pages = fetch_pages_for_sid(working_sid, '&LH_Complete=1&LH_Sold=1')
    current_pages = fetch_pages_for_sid(working_sid, '')
    all_pages = sold_pages + current_pages

    return all_pages, '已售出 + 当前在售'


def parse_prices(html: str) -> list[float]:
    """Extract listing prices, filtering out UI slider/repeated values."""
    raw = re.findall(r'\$([0-9][0-9,]*\.?[0-9]*)', html)
    all_vals = []
    for p in raw:
        try:
            v = float(p.replace(',', ''))
            if 0.99 < v < 50000:
                all_vals.append(v)
        except:
            pass
    # Filter values that appear 4+ times on a single page (UI elements like sliders)
    from collections import Counter
    freq = Counter(all_vals)
    return [v for v in all_vals if freq[v] < 4]


TITLE_NOISE = {'your listing', 'oops', 'something went wrong', 'reach more buyers',
               'your new destination', 'shopping destination', 'free shipping',
               'shop by category', 'filter by category', 'sign in', 'register',
               'find your next', 'daily deals', 'brand outlet'}


def extract_titles(html: str) -> list[str]:
    import html as _html_mod
    raw = []
    # JSON "title" fields (store pages)
    raw += re.findall(r'"title"\s*:\s*"([^"]{15,200})"', html)
    # img alt attributes (search results pages — actual listing titles)
    raw += re.findall(r'<img[^>]+alt="([^"]{15,250})"', html)

    seen = set()
    titles = []
    for t in raw:
        t = _html_mod.unescape(t)
        t_clean = re.sub(r'[^\x00-\x7F]', '', t).strip().lower()
        if t_clean in seen:
            continue
        if any(noise in t_clean for noise in TITLE_NOISE):
            continue
        if 'ebay' in t_clean and len(t_clean) < 50:
            continue
        if len(t_clean.split()) < 3:
            continue
        seen.add(t_clean)
        titles.append(t_clean)
    return titles


def extract_product_images(html: str, n: int = 2) -> list[str]:
    """Extract distinct product thumbnail URLs from a search results page.
    Since we always call this on the seller search page (not store page),
    all /images/g/ URLs found are listing thumbnails."""
    seen_base, urls = set(), []
    for m in re.finditer(r'https://i\.ebayimg\.com/images/g/([^/]+)/s-l\d+\.(?:jpg|webp|png)', html):
        img_hash = m.group(1)
        if img_hash not in seen_base:
            seen_base.add(img_hash)
            urls.append(f'https://i.ebayimg.com/images/g/{img_hash}/s-l300.jpg')
        if len(urls) >= n:
            return urls
    return urls


def fetch_product_images_from_search(seller_id: str, n: int = 2) -> list[str]:
    """Fetch product thumbnails from seller's search results (not store page)."""
    for sid in [seller_id, seller_id.replace('_', '')]:
        try:
            r = _ebay_get(
                f"https://www.ebay.com/sch/i.html?_ssn={sid}&_pgn=1&_ipg=10",
                timeout=10)
            imgs = extract_product_images(r.text, n)
            if imgs:
                return imgs
        except:
            pass
    return []


def fetch_store_titles(seller_id: str) -> tuple[list[str], list[str]]:
    """Fetch /str/ store page — returns (titles, image_urls)."""
    for sid in [seller_id, seller_id.replace('-', ''), seller_id.replace('_', '')]:
        try:
            r = _ebay_get(f"https://www.ebay.com/str/{sid}", timeout=15)
            titles = extract_titles(r.text)
            imgs = extract_product_images(r.text)
            if len(titles) >= 3:
                return titles, imgs
        except:
            pass
        time.sleep(0.3)
    return [], []


def fetch_total_listing_count(seller_id: str) -> str:
    """Fetch real total listing count from eBay search page."""
    try:
        r = _ebay_get(
            f"https://www.ebay.com/sch/i.html?_ssn={seller_id}&_pgn=1&_ipg=1",
            timeout=10)
        m = re.search(r'([\d,]+\+?)\s*results?', r.text, re.I)
        if m:
            return m.group(1)
    except:
        pass
    return ''


def scrape_store(raw_input: str) -> dict:
    seller_id = extract_seller_id(raw_input)
    all_prices = []
    all_titles = []

    pages, data_source = fetch_listings_html(seller_id)
    for html in pages:
        all_prices += parse_prices(html)
        all_titles += extract_titles(html)

    # Store page has more reliable product titles for category detection
    store_titles, _ = fetch_store_titles(seller_id)
    all_titles += store_titles
    # Product thumbnails come from search results (not store page which shows avatar/banner)
    image_urls = fetch_product_images_from_search(seller_id)

    # Fetch real total from search page (try clean ID if underscore version gives nothing)
    total_count_str = fetch_total_listing_count(seller_id)
    if not total_count_str and '_' in seller_id:
        total_count_str = fetch_total_listing_count(seller_id.replace('_', ''))

    category = infer_category(all_titles)
    vertical_score = compute_vertical_score(all_titles, category)

    return {
        'seller_id': seller_id,
        'prices': sorted(all_prices),
        'asp_median': float(np.median(all_prices)) if all_prices else 0,
        'listing_count': len(all_prices),
        'total_listing_count': total_count_str,
        'category': category,
        'vertical_score': vertical_score,
        'data_source': data_source,
        'titles': all_titles,
        'image_urls': image_urls,
    }


def infer_category(titles: list) -> str:
    text = ' '.join(titles).lower()
    def count_whole_word(t, kw):
        return len(re.findall(r'\b' + re.escape(kw) + r'\b', t))
    scores = {cat: sum(count_whole_word(text, k) for k in kws) for cat, kws in CATEGORY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'General'


STOP_WORDS = {
    'the', 'a', 'an', 'for', 'with', 'to', 'of', 'in', 'and', 'or', 'by',
    'new', 'used', 'lot', 'set', 'pack', 'bundle', 'piece', 'pc', 'pcs',
    'item', 'free', 'fast', 'ship', 'shipping', 'sale', 'buy', 'get',
    'best', 'great', 'good', 'nice', 'top', 'hot', 'rare', 'vintage',
    'original', 'official', 'authentic', 'genuine', 'oem', 'quality',
    'size', 'color', 'black', 'white', 'red', 'blue', 'green', 'silver',
    'gold', 'us', 'usa', 'seller', 'ebay', '1', '2', '3', '4', '5',
}

def compute_vertical_score(titles: list, category: str) -> float:
    """
    Dual-signal vertical score — takes the max of two complementary signals:
      A) Word concentration: high word overlap across titles (brand-type vertical)
      B) Category keyword coverage: % of titles containing category keywords (category-type vertical)
    No per-seller tuning needed; both signals are adaptive.
    """
    if not titles or len(titles) < 3:
        return 5.0

    from collections import Counter

    title_word_sets = []
    for t in titles:
        words = {w for w in re.sub(r'[^a-z0-9 ]', ' ', t.lower()).split()
                 if len(w) >= 3 and w not in STOP_WORDS}
        if words:
            title_word_sets.append(words)

    if not title_word_sets:
        return 5.0

    n = len(title_word_sets)

    # ── Signal A: top-3 word concentration (brand vertical) ──
    word_doc_freq: Counter = Counter()
    for ws in title_word_sets:
        for w in ws:
            word_doc_freq[w] += 1
    top3_freqs = [freq for _, freq in word_doc_freq.most_common(3)]
    avg_top3 = sum(top3_freqs) / len(top3_freqs) if top3_freqs else 0
    concentration = avg_top3 / n
    score_a = 1 + 9 * min(concentration / 0.5, 1.0)

    # ── Signal B: category keyword coverage (category vertical) ──
    score_b = score_a  # default: same as A if no category match
    if category != 'General':
        cat_kws = {k for k in CATEGORY_KEYWORDS.get(category, [])
                   if ' ' not in k and len(k) >= 4}
        titles_with_cat_kw = sum(1 for ws in title_word_sets if ws & cat_kws)
        cat_coverage = titles_with_cat_kw / n
        # 45% of titles containing a category keyword → near-max score
        score_b = 1 + 9 * min(cat_coverage / 0.45, 1.0)

    return round(max(score_a, score_b), 1)


# ── Quadrant ──────────────────────────────────────────────────────────────────

def get_quadrant(asp: float, vertical_score: float) -> str:
    high_asp = asp > 100
    vertical = vertical_score >= 5
    if high_asp and vertical:
        return '右上'
    elif high_asp:
        return '左上'
    elif vertical:
        return '右下'
    else:
        return '左下'


def render_quadrant_chart(store: dict, T: dict = None) -> plt.Figure:
    if T is None:
        T = TRANSLATIONS['zh']
    asp = store['asp_median']
    vs = store['vertical_score']
    quadrant = get_quadrant(asp, vs)

    # eBay brand palette
    _Q_COLORS = {'右上': '#0064D2', '左上': '#86B817', '右下': '#F5AF02', '左下': '#E53238'}
    _Q_POS    = {'左上': (-5, 5),   '右上': (5, 5),   '左下': (-5, -5),  '右下': (5, -5)}
    _active_color = _Q_COLORS[quadrant]

    BG, GRID = '#ffffff', '#d1d5db'

    fig, ax = plt.subplots(figsize=(8, 5.5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(-11, 11)
    ax.set_ylim(-11, 11)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

    # Quadrant fills: active at 12% opacity, inactive at 4%
    _quad_regions = [('左上', -10, 0, 0, 10), ('右上', 0, 10, 0, 10),
                     ('左下', -10, 0, -10, 0), ('右下', 0, 10, -10, 0)]
    for _qn, x0, x1, y0, y1 in _quad_regions:
        _c = _Q_COLORS[_qn]
        _a = 0.13 if _qn == quadrant else 0.04
        _r, _g, _b = int(_c[1:3], 16)/255, int(_c[3:5], 16)/255, int(_c[5:7], 16)/255
        ax.fill_between([x0, x1], [y0, y0], [y1, y1], color=(_r, _g, _b, _a))

    ax.axhline(0, color=GRID, lw=1.5)
    ax.axvline(0, color=GRID, lw=1.5)

    # Ellipse only for active quadrant
    cx, cy = _Q_POS[quadrant]
    _r, _g, _b = int(_active_color[1:3], 16)/255, int(_active_color[3:5], 16)/255, int(_active_color[5:7], 16)/255
    ax.add_patch(Ellipse((cx, cy), 9, 7, fill=True,
                          facecolor=(_r, _g, _b, 0.15), edgecolor=_active_color, lw=2))

    ax.text(0, 10.8, T['axis_asp_high'], ha='center', color='#111827', fontsize=13, fontweight='bold')
    ax.text(0, -10.8, T['axis_asp_low'], ha='center', color='#111827', fontsize=13, fontweight='bold')
    ax.text(-11.5, 0, T['axis_scatter'], ha='center', va='center', color='#111827', fontsize=13, fontweight='bold')
    ax.text(11.5, 0, T['axis_vertical'], ha='center', va='center', color='#111827', fontsize=13, fontweight='bold')

    # Strategy label sits ABOVE/BELOW ellipse (ellipse top/bottom at ±8.5)
    _qlabels = {
        '左上': (-5,  9.3, 'PLG + PLP Auto + OA'),
        '右上': ( 5,  9.3, 'PLP Manual + PLP Auto + OA'),
        '左下': (-5, -9.3, 'PLG + OA'),
        '右下': ( 5, -9.3, 'PLG → PLP Manual + PLP Auto'),
    }
    if quadrant in _qlabels:
        _lx, _ly, _label = _qlabels[quadrant]
        ax.text(_lx, _ly, _label, ha='center', va='center',
                color=_active_color, fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=_active_color, alpha=0.9, lw=1))

    # Seller dot
    dot_x = min(max((vs - 5) * 2, -9), 9)
    raw_y = (np.log10(max(asp, 1)) - 2) * 7
    dot_y = min(max(raw_y, -9), 9)

    ax.scatter([dot_x], [dot_y], s=300, color=_active_color, zorder=10, edgecolors='white', lw=2)
    offset_x = 2.5 if dot_x < 4 else -2.5
    offset_y = 2.5 if dot_y < 4 else -2.5
    ax.annotate(
        f"{store['seller_id']}\nASP: ${asp:.0f}",
        (dot_x, dot_y),
        xytext=(dot_x + offset_x, dot_y + offset_y),
        color='#111827', fontsize=12, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor=_active_color, alpha=0.95),
        arrowprops=dict(arrowstyle='->', color=_active_color, lw=1.5),
    )


    ax.set_title(T['chart_title'], color='#111827', fontsize=12, fontweight='bold', pad=12)
    fig.tight_layout()
    return fig


# ── Keywords ──────────────────────────────────────────────────────────────────

SYNONYM_MAP = {
    # Plants & succulents
    'cactus': ['succulent', 'cacti', 'echeveria', 'haworthia', 'aloe'],
    'succulent': ['cactus', 'sedum', 'echeveria', 'stonecrop'],
    'orchid': ['phalaenopsis', 'dendrobium'],
    'bonsai': ['miniature tree', 'dwarf tree'],
    # Vehicles
    'car': ['vehicle', 'auto', 'automobile'],
    'vehicle': ['car', 'auto', 'automobile'],
    'auto': ['car', 'vehicle', 'automobile'],
    'truck': ['pickup', 'van'],
    'motorcycle': ['motorbike', 'moto'],
    'bike': ['bicycle', 'cycle', 'ebike'],
    'bicycle': ['bike', 'cycle', 'ebike'],
    # Electronics
    'phone': ['smartphone', 'mobile', 'cellphone'],
    'laptop': ['notebook', 'computer'],
    'tablet': ['ipad', 'pad'],
    'headphone': ['earphone', 'earbud', 'headset'],
    'headphones': ['earphones', 'earbuds', 'headset'],
    'earphone': ['headphone', 'earbud'],
    'earphones': ['headphones', 'earbuds'],
    # Clothing
    'shirt': ['tee', 'tshirt', 'top'],
    'shoes': ['sneakers', 'footwear', 'trainers'],
    'sneakers': ['shoes', 'trainers', 'kicks'],
    'jacket': ['coat', 'hoodie', 'outerwear'],
    'dress': ['gown', 'frock'],
    # Trading cards
    'pokemon': ['pocket monster', 'tcg'],
    # Jewelry
    'ring': ['band', 'jewelry'],
    'necklace': ['pendant', 'chain'],
    'bracelet': ['bangle', 'wristband'],
    # Home & Garden
    'sofa': ['couch', 'settee', 'loveseat'],
    'lamp': ['light', 'lighting'],
    'rug': ['carpet', 'mat'],
    'mattress': ['bed', 'memory foam'],
    # Tools
    'drill': ['power drill', 'cordless drill'],
    'saw': ['circular saw', 'jigsaw'],
    # Coins
    'coin': ['currency', 'numismatic', 'bullion'],
    # Food
    'coffee': ['espresso', 'java'],
}

def fetch_ebay_suggestions(q: str) -> list:
    try:
        r = requests.get(f"https://autosug.ebay.com/autosug?sId=0&kwd={requests.utils.quote(q)}",
                         headers=HEADERS, timeout=8)
        # API returns JSONP: /**/vjo...AutoFill._do({...})
        m = re.search(r'\._do\((.+)\)\s*$', r.text.strip())
        if m:
            import json as _json
            data = _json.loads(m.group(1))
            return data.get('res', {}).get('sug', [])
        # Fallback: try plain JSON
        return r.json().get('res', {}).get('sug', [])
    except:
        return []


def fetch_walmart_suggestions(q: str) -> list:
    urls = [
        f"https://www.walmart.com/search/autocomplete/v1?query={requests.utils.quote(q)}&max_results=10",
        f"https://www.walmart.com/typeahead?query={requests.utils.quote(q)}&max_results=10",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            data = r.json()
            # Try different response shapes
            if isinstance(data, list) and data:
                return [str(x) for x in data[:10] if x]
            terms = (data.get('suggestions') or data.get('items') or
                     data.get('results') or data.get('payload', {}).get('suggestions', []))
            if terms:
                results = []
                for s in terms:
                    if isinstance(s, str):
                        results.append(s)
                    elif isinstance(s, dict):
                        results.append(s.get('term') or s.get('query') or s.get('suggestion') or '')
                results = [r for r in results if r]
                if results:
                    return results
        except:
            pass
    return []


def fetch_amazon_suggestions(q: str) -> list:
    try:
        r = requests.get(
            f"https://completion.amazon.com/api/2017/suggestions"
            f"?limit=10&prefix={requests.utils.quote(q)}&suggestion-type=KEYWORD&mid=ATVPDKIKX0DER",
            headers=HEADERS, timeout=8)
        return [s['value'] for s in r.json().get('suggestions', [])]
    except:
        return []


def get_competitors(category: str) -> list:
    data = COMPETITOR_MAP.get(category, {'single': [], 'multi': []})
    return [b.lower() for b in data['single']] + [b.lower() for b, _ in data.get('multi', [])]


def classify_kw(kw: str, category: str, asp: float, T: dict = None) -> tuple:
    if T is None:
        T = TRANSLATIONS['zh']
    kw_l = kw.lower()
    words = kw_l.split()
    word_count = len(words)
    competitors = get_competitors(category)
    has_spec = bool(re.search(r'\d+\s?(w|v|mph|km|inch|lb|kg|cm|oz|speed)', kw_l))
    is_competitor = any(c in kw_l for c in competitors)
    scenario_words = ['for', 'commut', 'gift', 'adult', 'beginner', 'indoor', 'outdoor',
                      'offroad', 'off road', 'wedding', 'desk', 'office', 'kids', 'women', 'men']
    is_scenario = any(w in kw_l for w in scenario_words)

    is_specific_product = (word_count >= 3 and has_spec)
    is_branded_long = (word_count >= 5 and not is_scenario)
    is_exact_competitor = (is_competitor and word_count <= 3)
    is_broad_candidate = (
        word_count <= 2 and not has_spec and not is_competitor
        and (asp < 150 or category in ('Trading Cards', 'Coins & Paper Money', 'Comics & Memorabilia'))
    )

    if is_exact_competitor:
        kw_cat = T['cat_competitor']
        match = 'Exact'
        reason = T['reason_comp_exact']
    elif is_competitor:
        kw_cat = T['cat_competitor']
        match = 'Phrase'
        reason = T['reason_comp_phrase']
    elif is_specific_product:
        kw_cat = T['cat_spec']
        match = 'Exact'
        reason = T['reason_spec_exact']
    elif is_branded_long:
        kw_cat = T['cat_core']
        match = 'Exact'
        reason = T['reason_branded_long']
    elif has_spec:
        kw_cat = T['cat_spec']
        match = 'Phrase'
        reason = T['reason_has_spec']
    elif is_scenario:
        kw_cat = T['cat_scenario']
        match = 'Phrase'
        reason = T['reason_scenario']
    elif is_broad_candidate:
        kw_cat = T['cat_core']
        match = 'Broad'
        reason = T['reason_broad'].replace('${asp}', f'{asp:.0f}')
    else:
        kw_cat = T['cat_core']
        match = 'Phrase'
        reason = T['reason_default']

    return kw_cat, match, reason


# Generic words that are too broad to use as standalone seeds
_GENERIC_SEEDS = {
    'plant', 'plants', 'flower', 'flowers', 'tree', 'trees', 'seed', 'seeds',
    'card', 'cards', 'item', 'items', 'part', 'parts', 'piece', 'pieces',
    'product', 'products', 'thing', 'stuff', 'accessory', 'accessories',
    'tool', 'tools', 'gear', 'supply', 'supplies', 'type', 'style', 'model',
    'black', 'white', 'blue', 'red', 'green', 'pink', 'small', 'large', 'mini',
}


def extract_seeds_from_titles(titles: list, category: str, n: int = 6) -> list[str]:
    """Extract product-specific bigram/trigram seeds from listing titles.
    Brand words (appearing in >60% of titles but not a known category keyword) are
    excluded so seeds reflect what buyers search, not the seller's brand name.
    """
    if not titles:
        return SEED_MAP.get(category, [category.lower()])

    from collections import Counter

    # Detect brand words: high-frequency words that are NOT category keywords
    all_cat_kws = {k for kws in CATEGORY_KEYWORDS.values() for k in kws if ' ' not in k}
    raw_word_freq: Counter = Counter()
    for t in titles:
        for w in re.sub(r'[^a-z0-9 ]', ' ', t.lower()).split():
            if len(w) >= 4 and w not in STOP_WORDS:
                raw_word_freq[w] += 1
    n_titles = len(titles)
    brand_words = {w for w, f in raw_word_freq.items()
                   if f / n_titles > 0.60 and w not in all_cat_kws}

    # Extended stop: exclude brand words so seeds are buyer-intent phrases
    seed_stop = STOP_WORDS | brand_words

    seeds = []

    # Bigrams / trigrams (primary seeds)
    bigram_freq: dict = {}
    trigram_freq: dict = {}
    for t in titles:
        words = [w for w in re.sub(r'[^a-z0-9 ]', ' ', t.lower()).split()
                 if len(w) >= 3 and w not in seed_stop]
        for i in range(len(words) - 1):
            bg = f"{words[i]} {words[i+1]}"
            bigram_freq[bg] = bigram_freq.get(bg, 0) + 1
        for i in range(len(words) - 2):
            tg = f"{words[i]} {words[i+1]} {words[i+2]}"
            trigram_freq[tg] = trigram_freq.get(tg, 0) + 1

    # Prefer trigrams (more specific), then fill with non-redundant bigrams
    top_trigrams = sorted(trigram_freq, key=trigram_freq.get, reverse=True)[:3]
    top_bigrams = sorted(bigram_freq, key=bigram_freq.get, reverse=True)[:5]
    seeds += top_trigrams
    for bg in top_bigrams:
        # Skip bigram if it's a substring of an already-added trigram (redundant)
        if not any(bg in tg for tg in top_trigrams):
            seeds.append(bg)

    # Single-word seeds: specific product words not in brand/stop/generic lists
    word_freq: dict = {}
    for t in titles:
        for w in re.sub(r'[^a-z0-9 ]', ' ', t.lower()).split():
            if len(w) >= 5 and w not in seed_stop and w not in _GENERIC_SEEDS:
                word_freq[w] = word_freq.get(w, 0) + 1
    top_specific = sorted(word_freq, key=word_freq.get, reverse=True)[:2]
    seeds += top_specific

    # Category fallback if we found nothing useful
    if not seeds:
        seeds += SEED_MAP.get(category, [category.lower()])[:2]

    return list(dict.fromkeys(seeds))[:n]


def title_validates(kw: str, titles: list) -> bool:
    """Hard gate: every meaningful word in kw must appear somewhere in seller's catalog.
    Foreign words (absent from all titles) indicate the keyword is off-topic.
    With <10 titles, falls back to a softer majority check to avoid over-rejection."""
    if not titles:
        return False
    kw_words = [w for w in re.sub(r'[^a-z0-9 ]', ' ', kw.lower()).split()
                if len(w) >= 4 and w not in STOP_WORDS]
    if not kw_words:
        return True

    title_corpus: set = set()
    for t in titles:
        for w in re.sub(r'[^a-z0-9 ]', ' ', t.lower()).split():
            if len(w) >= 4 and w not in STOP_WORDS:
                title_corpus.add(w)

    if len(titles) >= 10:
        # Hard gate: no foreign word allowed (1 allowed for long keywords)
        foreign = [w for w in kw_words if w not in title_corpus]
        max_foreign = 1 if len(kw_words) >= 4 else 0
        return len(foreign) <= max_foreign

    # Soft check for sparse title sets
    hits = sum(1 for w in kw_words if w in title_corpus)
    return hits >= max(1, len(kw_words) // 2)


def is_valid_kw(kw: str) -> bool:
    if re.search(r'=\s*[0-9]', kw):
        return False
    if re.match(r'^[0-9\s.=]+$', kw):
        return False
    if any(u in kw for u in ['kilometer', 'miles', 'celsius', 'fahrenheit', 'pounds to']):
        return False
    if len(kw.split()) < 2 and len(kw) < 6:
        return False
    return True


def _get_synonym_seeds(seeds: list) -> list:
    """Expand seed list with synonyms from SYNONYM_MAP."""
    syn_seeds = []
    for seed in seeds:
        for word in seed.split():
            for syn in SYNONYM_MAP.get(word, []):
                if syn not in seeds and syn not in syn_seeds:
                    syn_seeds.append(syn)
    return syn_seeds[:4]  # cap to avoid too many requests


def _fetch_kw_candidates(seeds: list, titles: list) -> tuple:
    """Network-only step: fetch autocomplete from eBay / Amazon / Walmart.
    Returns (candidates_dict, synonym_kws_set).
    Google excluded — its autocomplete reflects general web searches, not purchase intent."""
    all_kws: dict = {}
    _sources = [('eBay', fetch_ebay_suggestions),
                ('Amazon', fetch_amazon_suggestions),
                ('Walmart', fetch_walmart_suggestions)]

    # Regular seeds
    for seed in seeds:
        for source, fn in _sources:
            for kw in fn(seed)[:20]:
                kw = kw.strip().lower()
                if not kw or len(kw) < 3:
                    continue
                if kw not in all_kws:
                    all_kws[kw] = set()
                all_kws[kw].add(source)
        time.sleep(0.3)

    # Synonym seeds — same 3 sources, fewer results
    synonym_kws: set = set()
    for seed in _get_synonym_seeds(seeds):
        for source, fn in _sources:
            for kw in fn(seed)[:15]:
                kw = kw.strip().lower()
                if not kw or len(kw) < 3:
                    continue
                if kw not in all_kws:
                    all_kws[kw] = set()
                all_kws[kw].add(source)
                synonym_kws.add(kw)
        time.sleep(0.3)

    return all_kws, synonym_kws


def _build_kw_df(candidates: dict, category: str, asp: float,
                 seller_id: str, titles: list, T: dict,
                 synonym_kws: set = None) -> pd.DataFrame:
    """Priority-based selection — no cross-validation required.
    Order: eBay Titles > eBay > Amazon > Walmart. is_valid_kw is the only filter."""
    if synonym_kws is None:
        synonym_kws = set()

    SOURCE_WEIGHT = {T['source_ebay_title']: 4, 'eBay': 3, 'Amazon': 2, 'Walmart': 1}

    # Score every candidate keyword
    has_robust_titles = len(titles) >= 10
    scored = []
    for kw, sources_set in candidates.items():
        if not is_valid_kw(kw):
            continue
        sources = list(sources_set)
        validates = title_validates(kw, titles)
        if validates:
            sources.append(T['source_ebay_title'])
        # Hard gate: sufficient titles available → reject keywords foreign to catalog
        if has_robust_titles and not validates:
            continue
        if not sources:
            continue
        priority_score = sum(SOURCE_WEIGHT.get(s, 0) for s in sources)
        display_sources = sorted(sources, key=lambda s: -SOURCE_WEIGHT.get(s, 0))
        is_syn = (kw in synonym_kws)
        scored.append((kw, display_sources, priority_score, is_syn))

    # Sort by priority score descending (eBay Title > eBay > Amazon > Walmart)
    scored.sort(key=lambda x: -x[2])

    col_kw = T['col_keyword']
    col_cat = T['col_category']
    col_match = T['col_match']
    col_src = T['col_source']
    col_cnt = T['col_count']
    col_note = T['col_note']

    rows = [{col_kw: f'[{seller_id}]', col_cat: T['cat_brand'], col_match: 'Exact',
             col_src: T['source_own'], col_cnt: 4, col_note: T['reason_brand']}]
    for kw, display_sources, score, is_syn in scored[:15]:
        if is_syn:
            kw_cat = T['cat_synonym']
            match = 'Phrase'
            reason = T['reason_synonym']
        else:
            kw_cat, match, reason = classify_kw(kw, category, asp, T)
        rows.append({col_kw: kw, col_cat: kw_cat, col_match: match,
                     col_src: ' / '.join(display_sources),
                     col_cnt: len(display_sources), col_note: reason})
    return pd.DataFrame(rows)


def get_keywords(category: str, asp: float, seller_id: str, titles: list = None, T: dict = None) -> pd.DataFrame:
    if T is None:
        T = TRANSLATIONS['zh']
    titles = titles or []
    seeds = extract_seeds_from_titles(titles, category)
    candidates, synonym_kws = _fetch_kw_candidates(seeds, titles)
    return _build_kw_df(candidates, category, asp, seller_id, titles, T, synonym_kws)


# ── PLG Ad Groups ─────────────────────────────────────────────────────────────

def get_plg_groups(prices: list, seller_id: str, T: dict = None) -> pd.DataFrame:
    if T is None:
        T = TRANSLATIONS['zh']
    if not prices:
        return pd.DataFrame()

    max_p = max(prices)
    tiers = (
        [(0, 50, 12), (50, 100, 8), (100, 300, 5), (300, 700, 3), (700, 99999, 2)]
        if max_p > 300
        else [(0, 20, 15), (20, 50, 12), (50, 100, 8), (100, 99999, 5)]
    )

    rows = []
    for lo, hi, rate in tiers:
        count = sum(1 for p in prices if lo < p <= hi)
        if count == 0:
            continue
        hi_str = str(hi) if hi < 99999 else '+'
        name = f"{seller_id}_${lo}-{hi_str}_{rate}%"
        avg_in_tier = np.mean([p for p in prices if lo < p <= hi])
        abs_bid = avg_in_tier * rate / 100
        if rate >= 10:
            note = T['plg_note_high']
        elif lo >= 300:
            note = T['plg_note_plp']
        else:
            note = T['plg_note_ok']
        rows.append({
            T['plg_col_name']: name,
            T['plg_col_range']: f'${lo} – ${hi_str}',
            T['plg_col_rate']: f'{rate}%',
            T['plg_col_bid']: f'${abs_bid:.2f}',
            T['plg_col_listing']: count,
            T['plg_col_note']: note,
        })

    return pd.DataFrame(rows)


# ── Streamlit UI ──────────────────────────────────────────────────────────────

LANG_OPTIONS = {'🇨🇳 中文': 'zh', '🇺🇸 English': 'en', '🇮🇳 हिंदी': 'hi'}

TRANSLATIONS = {
    'zh': {
        # Page
        'page_title': 'eBay 广告策略看板',
        'title': 'eBay 广告策略看板',
        'subtitle': '输入卖家账号，分析店铺并生成专属广告策略建议',
        'input_placeholder': '输入 eBay 卖家账号，例如 XXXX',
        'analyze_btn': '开始分析',
        'spinner_analyze': '正在分析 {sid} 的店铺...',
        'error_no_data': '未能获取店铺数据，请检查账号是否正确。',
        # Overview panel
        'store_overview': '店铺概况',
        'asp_label': 'ASP 中位',
        'listing_count': '总 Listing 数',
        'vertical_score': '垂直度',
        'main_category': '**主要品类**：',
        'quadrant_label': '**所在象限**：',
        'data_source': '数据来源：',
        'rec_combo': '推荐广告组合',
        'ds_sold_current': '已售出 + 当前在售',
        'ds_no_data': '无数据',
        # KW section
        'kw_section': 'PLP 广告关键词推荐',
        'kw_caption': '四源优先级排序（标题 > eBay > Amazon > Walmart），按相关性从高到低推荐',
        'spinner_kw': '正在抓取关键词数据...',
        'col_keyword': '关键词',
        'col_category': '分类',
        'col_match': '匹配方式',
        'col_source': '验证来源',
        'col_count': '验证数',
        'col_note': '推荐原因',
        # KW cell values
        'cat_brand': '品牌词',
        'cat_competitor': '竞品词',
        'cat_spec': '规格词',
        'cat_scenario': '场景词',
        'cat_core': '产品核心词',
        'cat_synonym': '同义词',
        'source_own': '自有品牌',
        'source_ebay_title': 'eBay标题',
        'reason_brand': '防御自有品牌，避免被竞品截流',
        'reason_comp_exact': '竞品品牌词Exact，精准截流，避免浪费在无关变体',
        'reason_comp_phrase': '竞品词Phrase，覆盖买家加词搜索（如"品牌+type"）',
        'reason_spec_exact': '含具体规格参数，买家意图极明确，Exact控制精准度',
        'reason_branded_long': '4词以上具体产品词，搜索量小但转化高，Exact避免浪费',
        'reason_has_spec': '含规格Phrase保持词序，过滤无关流量',
        'reason_scenario': '场景词Phrase，精准匹配使用意图',
        'reason_broad': '短泛词，ASP ${asp} 或小众品类需Broad补充曝光，配否定词',
        'reason_default': '默认Phrase，平衡覆盖与精准，适合弱运营卖家',
        'reason_synonym': '同义词扩展，覆盖买家使用不同词汇搜索同类产品的场景',
        # PLG section
        'plg_section': 'PLG 广告组设置',
        'plg_caption': '按价格区间分组 — 低单价高费率、高单价低费率，保证各区间绝对出价有竞争力',
        'plg_no_data': '价格数据不足，无法自动生成广告组建议',
        'plg_col_name': '广告组名称',
        'plg_col_range': '价格区间',
        'plg_col_rate': '出价费率',
        'plg_col_bid': '预计平均绝对出价',
        'plg_col_listing': 'Listing数量',
        'plg_col_note': '备注',
        'plg_note_high': '高费率补低单价竞争力',
        'plg_note_ok': '绝对出价已足够竞争',
        'plg_note_plp': '低费率节省预算，配合 PLP 关键词广告投放',
        # KW section — quadrant-based gating
        'kw_no_kw_msg': '该卖家属于低单价铺货类型，CPC 成本易侵蚀利润。\n\n**推荐策略：** 优先开启 **PLS（Promoted Listings Standard）** 测爆款，再通过 **Smart Targeting** 自动匹配买家意图，无需手动关键词。',
        'kw_highval_note': '⚠️ 铺货卖家建议仅对高单价商品（≥ $${asp}）开启 PLP 关键词投放，其余商品走 Smart Targeting。',
        'kw_copy_expander': '📋 点击展开 — 一键复制关键词',
        # Chart
        'chart_title': 'eBay 广告策略象限图',
        'axis_asp_high': 'ASP 高 (>$100)',
        'axis_asp_low': 'ASP 低 (≤$100)',
        'axis_scatter': '铺货',
        'axis_vertical': '垂直',
        'quadrant_labels': {'右上': '高ASP + 垂直', '左上': '高ASP + 铺货', '右下': '低ASP + 垂直', '左下': '低ASP + 铺货'},
        'quadrant_reasons': {
            '右上': '高利润支撑CPC，垂直品类关键词集中；手动词精准控ACOS，自动词补长尾，OA引外站高价流量',
            '左上': 'SKU多品类杂，手动关键词维护成本极高；PLG全覆盖+Smart Targeting托管高价品，OA整店推广',
            '右下': '低单价CPC风险高；先用PLG测爆款，有出单记录后对爆款单独开手动词，Smart Targeting补量',
            '左下': 'CPC几乎无利润空间；PLG按出单付费控风险，OA整店维度推广补充站外曝光',
        },
    },
    'en': {
        # Page
        'page_title': 'eBay Ads Strategy Dashboard',
        'title': 'eBay Ads Strategy Dashboard',
        'subtitle': 'Enter a seller ID to analyze the store and generate ad strategy recommendations based on <b>sold listings</b>',
        'input_placeholder': 'Enter eBay seller ID, e.g. XXXX',
        'analyze_btn': 'Analyze',
        'spinner_analyze': 'Analyzing store: {sid}...',
        'error_no_data': 'Could not fetch store data. Please check if the seller ID is correct.',
        # Overview panel
        'store_overview': 'Store Overview',
        'asp_label': 'Median ASP',
        'listing_count': 'Total Listings',
        'vertical_score': 'Vertical Score',
        'main_category': '**Category**: ',
        'quadrant_label': '**Quadrant**: ',
        'data_source': 'Data source: ',
        'rec_combo': 'Recommended Ad Mix',
        'ds_sold_current': 'Sold + Active Listings',
        'ds_no_data': 'No Data',
        # KW section
        'kw_section': 'PLP Keyword Recommendations',
        'kw_caption': '4-source priority ranking (Titles > eBay > Amazon > Walmart), ordered by relevance',
        'spinner_kw': 'Fetching keyword data...',
        'col_keyword': 'Keyword',
        'col_category': 'Category',
        'col_match': 'Match Type',
        'col_source': 'Validated By',
        'col_count': 'Sources',
        'col_note': 'Notes',
        # KW cell values
        'cat_brand': 'Brand',
        'cat_competitor': 'Competitor',
        'cat_spec': 'Spec',
        'cat_scenario': 'Scenario',
        'cat_core': 'Core Product',
        'cat_synonym': 'Synonym',
        'source_own': 'Own Brand',
        'source_ebay_title': 'eBay Titles',
        'reason_brand': 'Defend own brand — prevent competitors from intercepting traffic',
        'reason_comp_exact': 'Competitor brand Exact — precise interception, no wasted spend on variants',
        'reason_comp_phrase': 'Competitor Phrase — covers buyer searches like "brand + type"',
        'reason_spec_exact': 'Specific spec/model — very clear buyer intent, Exact maximises precision',
        'reason_branded_long': '4+ word specific product term — low volume but high conversion, Exact avoids waste',
        'reason_has_spec': 'Contains spec — Phrase preserves word order and filters irrelevant traffic',
        'reason_scenario': 'Use-case term — Phrase matches buyer intent precisely',
        'reason_broad': 'Short generic term — ASP ${asp} or niche category needs Broad for reach; add negatives',
        'reason_default': 'Default Phrase — balances reach and precision for lean operations',
        'reason_synonym': 'Synonym expansion — captures buyers who search with different words for the same product',
        # PLG section
        'plg_section': 'PLG Ad Group Settings',
        'plg_caption': 'Grouped by price range — lower ASP = higher rate, higher ASP = lower rate',
        'plg_no_data': 'Not enough price data to generate ad group recommendations',
        'plg_col_name': 'Ad Group Name',
        'plg_col_range': 'Price Range',
        'plg_col_rate': 'Ad Rate',
        'plg_col_bid': 'Est. Avg Absolute Bid',
        'plg_col_listing': 'Listing Count',
        'plg_col_note': 'Notes',
        'plg_note_high': 'Higher rate compensates for low unit price',
        'plg_note_ok': 'Absolute bid already competitive',
        'plg_note_plp': 'Low rate saves budget — pair with PLP keyword ads',
        # Chart (ASCII only — matplotlib cannot render Devanagari or CJK without extra fonts)
        'chart_title': 'eBay Ads Strategy Quadrant',
        'axis_asp_high': 'High ASP (>$100)',
        'axis_asp_low': 'Low ASP (≤$100)',
        'axis_scatter': 'Broad',
        'axis_vertical': 'Vertical',
        'quadrant_labels': {
            '右上': 'High ASP + Vertical', '左上': 'High ASP + Broad',
            '右下': 'Low ASP + Vertical', '左下': 'Low ASP + Broad',
        },
        'quadrant_reasons': {
            '右上': 'High margin supports CPC bids; concentrated vertical keywords make precise targeting worthwhile',
            '左上': 'Too many SKUs for manual management; algorithm automation + OA for offsite traffic',
            '右下': 'CPC risk is high; build sales history with PLS first, add Smart Targeting for model/category terms',
            '左下': 'CPC hurts margin; broad catalog is hard to target precisely — use PLS to find winners',
        },
    },
    'hi': {
        # Page
        'page_title': 'eBay विज्ञापन रणनीति डैशबोर्ड',
        'title': 'eBay विज्ञापन रणनीति डैशबोर्ड',
        'subtitle': 'विक्रेता ID दर्ज करें — <b>बिके हुए उत्पादों</b> के आधार पर स्टोर विश्लेषण और विज्ञापन सुझाव',
        'input_placeholder': 'eBay विक्रेता ID दर्ज करें, जैसे XXXX',
        'analyze_btn': 'विश्लेषण करें',
        'spinner_analyze': '{sid} का स्टोर विश्लेषण हो रहा है...',
        'error_no_data': 'स्टोर डेटा प्राप्त नहीं हो सका। कृपया विक्रेता ID जांचें।',
        # Overview panel
        'store_overview': 'स्टोर सारांश',
        'asp_label': 'औसत ASP',
        'listing_count': 'कुल लिस्टिंग',
        'vertical_score': 'वर्टिकल स्कोर',
        'main_category': '**मुख्य श्रेणी**: ',
        'quadrant_label': '**चतुर्थांश**: ',
        'data_source': 'डेटा स्रोत: ',
        'rec_combo': 'अनुशंसित विज्ञापन संयोजन',
        'ds_sold_current': 'बिके + सक्रिय लिस्टिंग',
        'ds_no_data': 'डेटा नहीं',
        # KW section
        'kw_section': 'PLP कीवर्ड सुझाव',
        'kw_caption': '4-स्रोत प्राथमिकता (शीर्षक > eBay > Amazon > Walmart), प्रासंगिकता के अनुसार क्रमबद्ध',
        'spinner_kw': 'कीवर्ड डेटा प्राप्त हो रहा है...',
        'col_keyword': 'कीवर्ड',
        'col_category': 'श्रेणी',
        'col_match': 'मिलान प्रकार',
        'col_source': 'सत्यापन स्रोत',
        'col_count': 'स्रोत संख्या',
        'col_note': 'टिप्पणी',
        # KW cell values
        'cat_brand': 'ब्रांड',
        'cat_competitor': 'प्रतिस्पर्धी',
        'cat_spec': 'विनिर्देश',
        'cat_scenario': 'परिदृश्य',
        'cat_core': 'मुख्य उत्पाद',
        'cat_synonym': 'पर्यायवाची',
        'source_own': 'स्वयं का ब्रांड',
        'source_ebay_title': 'eBay शीर्षक',
        'reason_brand': 'अपने ब्रांड की रक्षा करें — प्रतिस्पर्धियों को ट्रैफ़िक छीनने से रोकें',
        'reason_comp_exact': 'प्रतिस्पर्धी Exact — सटीक अवरोधन, बर्बादी नहीं',
        'reason_comp_phrase': 'प्रतिस्पर्धी Phrase — "ब्रांड + प्रकार" जैसी खोजों को कवर करता है',
        'reason_spec_exact': 'विशिष्ट विनिर्देश — स्पष्ट खरीदार इरादा, Exact सटीकता बढ़ाता है',
        'reason_branded_long': '4+ शब्द उत्पाद — कम खोज लेकिन उच्च रूपांतरण, Exact बर्बादी कम करता है',
        'reason_has_spec': 'विनिर्देश युक्त — Phrase शब्द क्रम बनाए रखता है',
        'reason_scenario': 'उपयोग परिदृश्य — Phrase खरीदार इरादे से मेल खाता है',
        'reason_broad': 'छोटा सामान्य शब्द — ASP ${asp} या niche श्रेणी के लिए Broad; नकारात्मक शब्द जोड़ें',
        'reason_default': 'डिफ़ॉल्ट Phrase — कवरेज और सटीकता का संतुलन',
        'reason_synonym': 'पर्यायवाची विस्तार — अलग शब्दों से खोजने वाले खरीदारों को कवर करता है',
        # PLG section
        'plg_section': 'PLG विज्ञापन समूह सेटिंग',
        'plg_caption': 'मूल्य सीमा के अनुसार समूहीकृत — कम ASP = अधिक दर, अधिक ASP = कम दर',
        'plg_no_data': 'पर्याप्त मूल्य डेटा नहीं — विज्ञापन समूह सुझाव उत्पन्न नहीं हो सके',
        'plg_col_name': 'विज्ञापन समूह',
        'plg_col_range': 'मूल्य सीमा',
        'plg_col_rate': 'विज्ञापन दर',
        'plg_col_bid': 'अनुमानित बोली',
        'plg_col_listing': 'लिस्टिंग संख्या',
        'plg_col_note': 'टिप्पणी',
        'plg_note_high': 'उच्च दर कम मूल्य की भरपाई करती है',
        'plg_note_ok': 'बोली पहले से प्रतिस्पर्धी है',
        'plg_note_plp': 'कम दर बजट बचाती है — PLP कीवर्ड विज्ञापन के साथ उपयोग करें',
        # Chart — use ASCII/English to avoid font rendering issues in matplotlib
        'chart_title': 'eBay Ads Strategy Quadrant',
        'axis_asp_high': 'High ASP (>$100)',
        'axis_asp_low': 'Low ASP (≤$100)',
        'axis_scatter': 'Broad',
        'axis_vertical': 'Vertical',
        'quadrant_labels': {
            '右上': 'High ASP + Vertical', '左上': 'High ASP + Broad',
            '右下': 'Low ASP + Vertical', '左下': 'Low ASP + Broad',
        },
        'quadrant_reasons': {
            '右上': 'उच्च मार्जिन CPC बोली का समर्थन करता है; वर्टिकल कीवर्ड केंद्रित हैं',
            '左上': 'बहुत अधिक SKU — एल्गोरिदम स्वचालन + OA बेहतर',
            '右下': 'CPC जोखिम अधिक; पहले PLS से बिक्री बनाएं, फिर Smart Targeting',
            '左下': 'CPC मार्जिन को नुकसान पहुंचाता है; PLS से विजेता खोजें',
        },
    },
}

st.set_page_config(page_title="eBay 广告策略看板", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* ── Desktop ── */
.block-container { padding: 2rem 3rem 3rem; }
h1, h2, h3 { color: #0064D2 !important; }
.stButton > button {
    background-color: #0064D2; color: white; border: none;
    border-radius: 24px; padding: 0.55rem 2rem; font-size: 1rem; font-weight: 600;
}
.stButton > button:hover { background-color: #0050a8; }
div[data-testid="metric-container"] {
    background: #f8f9fa; border-radius: 8px; padding: 1rem;
    border: 1px solid #e5e7eb;
}

/* ── Mobile ── */
@media (max-width: 768px) {
    .block-container { padding: 1rem 1rem 2rem !important; }
    h1 { font-size: 1.6rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1rem !important; }
    /* 搜索框全宽 */
    .stTextInput input { font-size: 1rem !important; }
    .stButton > button { width: 100% !important; border-radius: 12px !important; }
    /* 指标卡片缩小内边距 */
    div[data-testid="metric-container"] { padding: 0.6rem !important; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    /* 分割线间距 */
    hr { margin: 0.8rem 0 !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Language selector (always top-right) ──
if 'lang_label' not in st.session_state:
    st.session_state.lang_label = '🇨🇳 中文'

_lang_col = st.columns([6, 1])[1]
with _lang_col:
    st.session_state.lang_label = st.selectbox(
        '🌐', list(LANG_OPTIONS.keys()),
        index=list(LANG_OPTIONS.keys()).index(st.session_state.lang_label),
        label_visibility='collapsed',
    )

T = TRANSLATIONS[LANG_OPTIONS[st.session_state.lang_label]]

_has_results = bool(st.session_state.get('cached_sid'))

if not _has_results:
    # ── Google-style landing page ──
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
    _, _center, _ = st.columns([0.2, 3, 0.2])
    with _center:
        st.markdown(
            f"<h1 style='text-align:center;color:#0064D2;font-size:2.6rem;margin-bottom:4px;'>{T['title']}</h1>",
            unsafe_allow_html=True)
        st.markdown(
            f"<p style='text-align:center;color:#6b7280;margin-bottom:24px;'>{T['subtitle']}</p>",
            unsafe_allow_html=True)
        with st.form("search_form"):
            seller_id_input = st.text_input(
                "seller_id", placeholder=T['input_placeholder'], label_visibility='collapsed')
            analyze = st.form_submit_button(
                T['analyze_btn'], use_container_width=True)
else:
    # ── Compact top bar after search ──
    _t_col, _s_col = st.columns([2, 5])
    with _t_col:
        st.markdown(f"<h2 style='margin-bottom:0;'>{T['title']}</h2>", unsafe_allow_html=True)
    with _s_col:
        with st.form("search_form"):
            _in_c, _btn_c, _ = st.columns([4, 1, 1])
            with _in_c:
                seller_id_input = st.text_input(
                    "seller_id", placeholder=T['input_placeholder'], label_visibility='collapsed')
            with _btn_c:
                analyze = st.form_submit_button(T['analyze_btn'], use_container_width=True)

# New search → fetch data and cache it; language change → use cache
if analyze and seller_id_input.strip():
    new_sid = seller_id_input.strip()
    if new_sid != st.session_state.get('cached_sid'):
        # Different seller: clear all caches
        st.session_state['cached_sid'] = new_sid
        st.session_state.pop('cached_store', None)
        st.session_state.pop('cached_kw_candidates', None)

# Nothing cached yet and no new search → show nothing
if 'cached_sid' not in st.session_state:
    st.stop()

seller_id = st.session_state['cached_sid']

# Fetch & cache store (slow: HTTP requests)
if 'cached_store' not in st.session_state:
    with st.spinner(T['spinner_analyze'].format(sid=seller_id)):
        st.session_state['cached_store'] = scrape_store(seller_id)

store = st.session_state['cached_store']

if store['listing_count'] == 0:
    st.error(T['error_no_data'])
    st.stop()

quadrant = get_quadrant(store['asp_median'], store['vertical_score'])
qinfo = QUADRANT_INFO[quadrant]

st.markdown("---")

# ── Row 1: Chart + Summary ──
col_chart, col_rec = st.columns([3, 2])

with col_chart:
    fig = render_quadrant_chart(store, T)
    st.pyplot(fig)
    plt.close(fig)
    _img_urls = store.get('image_urls', [])
    if _img_urls:
        st.caption(f"📦 {store['seller_id']} 店铺商品")
        _ic = st.columns(len(_img_urls))
        for _i, _url in enumerate(_img_urls):
            with _ic[_i]:
                st.image(_url, use_container_width=True)

with col_rec:
    st.subheader(T['store_overview'])
    m1, m2, m3 = st.columns(3)
    m1.metric(T['asp_label'], f"${store['asp_median']:.0f}")
    _total = store.get('total_listing_count', '')
    m2.metric(T['listing_count'], _total if _total else store['listing_count'])
    m3.metric(T['vertical_score'], f"{store['vertical_score']}/10")

    st.markdown(f"{T['main_category']}{store['category']}")
    _qlabel = T['quadrant_labels'].get(quadrant, quadrant)
    st.markdown(f"{T['quadrant_label']}{_qlabel}")
    _ds_raw = store['data_source']
    _ds_map = {'已售出 + 当前在售': T['ds_sold_current'], '无数据': T['ds_no_data']}
    _ds = _ds_map.get(_ds_raw, _ds_raw)
    st.caption(f"{T['data_source']}{_ds}")

    st.subheader(T['rec_combo'])
    st.success(f"**{qinfo['strategy']}**")
    _reason = T['quadrant_reasons'].get(quadrant, qinfo['reason'])
    st.caption(_reason)

    # ── Budget allocation insight (uses st.markdown for full responsiveness) ──
    _alloc = QUADRANT_ALLOCATION[quadrant]
    _bar_segs = ''.join(
        f'<div style="width:{pct}%;background:{color};display:flex;align-items:center;'
        f'justify-content:center;color:#fff;font-size:0.75em;font-weight:700;'
        f'white-space:nowrap;overflow:hidden;padding:0 4px;">'
        f'{name} {pct}%</div>'
        for name, pct, color, _ in _alloc
    )
    _bullets = ''.join(
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:6px 0;'
        f'border-bottom:1px solid rgba(255,255,255,0.06);">'
        f'<div style="width:9px;height:9px;border-radius:50%;background:{color};'
        f'flex-shrink:0;margin-top:4px;"></div>'
        f'<div style="line-height:1.5;">'
        f'<span style="color:{color};font-weight:700;">{name}</span>'
        f'<span style="color:#374151;font-weight:600;"> · {pct}%</span>'
        f'<span style="color:#6b7280;font-size:0.9em;margin-left:8px;">{desc}</span>'
        f'</div>'
        f'</div>'
        for name, pct, color, desc in _alloc
    )
    st.markdown(
        f'<div style="margin:8px 0 4px 0;">'
        f'<div style="color:#6b7280;font-size:0.75em;font-weight:600;margin-bottom:8px;letter-spacing:.5px;text-transform:uppercase;">广告投入占比建议</div>'
        f'<div style="display:flex;height:26px;border-radius:5px;overflow:hidden;margin-bottom:12px;gap:2px;">{_bar_segs}</div>'
        f'{_bullets}'
        f'<div style="margin-top:10px;color:#4b5563;font-size:0.75em;line-height:1.6;">'
        f'* PLG 按出单付费（CPS），无固定日预算 &nbsp;|&nbsp; OA 为 eBay 邀请项目，独立计费'
        f'</div></div>',
        unsafe_allow_html=True
    )

# ── Row 2: PLP Keywords ──
st.markdown("---")
st.subheader(T['kw_section'])

# Quadrant-gated display:
# 左下 (低ASP + 非垂直 铺货) → Smart Targeting only, no keywords needed
# 左上 (高ASP + 非垂直 铺货) → keywords shown, but with high-value targeting note
# 右上 / 右下 (垂直) → normal keyword analysis
if quadrant == '左下':
    st.warning(T['kw_no_kw_msg'])
else:
    if quadrant == '左上':
        _note = T['kw_highval_note'].replace('${asp}', f"{store['asp_median']:.0f}")
        st.info(_note)

    st.caption(T['kw_caption'])

    # Fetch & cache raw keyword candidates (slow: HTTP requests)
    # Validate cache format — must be (dict, set); clear if stale/old format
    _cached = st.session_state.get('cached_kw_candidates')
    if not (isinstance(_cached, tuple) and len(_cached) == 2
            and isinstance(_cached[0], dict) and isinstance(_cached[1], set)):
        st.session_state.pop('cached_kw_candidates', None)

    if 'cached_kw_candidates' not in st.session_state:
        with st.spinner(T['spinner_kw']):
            _titles = store.get('titles', [])
            _seeds = extract_seeds_from_titles(_titles, store['category'])
            st.session_state['cached_kw_candidates'] = _fetch_kw_candidates(_seeds, _titles)

    # Build df with current language (fast, no network)
    _candidates, _synonym_kws = st.session_state['cached_kw_candidates']
    kw_df = _build_kw_df(
        _candidates,
        store['category'], store['asp_median'], seller_id,
        store.get('titles', []), T, _synonym_kws,
    )

    import streamlit.components.v1 as _components

    _ck  = T['col_keyword']
    _cc  = T['col_category']
    _cm  = T['col_match']
    _cs  = T['col_source']
    _cn  = T['col_count']
    _cno = T['col_note']

    _rows_html = ''
    for _, _row in kw_df.iterrows():
        _kw    = str(_row[_ck])
        _match = str(_row[_cm])
        _mc    = {'Exact': '#FFD700', 'Broad': '#FF9966'}.get(_match, '#7EC8E3')
        _is_kw = not _kw.startswith('[')
        _td_kw = (
            f'<td class="cp" onclick="cpKw(this)" title="点击复制">{_kw}</td>'
            if _is_kw else f'<td style="color:#9ca3af">{_kw}</td>'
        )
        _rows_html += (
            f'<tr>{_td_kw}'
            f'<td>{_row[_cc]}</td>'
            f'<td style="color:{_mc};font-weight:600">{_match}</td>'
            f'<td>{_row[_cs]}</td>'
            f'<td style="text-align:center">{_row[_cn]}</td>'
            f'<td style="color:#6b7280;font-size:12px">{_row[_cno]}</td></tr>'
        )

    _kw_html = f"""<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent}}
.kwt{{width:100%;border-collapse:collapse;font-size:13px;color:#111827;font-family:sans-serif}}
.kwt th{{background:#f3f4f6;padding:9px 10px;text-align:left;color:#374151;font-weight:600;border-bottom:2px solid #e5e7eb;white-space:nowrap}}
.kwt td{{padding:8px 10px;border-bottom:1px solid #e5e7eb;vertical-align:top}}
.kwt tr:hover td{{background:#f9fafb}}
.cp{{cursor:pointer;color:#0064D2}}
.cp:hover{{color:#0050a8;text-decoration:underline dotted;text-underline-offset:3px}}
.cp.ok{{color:#16a34a!important}}
#toast{{position:fixed;bottom:18px;right:18px;background:#16a34a;color:#fff;
        padding:6px 14px;border-radius:6px;font-size:12px;
        opacity:0;transition:opacity .2s;z-index:9999;pointer-events:none}}
#toast.show{{opacity:1}}
</style>
<div id="toast"></div>
<table class="kwt">
<thead><tr>
<th>{_ck}</th><th>{_cc}</th><th>{_cm}</th>
<th>{_cs}</th><th>{_cn}</th><th>{_cno}</th>
</tr></thead>
<tbody>{_rows_html}</tbody>
</table>
<script>
function cpKw(el){{
  var t=el.innerText.trim();
  var done=function(){{
    el.classList.add('ok');
    var d=document.getElementById('toast');
    d.innerText='✓ 已复制: '+t;
    d.classList.add('show');
    setTimeout(function(){{d.classList.remove('show');el.classList.remove('ok')}},1400);
  }};
  if(navigator.clipboard){{
    navigator.clipboard.writeText(t).then(done).catch(function(){{fallback(t,done)}});
  }}else{{fallback(t,done);}}
}}
function fallback(t,cb){{
  var ta=document.createElement('textarea');
  ta.value=t;ta.style.position='fixed';ta.style.opacity='0';
  document.body.appendChild(ta);ta.select();
  document.execCommand('copy');document.body.removeChild(ta);cb();
}}
</script>"""

    _tbl_height = min(50 + len(kw_df) * 42, 600)
    _components.html(_kw_html, height=_tbl_height, scrolling=False)

    _csv_bytes = kw_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        '⬇ 下载关键词 CSV',
        _csv_bytes,
        file_name=f'{seller_id}_keywords.csv',
        mime='text/csv',
    )

# ── Row 3: PLG Groups ──
st.markdown("---")
st.subheader(T['plg_section'])
st.caption(T['plg_caption'])

plg_df = get_plg_groups(store['prices'], seller_id, T=T)
if not plg_df.empty:
    st.dataframe(plg_df, use_container_width=True)
else:
    st.info(T['plg_no_data'])
