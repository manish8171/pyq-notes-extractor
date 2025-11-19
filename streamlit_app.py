import streamlit as st
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import re
from urllib.parse import quote
import time

st.set_page_config(page_title="AKTU PYQ Extractor", page_icon="📚")

# --- SCRAPING LOGIC ---
BASE_URL = "https://notesgallery.com"
USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
]
_ua_idx = 0

def make_session():
    global _ua_idx
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENTS[_ua_idx % len(USER_AGENTS)],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": BASE_URL + "/",
    })
    _ua_idx += 1
    return s

def fetch(url, session=None, retries=3):
    for attempt in range(retries):
        try:
            s = session or make_session()
            resp = s.get(url, timeout=15)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 403:
                time.sleep(1 + attempt)
            else:
                return None
        except requests.RequestException:
            time.sleep(1)
    return None

def seed_session(s):
    try:
        s.get(BASE_URL + "/", timeout=8)
    except:
        pass

def search_on_site(query):
    search_url = f"{BASE_URL}/?s={quote(query)}"
    s = make_session()
    seed_session(s)
    resp = fetch(search_url, session=s)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results, seen = [], set()

    for article in soup.find_all("article"):
        for tag in ["h2", "h1", "h3"]:
            h = article.find(tag)
            if h:
                a = h.find("a", href=True)
                if a and a["href"] not in seen and BASE_URL in a["href"]:
                    t = a.get_text(strip=True)
                    if t:
                        results.append({"title": t, "url": a["href"]})
                        seen.add(a["href"])
                break

    for div in soup.find_all(["div", "li"], class_=re.compile(r"post|entry|result", re.I)):
        a = div.find("a", href=True)
        if a and BASE_URL in a.get("href","") and a["href"] not in seen:
            t = a.get_text(strip=True)
            if t and len(t) > 5:
                results.append({"title": t, "url": a["href"]})
                seen.add(a["href"])

    return results

def fuzzy_rank(query, results):
    ranked = []
    for r in results:
        score = fuzz.WRatio(query.lower(), r["title"].lower())
        ranked.append({**r, "score": score})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked

JUNK_URL = re.compile(
    r"(facebook|twitter|whatsapp|instagram|telegram|youtube|linkedin|"
    r"mailto:|javascript:|#respond|#comment|/category/|/tag/|/author/|"
    r"/page/|/internship|/hiring|/jobs|/syllabus|/admit|/result|"
    r"/scholarship|/aktu-notes(?!/)|notesgallery\.com/?$)",
    re.I
)

JUNK_TEXT = re.compile(
    r"^(home|about|contact|syllabus|admit|result|internship|hiring|jobs|"
    r"scholarship|certificate|b\.?tech|mba|mca|check here|click here|"
    r"read more|see more|view all|whatsapp|telegram|join|privacy|"
    r"terms|dmca|sitemap|search|menu|skip|back|next|previous|share)$",
    re.I
)

NOISE_CLASSES = re.compile(
    r"sidebar|(?<!elementor-)widget|related|sharedaddy|jp-relatedposts|post-navigation|"
    r"nav-links|comments|author-bio|breadcrumb|social|share|ad|advertisement|"
    r"footer-widget|header-widget|cookie",
    re.I
)

def is_real_pyq_link(href, text):
    hl = href.lower()
    if "drive.google.com" in hl or "docs.google.com" in hl:
        return True
    if hl.endswith(".pdf") or ".pdf?" in hl or "/pdf/" in hl:
        return True
    if any(h in hl for h in ["dropbox.com", "onedrive.live", "mediafire.com", "mega.nz", "box.com", "1drv.ms"]):
        return True
    return False

def get_link_name(a_tag, index):
    text = a_tag.get_text(strip=True)
    generic = {"download", "click here", "here", "pdf", "link", "open", "view", "", "odd", "even"}
    if text.lower() not in generic and len(text) > 2:
        return text
    parent = a_tag.parent
    for _ in range(4):
        if parent is None:
            break
        siblings_text = []
        for sib in parent.children:
            if sib == a_tag:
                break
            st = sib.get_text(strip=True) if hasattr(sib, "get_text") else str(sib).strip()
            if st and len(st) > 3 and st.lower() not in generic:
                siblings_text.append(st)
        if siblings_text:
            return siblings_text[-1][:80]
        pt = parent.get_text(separator=" ", strip=True)
        pt = pt.replace(text, "").strip()
        if pt and len(pt) > 3:
            return pt[:80]
        parent = parent.parent
    return f"PYQ_Paper_{index}"

def extract_content(soup):
    content = None
    for cls in [re.compile(r"td-post-content|entry-content|post-content|article-content|post-body|main-content", re.I)]:
        content = soup.find("div", class_=cls)
        if content:
            break
    if not content:
        article = soup.find("article")
        if article:
            content = article
        else:
            content = soup.find("main") or soup.find("body")

    if content:
        for tag in content.find_all(["aside", "nav", "footer", "header"]):
            tag.decompose()
        for div in content.find_all("div", class_=NOISE_CLASSES):
            div.decompose()
        for div in content.find_all("section", class_=NOISE_CLASSES):
            div.decompose()
    return content

@st.cache_data(show_spinner=False)
def get_pdf_links(page_url):
    s = make_session()
    seed_session(s)
    resp = fetch(page_url, session=s)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    content = extract_content(soup)
    if not content:
        return []

    links = []
    seen = set()
    idx = 1

    for a in content.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)

        if not href or href in seen:
            continue
        if JUNK_URL.search(href):
            continue
        if JUNK_TEXT.match(text):
            continue

        if is_real_pyq_link(href, text):
            seen.add(href)
            ltype = "GDrive" if ("drive.google.com" in href.lower() or "docs.google.com" in href.lower()) else "Direct"
            name = get_link_name(a, idx)
            links.append({"name": name, "url": href, "type": ltype})
            idx += 1

    return links

@st.cache_data(show_spinner=False)
def create_zip(links):
    import io, zipfile, tempfile, os, re
    zip_buffer = io.BytesIO()
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, lnk in enumerate(links):
                fname = re.sub(r'[<>:"/\\|?*\n\r\t]', '', lnk['name'])
                fname = re.sub(r'\s+', '_', fname.strip())[:80]
                if not fname.lower().endswith(".pdf"):
                    fname += ".pdf"
                
                dest_path = os.path.join(tmpdir, fname)
                try:
                    if lnk["type"] == "GDrive":
                        try:
                            import gdown
                            gdown.download(lnk["url"], dest_path, quiet=True)
                        except ImportError:
                            pass # gdown not installed, skip
                    else:
                        resp = make_session().get(lnk["url"], stream=True, timeout=20)
                        if resp.status_code == 200:
                            with open(dest_path, "wb") as f:
                                for chunk in resp.iter_content(8192):
                                    f.write(chunk)
                    
                    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
                        zip_file.write(dest_path, arcname=fname)
                except:
                    pass
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# --- UI ---
st.title("📚 AKTU PYQ Extractor")
st.markdown("Easily search and find Previous Year Question papers from notesgallery.com.")

subject = st.text_input("Enter Subject Name (e.g., 'Machine Learning', 'Data Structures')")

if subject:
    with st.spinner(f"Searching for '{subject}'..."):
        results = search_on_site(subject)
        
    if not results:
        st.error("No results found. Try using the full subject name.")
    else:
        ranked = fuzzy_rank(subject, results)[:8]
        
        st.write("### Select the most relevant subject:")
        
        # Format options for the user
        options = [f"{r['title']} (Match: {r['score']}%)" for r in ranked]
        choice = st.radio("Search Results", options=options, index=0, label_visibility="collapsed")
        
        selected_index = options.index(choice)
        selected_page = ranked[selected_index]
        
        state_key = f"links_{selected_index}"
        
        if st.button("Extract PYQs 🚀", type="primary"):
            with st.spinner("Scraping download links..."):
                st.session_state[state_key] = get_pdf_links(selected_page["url"])
                
        if state_key in st.session_state:
            links = st.session_state[state_key]
            
            if not links:
                st.warning("No downloadable PYQ links found on this page. The layout might be different.")
            else:
                st.success(f"Found {len(links)} downloadable links!")
                
                # --- ZIP DOWNLOAD ---
                if st.button("Prepare 'Download All' ZIP 📦"):
                    with st.spinner("Downloading files and creating ZIP (this may take a minute)..."):
                        zip_data = create_zip(links)
                        safe_title = re.sub(r'[<>:"/\\|?*\n\r\t]', '', selected_page['title']).strip().replace(' ', '_')
                        st.download_button(
                            label="Download ZIP Now ⬇️",
                            data=zip_data,
                            file_name=f"{safe_title}_PYQs.zip",
                            mime="application/zip",
                            type="primary"
                        )
                
                st.write("---")
                st.write("##### Or download individually:")
                # Display links nicely
                for i, lnk in enumerate(links):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{i+1}. {lnk['name']}**")
                    with col2:
                        st.link_button(f"Open ({lnk['type']})", lnk["url"])
