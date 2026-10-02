import base64
import html
import mimetypes
import os
import random
import re
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

from agent import generate_itinerary
from image_utils import get_destination_image

st.set_page_config(page_title="WanderAI", page_icon="🧳", layout="wide", initial_sidebar_state="collapsed")

# =====================================================================
#  CONFIG
# =====================================================================
PAGES = ["Plan a Trip", "Explore Destinations", "About Project"]
CURRENCIES = {"₹ INR": "₹", "$ USD": "$", "€ EUR": "€"}
INTEREST_OPTIONS = [
    "Historical monuments", "Nature", "Beaches", "Food", "Adventure",
    "Temples & spiritual", "Museums & art", "Shopping", "Nightlife", "Photography",
]
POPULAR = ["Delhi", "Jaipur", "Goa", "Paris", "Dubai", "Agra"]
SURPRISE = ["Delhi", "Jaipur", "Agra", "Mumbai", "Goa", "Paris", "Rome", "Dubai", "London", "New York"]
PACKING = [
    "Passport / ID", "Tickets & bookings", "Phone charger", "Power bank", "Comfortable shoes",
    "Sunscreen", "Water bottle", "Medicines", "Weather-appropriate clothes", "Cash & cards",
]
# (place name for photo, location label, region, city to plan for)
PLACES = [
    ("Taj Mahal", "Agra, India", "Asia", "Agra"),
    ("Amber Fort", "Jaipur, India", "Asia", "Jaipur"),
    ("Gateway of India", "Mumbai, India", "Asia", "Mumbai"),
    ("Golden Temple", "Amritsar, India", "Asia", "Amritsar"),
    ("Great Wall of China", "Beijing, China", "Asia", "Beijing"),
    ("Eiffel Tower", "Paris, France", "Europe", "Paris"),
    ("Colosseum", "Rome, Italy", "Europe", "Rome"),
    ("Santorini", "Greece", "Europe", "Santorini"),
    ("Burj Khalifa", "Dubai, UAE", "Middle East", "Dubai"),
    ("Machu Picchu", "Cusco, Peru", "Americas", "Cusco"),
    ("Statue of Liberty", "New York, USA", "Americas", "New York"),
]
# every city the planner already knows about (used for the destination suggestions)
DESTINATIONS = sorted(set(POPULAR) | set(SURPRISE) | {p[3] for p in PLACES})


def unsplash(photo_id, width=1200):
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w={width}&q=80"


# Curated Unsplash photos, used as the second layer behind the live photo (and as a graceful fallback).
PLACE_FALLBACK = {
    "Taj Mahal": unsplash("photo-1564507592333-c60657eea523", 900),
    "Amber Fort": unsplash("photo-1477587458883-47145ed94245", 900),
    "Gateway of India": unsplash("photo-1570168007204-dfb528c6958f", 900),
    "Golden Temple": unsplash("photo-1514222134-b57cbb8ce073", 900),
    "Great Wall of China": unsplash("photo-1508804185872-d7badad00f7d", 900),
    "Eiffel Tower": unsplash("photo-1502602898657-3e91760cbb34", 900),
    "Colosseum": unsplash("photo-1552832230-c0197dd311b5", 900),
    "Santorini": unsplash("photo-1570077188670-e3a8d69ac5ff", 900),
    "Burj Khalifa": unsplash("photo-1512453979798-5ea266f8880c", 900),
    "Machu Picchu": unsplash("photo-1587595431973-160d0d94add1", 900),
    "Statue of Liberty": unsplash("photo-1496442226666-8d4d0e62e6e9", 900),
}
GENERIC_PHOTO = unsplash("photo-1469474968028-56623f02e42e", 1000)
HERO_PHOTOS = {
    "full": [unsplash("photo-1464822759023-fed622ff2c3b", 2000), unsplash("photo-1506905925346-21bda4d32df4", 2000)],
    "explore": [unsplash("photo-1507525428034-b723cf961d3e", 2000), unsplash("photo-1469474968028-56623f02e42e", 2000)],
    "about": [unsplash("photo-1488646953014-85cb44e25828", 2000), unsplash("photo-1506905925346-21bda4d32df4", 2000)],
}
SOFT_SKY = "linear-gradient(135deg,#bcd9e8 0%,#e6f1f7 100%)"

# =====================================================================
#  SESSION STATE
# =====================================================================
DEFAULTS = {
    "page": "Plan a Trip", "destination": "", "days": 3, "currency": "₹ INR", "amount": 10000,
    "style": "Comfort", "interests_sel": ["Historical monuments"], "custom_interest": "",
    "trip": None, "history": [], "_scroll": False,
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# keep form values alive when a page (and its widgets) is not on screen
for k in ["destination", "days", "currency", "amount", "style", "interests_sel", "custom_interest"]:
    st.session_state[k] = st.session_state[k]


def set_destination(name):
    st.session_state.destination = name


def surprise():
    st.session_state.destination = random.choice(SURPRISE)


def go_plan(city):
    st.session_state.destination = city
    st.session_state.page = "Plan a Trip"
    st.session_state["_scroll"] = True


def open_trip(i):
    st.session_state.trip = st.session_state.history[i]
    st.session_state.page = "Plan a Trip"
    st.session_state["_scroll"] = True


def start_planning():
    st.session_state.page = "Plan a Trip"


# =====================================================================
#  DESIGN SYSTEM  (Quicksand + sky-blue / deep-teal palette from the reference)
# =====================================================================
def _svg_uri(inner, stroke="#1b6288", fill="none"):
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='{fill}' stroke='{stroke}' "
           f"stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>{inner}</svg>")
    return "data:image/svg+xml," + quote(svg, safe="")


ICONS = {
    "pin": _svg_uri("<path d='M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z'/><circle cx='12' cy='10' r='2.5'/>"),
    "calendar": _svg_uri("<rect x='3.5' y='5' width='17' height='15.5' rx='2.5'/><path d='M3.5 10h17M8 3v4M16 3v4'/>"),
    "wallet": _svg_uri("<path d='M4 7.5A2.5 2.5 0 0 1 6.5 5H19v3M4 7.5V17a2.5 2.5 0 0 0 2.5 2.5H20V8H6.5A2.5 2.5 0 0 1 4 7.5z'/><circle cx='16.5' cy='13.5' r='1'/>"),
    "compass": _svg_uri("<circle cx='12' cy='12' r='9'/><path d='M15.5 8.5l-2 5-5 2 2-5z'/>"),
    "logo": _svg_uri("<path d='M2 19L9 7l4 6 3-4 6 10z'/><circle cx='17.5' cy='5.5' r='1.6'/>", stroke="#1b6288", fill="#1b6288"),
}
ICON_CSS = "".join(f'.ico-{name}{{background-image:url("{uri}");}}' for name, uri in ICONS.items())


def safe_url(url):
    return quote(str(url), safe=":/?&=%#@+,;~!*()-._")


def to_src(img):
    """Turn whatever the image helper returns (URL, local path or bytes) into something CSS can load."""
    try:
        if isinstance(img, bytes):
            return "data:image/jpeg;base64," + base64.b64encode(img).decode()
        if isinstance(img, str) and img.strip():
            img = img.strip()
            if img.startswith(("http://", "https://", "data:")):
                return img
            if os.path.isfile(img):
                mime = mimetypes.guess_type(img)[0] or "image/jpeg"
                with open(img, "rb") as fh:
                    return f"data:{mime};base64," + base64.b64encode(fh.read()).decode()
    except Exception:
        pass
    return ""


def bg_style(*urls):
    """Layered CSS background: first image that loads wins, then a soft sky gradient."""
    layers = [f"url('{safe_url(u)}')" for u in urls if u]
    layers.append(SOFT_SKY)
    return html.escape("background-image:" + ",".join(layers), quote=False)


@st.cache_data(show_spinner=False, ttl=3600)
def cached_image(name):
    try:
        return to_src(get_destination_image(name))
    except Exception:
        return ""


def hero_bg(kind):
    top = "rgba(255,255,255,.66)" if kind == "full" else "rgba(255,255,255,.74)"
    mid = "rgba(255,255,255,.14)" if kind == "full" else "rgba(255,255,255,.38)"
    layers = [f"linear-gradient(180deg,{top} 0%,{mid} 55%,rgba(14,42,59,.10) 100%)"]
    layers += [f"url('{u}')" for u in HERO_PHOTOS[kind]]
    layers.append("linear-gradient(180deg,#d4e8f3,#eef6fa)")
    return ",".join(layers)


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&display=swap');
:root{--ink:#0e2a3b;--brand:#1b6288;--sky:#4a9fcb;--sky-d:#3688b5;--mist:#f2f8fb;--mist2:#e3f0f7;--line:#d5e6ef;--muted:#62808f;
--shadow:0 12px 40px rgba(14,42,59,.10);--shadow-s:0 4px 20px rgba(14,42,59,.08);}
html{color-scheme:light;scroll-behavior:smooth;}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"],#MainMenu,footer{display:none !important;}
.stApp{background:#fff;}
.block-container,[data-testid="stMainBlockContainer"]{max-width:100% !important;padding:0 !important;}
.stApp,.stApp p,.stApp li,.stApp label,.stApp button,.stApp input,.stApp textarea,.stApp h1,.stApp h2,.stApp h3,.stApp h4,
[data-baseweb]{font-family:'Quicksand',system-ui,-apple-system,'Segoe UI',sans-serif !important;}
.stApp,.stApp p,.stApp li,.stApp label,.stApp h1,.stApp h2,.stApp h3,.stApp h4{color:var(--ink);}
.stApp [data-testid="stMarkdownContainer"] p{margin:0;}
[data-testid="stVerticalBlock"]{gap:1rem;}
__ICONS__
.ico{display:inline-block;width:16px;height:16px;background-size:contain;background-repeat:no-repeat;background-position:center;flex:0 0 auto;}
/* ---------- hero + navigation ---------- */
[class*="st-key-hero_"]{position:relative;padding:26px 7vw 64px;background-size:cover;background-position:center;gap:.6rem !important;}
.st-key-hero_full{min-height:640px;background-image:__HERO_FULL__;}
.st-key-hero_explore{min-height:330px;background-image:__HERO_EXPLORE__;}
.st-key-hero_about{min-height:330px;background-image:__HERO_ABOUT__;}
.logo{display:flex;align-items:center;gap:.6rem;height:48px;}
.logo .ico{width:36px;height:36px;}
.logo-word{font-size:1.45rem;font-weight:700;color:var(--brand);letter-spacing:-.01em;}
.logo-word small{font-weight:500;color:var(--sky);font-size:.8rem;margin-left:.35rem;letter-spacing:.12em;}
.st-key-nav [role="radiogroup"]{justify-content:flex-end;gap:.2rem;flex-wrap:wrap;}
.st-key-hero_full .stButton,.st-key-hero_explore .stButton,.st-key-hero_about .stButton{display:flex;justify-content:flex-end;}
.hero-copy{text-align:center;margin:3.6rem auto 0;max-width:900px;}
.hero-copy h1{font-size:clamp(2.1rem,5vw,3.5rem) !important;font-weight:400 !important;line-height:1.15 !important;
letter-spacing:-.01em;margin:0 !important;padding:0 !important;color:var(--ink);}
.hero-copy h1 span{color:var(--brand);}
.hero-copy p{font-size:clamp(1.05rem,2.2vw,1.55rem) !important;font-weight:400;margin-top:1rem !important;color:var(--ink);}
.hero-slim{margin-top:1.6rem;}
/* ---------- search bar ---------- */
.st-key-searchbar{background:#fff;border-radius:16px;padding:16px 20px 14px;box-shadow:var(--shadow);
max-width:940px;width:100%;margin:2.2rem auto 0;gap:.5rem !important;}
.st-key-searchbar [data-testid="stHorizontalBlock"]{align-items:flex-end;gap:.4rem;}
.st-key-searchbar [data-testid="stColumn"]:not(:first-child),.st-key-searchbar [data-testid="column"]:not(:first-child){border-left:1px solid var(--line);padding-left:16px;}
.st-key-searchbar [data-baseweb="input"],.st-key-searchbar [data-baseweb="base-input"],.st-key-searchbar [data-testid="stTextInputRootElement"],
.st-key-searchbar [data-testid="stNumberInputContainer"],.st-key-searchbar [data-testid="stTextInput"] div,.st-key-searchbar [data-testid="stNumberInput"] div{
background:#fff !important;background-color:#fff !important;box-shadow:none !important;}
.st-key-searchbar [data-baseweb="input"],.st-key-searchbar [data-testid="stTextInputRootElement"],.st-key-searchbar [data-testid="stNumberInputContainer"]{
border:1px solid var(--line) !important;border-radius:8px !important;}
.st-key-searchbar [data-baseweb="base-input"]{border:none !important;}
.st-key-searchbar input{font-size:1rem;font-weight:600;padding-left:.2rem !important;color:var(--ink) !important;-webkit-text-fill-color:var(--ink) !important;}
.st-key-searchbar [data-baseweb="input"]{min-height:44px;}
.st-key-searchbar [data-testid="stNumberInputContainer"] button,.st-key-searchbar [data-testid="InputInstructions"]{display:none !important;}
.fld{display:flex;align-items:center;gap:.45rem;font-size:.72rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin:0 0 .1rem .2rem;}
.chip-label{font-size:.76rem;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:var(--brand);opacity:.85;}
[class*="st-key-chips"],.st-key-recent{flex-direction:row !important;flex-wrap:wrap;justify-content:center;align-items:center;gap:.5rem !important;}
[class*="st-key-chips"]>*,.st-key-recent>*{width:auto !important;flex:0 0 auto !important;}
[class*="st-key-chips"] .stButton,.st-key-recent .stButton{width:auto;}
[class*="st-key-chips"] .stButton>button{background:rgba(255,255,255,.88);border:1px solid #fff;color:var(--brand);padding:.3rem 1rem;
min-height:0;font-size:.9rem;font-weight:600;box-shadow:0 2px 12px rgba(14,42,59,.08);}
[class*="st-key-chips"] .stButton>button:hover{background:#fff;color:var(--sky-d);}
.st-key-recent{justify-content:flex-start;margin-top:1.6rem;}
.st-key-recent .stButton>button{padding:.3rem 1rem;min-height:0;font-size:.9rem;font-weight:600;color:var(--sky-d);border-color:var(--sky);}
/* ---------- buttons ---------- */
.stButton,.stDownloadButton{width:100%;}
.stButton>button,.stDownloadButton>button{width:100%;border-radius:8px;border:1px solid #cfdbe3;background:#fff;color:var(--brand);
font-weight:600;font-size:.98rem;padding:.55rem 1.2rem;min-height:46px;transition:all .22s ease;box-shadow:none;}
.stButton>button p,.stDownloadButton>button p{color:inherit;}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--sky);color:var(--sky-d);transform:translateY(-1px);box-shadow:0 6px 16px rgba(74,159,203,.18);}
.stButton>button[kind="primary"],button[data-testid="stBaseButton-primary"]{background:var(--sky);border:none;color:#fff;font-weight:700;}
.stButton>button[kind="primary"]:hover,button[data-testid="stBaseButton-primary"]:hover{background:var(--sky-d);color:#fff;box-shadow:0 8px 20px rgba(54,136,181,.3);}
.stButton>button[kind="primary"] p,button[data-testid="stBaseButton-primary"] p{color:#fff;}
.st-key-cta .stButton>button{width:auto;min-width:150px;}
/* ---------- inputs ---------- */
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"]>div,[data-baseweb="textarea"],[data-testid="stTextInputRootElement"],
[data-testid="stNumberInputContainer"],[data-testid="stTextArea"] div{background:#fff !important;background-color:#fff !important;border-color:var(--line) !important;border-radius:8px !important;}
input,textarea,[data-baseweb="input"] input,[data-baseweb="base-input"] input,[data-testid="stNumberInputContainer"] input,
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea{
color:var(--ink) !important;-webkit-text-fill-color:var(--ink) !important;caret-color:var(--brand) !important;
background:#fff !important;opacity:1 !important;}
input::placeholder,textarea::placeholder{color:#9bb2bf !important;-webkit-text-fill-color:#9bb2bf !important;opacity:1 !important;}
input:-webkit-autofill{-webkit-text-fill-color:var(--ink) !important;box-shadow:0 0 0 40px #fff inset !important;}
[data-baseweb="popover"] ul,[data-baseweb="popover"] li,[data-baseweb="menu"]{background:#fff !important;color:var(--ink) !important;}
[data-baseweb="popover"] li:hover{background:var(--mist2) !important;}
[data-baseweb="select"] *{color:var(--ink);}
[data-baseweb="tag"]{background:var(--mist2) !important;border-radius:6px !important;}
[data-baseweb="tag"] span{color:var(--brand) !important;font-weight:600;}
[data-testid="stWidgetLabel"] p{font-size:.76rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted) !important;}
/* ---------- tabs / segmented radios (the "Homes / Rooms / Experiences" style) ---------- */
[data-testid="stRadio"] [role="radiogroup"]{gap:.4rem;flex-wrap:wrap;}
label[data-baseweb="radio"]{padding:.5rem 1.15rem;border-radius:8px;cursor:pointer;margin:0;transition:background .2s ease;background:transparent;}
label[data-baseweb="radio"]>div:first-child{display:none !important;}
label[data-baseweb="radio"] p{color:var(--sky-d);font-weight:600;font-size:.98rem;}
label[data-baseweb="radio"]:hover{background:var(--mist2);}
label[data-baseweb="radio"]:has(input:checked){background:var(--sky);}
label[data-baseweb="radio"]:has(input:checked) p{color:#fff;}
.st-key-nav label[data-baseweb="radio"]{padding:.5rem .9rem;border-radius:0;}
.st-key-nav label[data-baseweb="radio"] p{color:var(--brand);font-weight:500;}
.st-key-nav label[data-baseweb="radio"]:hover{background:transparent;}
.st-key-nav label[data-baseweb="radio"]:has(input:checked){background:transparent;box-shadow:inset 0 -2px 0 var(--sky);}
.st-key-nav label[data-baseweb="radio"]:has(input:checked) p{color:var(--ink);font-weight:700;}
button[data-baseweb="tab"]{font-weight:600;font-size:1rem;color:var(--muted);padding:.9rem 1.4rem;}
button[data-baseweb="tab"] p{color:inherit;}
button[data-baseweb="tab"][aria-selected="true"]{color:var(--sky-d);}
[data-baseweb="tab-highlight"]{background:var(--sky) !important;height:3px;}
[data-baseweb="tab-border"]{background:var(--line) !important;}
[data-testid="stAlert"]{border-radius:10px;}
[data-testid="stStatus"],[data-testid="stExpander"]{border:1px solid var(--line);border-radius:12px;background:var(--mist);}
[data-testid="stProgress"]>div>div>div>div{background:var(--sky);}
/* ---------- layout ---------- */
.st-key-wrap{max-width:1200px;width:100%;margin:0 auto;padding:0 2rem;}
.sec-head{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin:3.4rem 0 .6rem;animation:fadeUp .6s ease both;}
.sec-head h2{margin:0 !important;padding:0 !important;font-size:clamp(1.8rem,3.4vw,2.7rem) !important;font-weight:400 !important;letter-spacing:-.01em;line-height:1.15;}
.sec-sub{color:var(--muted) !important;font-size:1.02rem;margin-top:.5rem !important;max-width:520px;}
.pill-out{display:inline-block;border:1px solid var(--sky);color:var(--sky-d);border-radius:8px;padding:.18rem .85rem;font-size:.86rem;font-weight:600;margin-top:.7rem;}
.tag{display:inline-block;margin:.55rem .35rem 0 0;border:1px solid var(--sky);color:var(--sky-d);border-radius:8px;padding:.1rem .7rem;font-size:.8rem;font-weight:600;}
.panel-head h3{margin:0 !important;padding:0 !important;font-size:1.7rem !important;font-weight:500 !important;}
.panel-head p{color:var(--muted) !important;margin-top:.3rem !important;}
.st-key-panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:28px 30px 24px;box-shadow:var(--shadow-s);margin-top:2.2rem;}
.st-key-filters{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 22px;box-shadow:var(--shadow-s);margin-top:2.2rem;}
/* ---------- destination cards ---------- */
[class*="st-key-grid_"] [data-testid="stHorizontalBlock"]{flex-wrap:wrap;gap:1.4rem;}
[class*="st-key-grid_"] [data-testid="stColumn"],[class*="st-key-grid_"] [data-testid="column"]{min-width:230px;flex:1 1 230px;}
[class*="st-key-dest_"]{background:#fff;border-radius:12px;box-shadow:var(--shadow-s);overflow:hidden;padding:0 0 16px !important;gap:.3rem !important;
transition:transform .3s ease,box-shadow .3s ease;animation:fadeUp .6s ease both;}
[class*="st-key-dest_"]:hover{transform:translateY(-5px);box-shadow:var(--shadow);}
[class*="st-key-dest_"] .stButton{padding:0 18px;}
.dest-imgwrap{overflow:hidden;height:210px;background:var(--mist2);}
.dest-img{width:100%;height:100%;background-size:cover;background-position:center;transition:transform .6s ease;}
[class*="st-key-dest_"]:hover .dest-img{transform:scale(1.06);}
.dest-info{padding:16px 18px 6px;}
.dest-info h4{margin:0 !important;padding:0 !important;font-size:1.2rem !important;font-weight:600 !important;}
.dest-info p{color:var(--muted) !important;font-size:.93rem;margin-top:.15rem !important;}
/* ---------- results ---------- */
.trip-banner{height:340px;border-radius:14px;background-size:cover;background-position:center;position:relative;overflow:hidden;margin-top:2.4rem;
box-shadow:var(--shadow);animation:fadeUp .6s ease both;}
.trip-banner:after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(14,42,59,0) 35%,rgba(14,42,59,.72) 100%);}
.trip-banner-in{position:absolute;left:32px;right:32px;bottom:26px;z-index:2;}
.trip-banner-in .eyebrow{color:#fff !important;opacity:.85;font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;font-weight:700;}
.trip-banner-in h2{color:#fff !important;margin:.25rem 0 0 !important;padding:0 !important;font-size:clamp(2rem,4.5vw,3.1rem) !important;font-weight:400 !important;}
.trip-banner-in p{color:#fff !important;opacity:.92;margin-top:.3rem !important;font-size:1.05rem;}
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-top:1rem;}
.stat{background:#fff;border:1px solid var(--line);border-radius:12px;padding:1rem 1.2rem;box-shadow:var(--shadow-s);animation:fadeUp .6s ease both;}
.stat span{display:block;font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);}
.stat b{display:block;font-size:1.55rem;font-weight:500;color:var(--ink);margin-top:.15rem;}
.day{display:grid;grid-template-columns:42px 1fr;gap:0 20px;animation:fadeUp .6s ease both;}
.rail{display:flex;flex-direction:column;align-items:center;}
.rail .dot{width:40px;height:40px;border-radius:50%;background:var(--sky);color:#fff !important;font-weight:700;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 14px rgba(74,159,203,.38);flex:0 0 auto;}
.rail:after{content:'';flex:1;width:2px;background:var(--line);margin:6px 0;}
.day-body{background:#fff;border:1px solid var(--line);border-radius:12px;padding:22px 26px 12px;box-shadow:var(--shadow-s);margin-bottom:18px;
transition:box-shadow .3s ease,transform .3s ease;}
.day-body:hover{box-shadow:var(--shadow);transform:translateY(-2px);}
.day-head{display:flex;justify-content:space-between;align-items:center;gap:1rem;border-bottom:1px solid var(--line);padding-bottom:14px;}
.day-head h3{margin:0 !important;padding:0 !important;font-size:1.6rem !important;font-weight:500 !important;}
.day-head .pill-out{margin-top:0;}
.acts{list-style:none;margin:0;padding:0;}
.act{display:flex;gap:16px;padding:16px 0;border-bottom:1px dashed var(--line);}
.act:last-child{border-bottom:none;}
.act-ix{flex:0 0 auto;width:36px;height:36px;border-radius:8px;background:var(--mist2);color:var(--sky-d) !important;font-size:.82rem;font-weight:700;display:flex;align-items:center;justify-content:center;}
.act-t{font-weight:700;font-size:1.04rem;color:var(--ink);margin-bottom:.15rem;}
.act-d{color:var(--muted) !important;line-height:1.65;font-size:.97rem;}
.act-d.solo{color:var(--ink) !important;}
/* ---------- empty / error / about / footer ---------- */
.empty{border:1.5px dashed #bcd6e4;border-radius:14px;background:var(--mist);text-align:center;padding:3.2rem 1.5rem;margin-top:2.4rem;animation:fadeUp .6s ease both;}
.empty .ico{width:34px;height:34px;}
.empty .ring{width:76px;height:76px;border-radius:50%;background:#fff;box-shadow:var(--shadow-s);display:inline-flex;align-items:center;justify-content:center;}
.empty h3{margin:1.1rem 0 .3rem !important;padding:0 !important;font-size:1.6rem !important;font-weight:500 !important;}
.empty p{color:var(--muted) !important;max-width:520px;margin:0 auto !important;}
.err{border:1px solid #f0c9c4;background:#fff7f6;border-radius:12px;padding:1.2rem 1.5rem;margin-top:1rem;}
.err h4{margin:0 0 .3rem 0 !important;padding:0 !important;color:#9b2c20 !important;font-size:1.1rem !important;}
.err p{color:#6d3a34 !important;}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:1.4rem;margin-top:1.6rem;}
.step{background:#fff;border:1px solid var(--line);border-radius:14px;padding:1.6rem;box-shadow:var(--shadow-s);animation:fadeUp .6s ease both;}
.step b.n{display:inline-flex;width:38px;height:38px;border-radius:50%;background:var(--sky);color:#fff !important;align-items:center;justify-content:center;font-weight:700;}
.step h4{margin:1rem 0 .3rem !important;padding:0 !important;font-size:1.25rem !important;font-weight:600 !important;}
.step p{color:var(--muted) !important;line-height:1.65;}
.note{margin-top:2rem;background:var(--mist);border-left:4px solid var(--sky);border-radius:10px;padding:1.1rem 1.4rem;color:var(--ink);}
.footer{background:var(--mist);margin-top:4.5rem;padding:2.4rem 7vw;display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;}
.footer p{color:var(--muted) !important;font-size:.92rem;}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:none;}}
/* ---------- responsive ---------- */
@media (max-width:900px){.stat-grid{grid-template-columns:1fr 1fr;}.steps{grid-template-columns:1fr;}}
@media (max-width:768px){
[class*="st-key-hero_"]{padding:18px 5vw 40px;}
.st-key-hero_full{min-height:0;}
.hero-copy{margin-top:2rem;}
.st-key-searchbar{padding:14px;}
.st-key-searchbar [data-testid="stColumn"],.st-key-searchbar [data-testid="column"]{border-left:none !important;padding-left:0 !important;border-bottom:1px solid var(--line);padding-bottom:.6rem;}
.st-key-nav [role="radiogroup"]{justify-content:center;}
.st-key-wrap{padding:0 1.1rem;}
.trip-banner{height:240px;}
.trip-banner-in{left:20px;right:20px;bottom:18px;}
.day{grid-template-columns:34px 1fr;gap:0 12px;}
.rail .dot{width:34px;height:34px;}
.day-body{padding:16px 16px 6px;}
.footer{padding:2rem 5vw;}
}
</style>
"""
CSS = (CSS.replace("__ICONS__", ICON_CSS)
          .replace("__HERO_FULL__", hero_bg("full"))
          .replace("__HERO_EXPLORE__", hero_bg("explore"))
          .replace("__HERO_ABOUT__", hero_bg("about")))
st.markdown(CSS, unsafe_allow_html=True)

# =====================================================================
#  HELPERS
# =====================================================================
DAY_PATTERN = re.compile(r"(?:^|\n)\s*\**\s*Day\s*(\d+)\s*[:\-–]?\s*\**\s*:?", re.IGNORECASE)


def keyed(name):
    """A container carrying a CSS hook (older Streamlit versions fall back to a plain container)."""
    try:
        return st.container(key=name)
    except TypeError:
        return st.container()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def clean_lines(text):
    lines = []
    for line in text.split("\n"):
        line = line.replace("**", "").strip()
        line = re.sub(r"^(?:[-*•]|\d+\.)\s+", "", line)
        if len(line) > 2 and not re.fullmatch(r"[\W_]+", line):
            lines.append(line)
    return lines


def parse_itinerary_to_days(text):
    matches = list(DAY_PATTERN.finditer(text))
    if not matches:
        return [("Itinerary", clean_lines(text))]
    days = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        days.append((f"Day {m.group(1)}", clean_lines(text[m.end():end])))
    return days


def render_line(line, n=1):
    idx = line.find(":")
    if 0 < idx < 50:
        title, desc = line[:idx].strip(), line[idx + 1:].strip()
    else:
        title, desc = "", line
    head = f'<div class="act-t">{html.escape(title)}</div>' if title else ""
    cls = "act-d" if title else "act-d solo"
    body = f'<div class="{cls}">{html.escape(desc)}</div>' if desc else ""
    return f'<li class="act"><span class="act-ix">{n:02d}</span><div>{head}{body}</div></li>'


def day_card(title, lines):
    num = re.search(r"\d+", title)
    badge = num.group(0) if num else "1"
    items = "".join(render_line(l, i) for i, l in enumerate(lines, 1))
    count = f"{len(lines)} {'activity' if len(lines) == 1 else 'activities'}"
    # single-line HTML: indented multi-line HTML is treated as a code block by markdown
    st.markdown(
        f'<div class="day"><div class="rail"><span class="dot">{html.escape(badge)}</span></div>'
        f'<div class="day-body"><div class="day-head"><h3>{html.escape(title)}</h3><span class="pill-out">{count}</span></div>'
        f'<ul class="acts">{items}</ul></div></div>',
        unsafe_allow_html=True)


def trip_as_text(t):
    out = [f"{t['destination'].title()} - {t['days']}-day trip", f"Budget: {t['budget']}", f"Interests: {t['interests']}", ""]
    for title, lines in parse_itinerary_to_days(t["raw"]):
        out.append(title)
        out += [f"  - {l}" for l in lines]
        out.append("")
    return "\n".join(out)


def run_generation(dest, days, currency, amount, style, interests_list):
    sym = CURRENCIES[currency]
    budget = f"{sym}{amount:,} ({style.lower()} style)"
    interests = ", ".join(interests_list)
    try:
        with st.status("Planning your trip...", expanded=True) as status:
            st.write("Finding places that match your interests")
            image = get_destination_image(dest)
            st.write("Drafting your day-by-day plan (this can take a minute)")
            raw = generate_itinerary(dest, days, budget, interests)
            status.update(label="Your trip is ready", state="complete", expanded=False)
    except Exception as e:
        st.markdown(
            f'<div class="err"><h4>We couldn\'t build that itinerary</h4>'
            f'<p>Couldn\'t generate the itinerary: {html.escape(str(e))}. Check that Ollama is running.</p></div>',
            unsafe_allow_html=True)
        return False
    trip = dict(destination=dest, days=days, currency=currency, amount=amount, style=style,
                interests_list=interests_list, budget=budget, interests=interests, image=image, raw=raw, sym=sym)
    st.session_state.trip = trip
    hist = [h for h in st.session_state.history if not (h["destination"] == dest and h["days"] == days)]
    st.session_state.history = ([trip] + hist)[:5]
    return True


def logo_html():
    return '<div class="logo"><i class="ico ico-logo"></i><span class="logo-word">WanderAI</span></div>'


def section_head(title, sub, count):
    st.markdown(
        f'<div class="sec-head"><div><h2>{html.escape(title)}</h2><span class="pill-out">{count}</span></div>'
        f'<p class="sec-sub">{html.escape(sub)}</p></div>', unsafe_allow_html=True)


def dest_card(prefix, name, location, reg, city):
    img = cached_image(name)
    style = bg_style(img, PLACE_FALLBACK.get(name), GENERIC_PHOTO)
    with keyed(f"dest_{prefix}_{slug(name)}"):
        st.markdown(
            f'<div class="dest-imgwrap"><div class="dest-img" style="{style}"></div></div>'
            f'<div class="dest-info"><h4>{html.escape(name)}</h4><p>{html.escape(location)}</p>'
            f'<span class="tag">{html.escape(reg)}</span></div>', unsafe_allow_html=True)
        st.button(f"Plan a trip to {city}", key=f"plan_{prefix}_{slug(name)}", on_click=go_plan, args=(city,))


def dest_grid(places, ncols, prefix):
    for r in range(0, len(places), ncols):
        with keyed(f"grid_{prefix}_{r}"):
            cols = st.columns(ncols)
            for col, p in zip(cols, places[r:r + ncols]):
                with col:
                    dest_card(prefix, *p)


def footer():
    st.markdown(
        f'<div class="footer">{logo_html()}'
        '<p>Your AI companion for every journey.</p></div>',
        unsafe_allow_html=True)


def scroll_to_top():
    if st.session_state.get("_scroll"):
        st.session_state["_scroll"] = False
        try:
            components.html(
                "<script>const d=window.parent.document;"
                "['[data-testid=\"stMain\"]','section.main','[data-testid=\"stAppViewContainer\"]'].forEach(function(s){"
                "const e=d.querySelector(s);if(e){e.scrollTo({top:0,behavior:'smooth'});}});</script>", height=0)
        except Exception:
            pass


# =====================================================================
#  HEADER / HERO  (logo + navigation live inside the hero photo, like the reference)
# =====================================================================
def render_hero(page):
    full = page == "Plan a Trip"
    kind = "full" if full else ("explore" if page == "Explore Destinations" else "about")
    go = False
    with keyed(f"hero_{kind}"):
        c1, c2, c3 = st.columns([1.4, 3.4, 1.3])
        c1.markdown(logo_html(), unsafe_allow_html=True)
        with c2:
            with keyed("nav"):
                st.radio("Navigate", PAGES, key="page", horizontal=True, label_visibility="collapsed")
        with c3:
            if not full:
                with keyed("cta"):
                    st.button("Start planning", key="cta_btn", type="primary", on_click=start_planning)

        if full:
            st.markdown(
                '<div class="hero-copy"><h1>Plan your next <span>unforgettable</span> escape</h1>'
                '<p>Tell us where — our AI builds your day-by-day itinerary</p></div>', unsafe_allow_html=True)
            s = st.session_state
            with keyed("searchbar"):
                a, b, c, d = st.columns([2.4, 1, 1.4, 1.1])
                with a:
                    st.markdown('<div class="fld"><i class="ico ico-pin"></i>Destination</div>', unsafe_allow_html=True)
                    st.text_input("Destination", key="destination", placeholder="Search a city, e.g. Jaipur",
                                  label_visibility="collapsed")
                with b:
                    st.markdown('<div class="fld"><i class="ico ico-calendar"></i>Days</div>', unsafe_allow_html=True)
                    st.number_input("Number of days", min_value=1, max_value=15, step=1, key="days",
                                    label_visibility="collapsed")
                with c:
                    st.markdown(f'<div class="fld"><i class="ico ico-wallet"></i>Budget ({CURRENCIES[s.currency]})</div>',
                                unsafe_allow_html=True)
                    st.number_input("Total budget", min_value=500, step=500, key="amount", label_visibility="collapsed")
                with d:
                    st.markdown('<div class="fld">&nbsp;</div>', unsafe_allow_html=True)
                    go = st.button("Plan my trip", key="go", type="primary")

            q = s.destination.strip()
            matches = [m for m in DESTINATIONS if q and q.lower() in m.lower() and m.lower() != q.lower()][:6]
            if matches:
                with keyed("chips_sug"):
                    st.markdown('<span class="chip-label">Suggestions</span>', unsafe_allow_html=True)
                    for m in matches:
                        st.button(m, key=f"sug_{slug(m)}", on_click=set_destination, args=(m,))
            with keyed("chips_pop"):
                st.markdown('<span class="chip-label">Popular</span>', unsafe_allow_html=True)
                for name in POPULAR:
                    st.button(name, key=f"chip_{name}", on_click=set_destination, args=(name,))
                st.button("Surprise me", key="surprise_btn", on_click=surprise)
        else:
            if page == "Explore Destinations":
                title, sub = "Explore <span>destinations</span>", "Find inspiration across India and the world, then plan it in one click"
            else:
                title, sub = "About this <span>project</span>", "Retrieval, reasoning and presentation — a local AI travel assistant"
            st.markdown(f'<div class="hero-copy hero-slim"><h1>{title}</h1><p>{sub}</p></div>', unsafe_allow_html=True)
    return go


# =====================================================================
#  PAGE: PLAN A TRIP
# =====================================================================
def render_trip(trip):
    img = to_src(trip.get("image"))
    style = bg_style(img, PLACE_FALLBACK.get(trip["destination"].title()), GENERIC_PHOTO)
    tags = "".join(f'<span class="tag">{html.escape(i)}</span>' for i in trip["interests_list"])
    st.markdown(
        f'<div class="trip-banner" style="{style}"><div class="trip-banner-in"><span class="eyebrow">Your itinerary</span>'
        f'<h2>{html.escape(trip["destination"].title())}</h2>'
        f'<p>{trip["days"]}-day trip &middot; {html.escape(trip["budget"])}</p></div></div>'
        f'<div class="stat-grid">'
        f'<div class="stat"><span>Duration</span><b>{trip["days"]} days</b></div>'
        f'<div class="stat"><span>Budget</span><b>{html.escape(trip["sym"])}{trip["amount"]:,}</b></div>'
        f'<div class="stat"><span>Per day</span><b>{html.escape(trip["sym"])}{trip["amount"] / trip["days"]:,.0f}</b></div>'
        f'<div class="stat"><span>Interests</span><b>{len(trip["interests_list"])}</b></div></div>'
        f'<div>{tags}</div>', unsafe_allow_html=True)

    tab_plan, tab_pack, tab_export = st.tabs(["Itinerary", "Packing list", "Export"])
    days = parse_itinerary_to_days(trip["raw"])

    with tab_plan:
        c1, c2 = st.columns([2, 1])
        with c1:
            view = st.radio("View", ["All days", "Single day"], horizontal=True, key="view_mode")
        with c2:
            regen = st.button("Regenerate", key="regen")
        if view == "Single day" and len(days) > 1:
            options = [d[0] for d in days]
            if st.session_state.get("day_pick") not in options:
                st.session_state.pop("day_pick", None)
            pick = st.select_slider("Day", options=options, key="day_pick")
            days = [d for d in days if d[0] == pick]
        for title, lines in days:
            day_card(title, lines)
        if regen:
            if run_generation(trip["destination"], trip["days"], trip["currency"], trip["amount"],
                              trip["style"], trip["interests_list"]):
                st.rerun()

    with tab_pack:
        st.caption("Tick items off as you pack.")
        cols = st.columns(2)
        done = 0
        for i, item in enumerate(PACKING):
            if cols[i % 2].checkbox(item, key=f"pack_{item}"):
                done += 1
        st.progress(done / len(PACKING), text=f"{done}/{len(PACKING)} packed")

    with tab_export:
        text = trip_as_text(trip)
        st.download_button("Download itinerary (.txt)", text,
                           file_name=f"{trip['destination'].lower().replace(' ', '_')}_itinerary.txt")
        st.text_area("Copy your itinerary", text, height=320)


def plan_page(go):
    s = st.session_state
    with keyed("wrap"):
        if s.history:
            with keyed("recent"):
                st.markdown('<span class="chip-label">Recently planned</span>', unsafe_allow_html=True)
                for i, t in enumerate(s.history):
                    st.button(f"{t['destination'].title()} · {t['days']}d", key=f"hist_{i}", on_click=open_trip, args=(i,))

        with keyed("panel"):
            st.markdown('<div class="panel-head"><h3>Make it yours</h3>'
                        '<p>Tell us what you love and how you like to travel.</p></div>', unsafe_allow_html=True)
            left, right = st.columns([3, 2])
            with left:
                st.multiselect("Interests", INTEREST_OPTIONS, key="interests_sel")
                st.text_input("Anything else?", key="custom_interest", placeholder="e.g. street food, sunsets")
            with right:
                st.selectbox("Currency", list(CURRENCIES), key="currency")
                st.radio("Travel style", ["Budget", "Comfort", "Luxury"], key="style", horizontal=True)
                st.markdown(f'<span class="pill-out">≈ {CURRENCIES[s.currency]}{s.amount / max(s.days, 1):,.0f} per day</span>',
                            unsafe_allow_html=True)

        if go:
            dest = s.destination.strip()
            interests = list(s.interests_sel) + ([s.custom_interest.strip()] if s.custom_interest.strip() else [])
            if not dest:
                st.warning("Enter a destination or tap one of the quick picks.")
            elif not interests:
                st.warning("Pick at least one interest so the plan fits you.")
            else:
                run_generation(dest, s.days, s.currency, s.amount, s.style, interests)

        if s.trip:
            render_trip(s.trip)
        else:
            st.markdown(
                '<div class="empty"><span class="ring"><i class="ico ico-compass"></i></span>'
                '<h3>Your journey starts here</h3>'
                '<p>Choose a destination above and we\'ll build a day-by-day plan with places that match your interests.</p></div>',
                unsafe_allow_html=True)

        india = [p for p in PLACES if "India" in p[1]]
        world = [p for p in PLACES if "India" not in p[1]]
        section_head("Discover India", "Timeless heritage, vivid cities and spiritual landmarks.", f"{len(india)} destinations")
        dest_grid(india, 4, "in")
        section_head("Around the world", "Iconic destinations across Europe, the Middle East and the Americas.",
                     f"{len(world)} destinations")
        dest_grid(world, 4, "world")
    footer()


# =====================================================================
#  PAGE: EXPLORE
# =====================================================================
def explore_page():
    with keyed("wrap"):
        with keyed("filters"):
            c1, c2 = st.columns([2, 3])
            query = c1.text_input("Search", placeholder="Search places...", label_visibility="collapsed")
            region = c2.radio("Region", ["All", "Asia", "Europe", "Middle East", "Americas"],
                              horizontal=True, label_visibility="collapsed")

        shown = [p for p in PLACES
                 if (region == "All" or p[2] == region)
                 and query.lower() in f"{p[0]} {p[1]}".lower()]
        if not shown:
            st.markdown(
                '<div class="empty"><span class="ring"><i class="ico ico-compass"></i></span>'
                '<h3>No places match</h3><p>Try a different search or region.</p></div>', unsafe_allow_html=True)
        else:
            section_head("Places to visit", "Pick a landmark and we'll plan the whole trip around it.",
                         f"{len(shown)} destinations")
            dest_grid(shown, 3, "x")
    footer()


# =====================================================================
#  PAGE: ABOUT
# =====================================================================
def about_page():
    steps = [
        ("1", "Retrieve", "ChromaDB finds places that match your destination and interests (RAG)."),
        ("2", "Reason", "A local Ollama model arranges them into days that fit your budget."),
        ("3", "Present", "Streamlit shows the plan, with photos from the Wikipedia API."),
    ]
    cards = "".join(f'<div class="step"><b class="n">{n}</b><h4>{t}</h4><p>{d}</p></div>' for n, t, d in steps)
    stack = "".join(f'<span class="tag">{html.escape(t)}</span>'
                    for t in ["LangChain", "ChromaDB", "Ollama (llama3.2)", "Wikipedia API", "Streamlit"])
    with keyed("wrap"):
        st.markdown(
            '<div class="sec-head"><div><h2>How it works</h2></div>'
            '<p class="sec-sub">An AI travel planner that retrieves real places from a dataset and uses a local LLM '
            'to build a personalised, day-wise itinerary.</p></div>'
            f'<div class="steps">{cards}</div>'
            '<div class="sec-head"><div><h2>Tech stack</h2></div></div>'
            f'<div>{stack}</div>'
            '<div class="note">Built as part of an Agentic AI &amp; LLM coursework project.</div>',
            unsafe_allow_html=True)
    footer()


# =====================================================================
#  ROUTER
# =====================================================================
current_page = st.session_state.page
go_clicked = render_hero(current_page)
if current_page == "Plan a Trip":
    plan_page(go_clicked)
elif current_page == "Explore Destinations":
    explore_page()
else:
    about_page()
scroll_to_top()
