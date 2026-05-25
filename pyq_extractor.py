#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════╗
║              PYQ EXTRACTOR - by Manish Dhangar            ║
║        AKTU Previous Year Question Paper Downloader       ║
╚═══════════════════════════════════════════════════════════╝
Target: notesgallery.com
"""

import os
import re
import sys
import time
import subprocess
from urllib.parse import urljoin, urlparse, quote

# ── AUTO-INSTALLER ────────────────────────────────────────────────────────────
REQUIRED_PACKAGES = {
    "requests":    "requests",
    "bs4":         "beautifulsoup4",
    "fuzzywuzzy":  "fuzzywuzzy",
    "Levenshtein": "python-Levenshtein",
    "rich":        "rich",
    "lxml":        "lxml",
}

def install_packages():
    missing = []
    for module, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(pip_name)
    if not missing:
        return
    print("\n[ PYQ Extractor — First-time Setup ]")
    print(f"Missing: {', '.join(missing)}\nInstalling...\n")
    pip_cmd = [sys.executable, "-m", "pip", "install"] + missing
    for extra in [[], ["--break-system-packages"], ["--user"]]:
        if subprocess.run(pip_cmd + extra, capture_output=True).returncode == 0:
            print("[OK] Done!\n"); return
    print("[FAIL] Run manually: pip install " + " ".join(missing) + " --break-system-packages")
    sys.exit(1)

install_packages()

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich import box

console = Console()
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

# Subject code lookup
SUBJECT_CODES = {
    "engineering mathematics i": "BAS103", "engineering mathematics ii": "BAS203",
    "engineering physics": "BAS101", "engineering chemistry": "BAS102",
    "programming for problem solving": "BCS101", "pps": "BCS101",
    "basic electrical engineering": "BEE101", "bee": "BEE101",
    "engineering mechanics": "BME101", "engineering drawing": "BOE101",
    "data structures": "KCS301", "ds": "KCS301",
    "computer organization and architecture": "KCS302", "coa": "KCS302",
    "discrete mathematics": "KAS301",
    "theory of automata and formal languages": "KCS401", "tafl": "KCS401",
    "object oriented programming": "KCS402", "oop": "KCS402",
    "database management systems": "KCS403", "dbms": "KCS403",
    "computer system security": "KCS404", "css": "KCS404",
    "operating systems": "KCS501", "os": "KCS501",
    "web technology": "KCS502",
    "design and analysis of algorithms": "KCS503", "daa": "KCS503",
    "software engineering": "KCS601", "se": "KCS601",
    "computer networks": "KCS603", "cn": "KCS603",
    "compiler design": "KCS602", "cd": "KCS602",
    "artificial intelligence": "KCS072", "ai": "KCS072",
    "machine learning": "KCS073", "ml": "KCS073",
    "cloud computing": "KCS074", "big data": "KCS075",
    "deep learning": "KCS076", "internet of things": "KEC501", "iot": "KEC501",
    "information security": "KCS701", "image processing": "KCS071",
    "data mining": "KIT601", "probability and statistics": "KAS401",
    "micro biology": "KAS501", "mlt": "—",
}

def get_code(title):
    return SUBJECT_CODES.get(title.lower().strip(), "—")


# ── NETWORK HELPERS ───────────────────────────────────────────────────────────

def fetch(url, session=None, retries=3):
    """Fetch a URL with retry + UA rotation. Returns response or None."""
    for attempt in range(retries):
        try:
            s = session or make_session()
            resp = s.get(url, timeout=15)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 403:
                console.print(f"[yellow]  [!] 403 attempt {attempt+1}, rotating UA...[/yellow]")
                time.sleep(2 + attempt * 2)
            else:
                console.print(f"[yellow]  [!] HTTP {resp.status_code} — {url}[/yellow]")
                return None
        except requests.RequestException as e:
            console.print(f"[red]  [!] Network error: {e}[/red]")
            time.sleep(2)
    return None


def seed_session(s):
    """Hit homepage first to get cookies — reduces 403s."""
    try:
        s.get(BASE_URL + "/", timeout=8)
        time.sleep(1.0)
    except Exception:
        pass


# ── SEARCH ────────────────────────────────────────────────────────────────────

def search_on_site(query):
    """WordPress ?s= search on notesgallery.com."""
    search_url = f"{BASE_URL}/?s={quote(query)}"
    s = make_session()
    seed_session(s)
    resp = fetch(search_url, session=s)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
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

    # Fallback: post/entry divs
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


# ── SCRAPE PYQ LINKS ──────────────────────────────────────────────────────────

# These URL patterns are NEVER actual PYQ files
JUNK_URL = re.compile(
    r"(facebook|twitter|whatsapp|instagram|telegram|youtube|linkedin|"
    r"mailto:|javascript:|#respond|#comment|/category/|/tag/|/author/|"
    r"/page/|/internship|/hiring|/jobs|/syllabus|/admit|/result|"
    r"/scholarship|/aktu-notes(?!/)|notesgallery\.com/?$)",
    re.I
)

# Link text that is clearly navigation, not a paper
JUNK_TEXT = re.compile(
    r"^(home|about|contact|syllabus|admit|result|internship|hiring|jobs|"
    r"scholarship|certificate|b\.?tech|mba|mca|check here|click here|"
    r"read more|see more|view all|whatsapp|telegram|join|privacy|"
    r"terms|dmca|sitemap|search|menu|skip|back|next|previous|share)$",
    re.I
)

# Noise containers to strip from page before scanning
NOISE_CLASSES = re.compile(
    r"sidebar|(?<!elementor-)widget|related|sharedaddy|jp-relatedposts|post-navigation|"
    r"nav-links|comments|author-bio|breadcrumb|social|share|ad|advertisement|"
    r"footer-widget|header-widget|cookie",
    re.I
)


def is_real_pyq_link(href, text):
    """
    Return True only if this link is a real downloadable PYQ.
    Accepts: Google Drive, direct .pdf, or any file-hosting link.
    Rejects: plain internal notesgallery page links.
    """
    hl = href.lower()

    # Definitely downloadable
    if "drive.google.com" in hl or "docs.google.com" in hl:
        return True
    if hl.endswith(".pdf") or ".pdf?" in hl or "/pdf/" in hl:
        return True
    # Other common file hosts
    if any(h in hl for h in ["dropbox.com", "onedrive.live", "mediafire.com",
                               "mega.nz", "box.com", "1drv.ms"]):
        return True

    # Internal notesgallery link — only keep if it clearly points to
    # a specific paper page (has a year pattern or "pyq" in path)
    if "notesgallery.com" in hl:
        # e.g. /mlt-2022-23/ or /mlt-pyq-2021/
        if re.search(r"20\d{2}", hl) or re.search(r"pyq(?!s)", hl):
            return True
        return False

    # External link with year in URL — likely a paper
    if re.search(r"20(1[8-9]|2[0-9])", hl):
        return True

    return False


def get_link_name(a_tag, index):
    """Best possible display name for a link."""
    text = a_tag.get_text(strip=True)
    generic = {"download", "click here", "here", "pdf", "link", "open", "view", "", "odd", "even"}
    if text.lower() not in generic and len(text) > 2:
        return text

    # Walk up DOM for surrounding context
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
    """Get the main post content div, stripping sidebar/noise."""
    content = None
    for cls in [
        re.compile(r"td-post-content|entry-content|post-content|article-content|post-body|main-content", re.I),
    ]:
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
        # Strip all noise containers
        for tag in content.find_all(["aside", "nav", "footer", "header"]):
            tag.decompose()
        for div in content.find_all("div", class_=NOISE_CLASSES):
            div.decompose()
        for div in content.find_all("section", class_=NOISE_CLASSES):
            div.decompose()

    return content


def scrape_pdf_links(page_url):
    """
    Scrape real downloadable PYQ links from a page.
    Only GDrive and direct .pdf links pass — everything else is noise.
    """
    s = make_session()
    seed_session(s)
    resp = fetch(page_url, session=s)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
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
            ltype = "gdrive" if ("drive.google.com" in href.lower() or "docs.google.com" in href.lower()) else "direct"
            name = get_link_name(a, idx)
            links.append({"name": name, "url": href, "type": ltype})
            idx += 1

    # Debug: if nothing found, dump all links seen so user can report structure
    if not links:
        all_links = [(a.get_text(strip=True), a["href"]) for a in content.find_all("a", href=True) if a.get_text(strip=True)]
        if all_links:
            console.print(f"\n[dim]  [DEBUG] Page has {len(all_links)} links but none matched. Top 20:[/dim]")
            for txt, href in all_links[:20]:
                console.print(f"  [dim]  [{txt[:45]:45}] {href[:70]}[/dim]")

    return links


# ── DOWNLOAD ──────────────────────────────────────────────────────────────────

def download_file(url, dest_path):
    try:
        s = make_session()
        resp = s.get(url, stream=True, timeout=30)
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"
        ct = resp.headers.get("content-type", "")
        if "text/html" in ct and ".pdf" not in url.lower():
            return False, "Got HTML (not a PDF)"
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        size_kb = os.path.getsize(dest_path) / 1024
        if size_kb < 5:
            os.remove(dest_path)
            return False, "Too small (error page?)"
        return True, f"{size_kb:.0f} KB"
    except Exception as e:
        return False, str(e)


def sanitize(name):
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:80] or "pyq_file"


def get_dest_dir(title):
    d = os.path.join(os.path.expanduser("~"), "Downloads", "PYQ_Extractor", sanitize(title))
    os.makedirs(d, exist_ok=True)
    return d


# ── UI ────────────────────────────────────────────────────────────────────────

def banner():
    console.print()
    console.print(Panel(
        "[bold cyan]  PYQ EXTRACTOR[/bold cyan]  —  AKTU Previous Year Question Paper Downloader\n"
        "  [dim]Manish Dhangar | CSE-AI | IIMT[/dim]",
        border_style="cyan", padding=(1, 2),
    ))
    console.print()


def show_results(ranked, query):
    t = Table(
        title=f"[bold yellow]Results for '{query}'[/bold yellow]",
        box=box.ROUNDED, border_style="yellow", show_lines=True,
    )
    t.add_column("#",     style="bold cyan",  width=4,  justify="center")
    t.add_column("Title", style="bold white",  min_width=42)
    t.add_column("Code",  style="green",       width=10, justify="center")
    t.add_column("Match", style="yellow",      width=8,  justify="center")
    for i, r in enumerate(ranked, 1):
        t.add_row(str(i), r["title"], get_code(r["title"]), f"{r['score']}%")
    console.print(t)


def show_links(links):
    t = Table(box=box.SIMPLE, border_style="cyan")
    t.add_column("#",    style="cyan",    width=4, justify="right")
    t.add_column("Name", style="white",   min_width=45)
    t.add_column("Type", style="magenta", width=9)
    for i, lnk in enumerate(links, 1):
        ltype = "[yellow]GDrive[/yellow]" if lnk["type"] == "gdrive" else "[green]Direct[/green]"
        t.add_row(str(i), lnk["name"][:70], ltype)
    console.print(t)


def pick_number(prompt_text, min_val, max_val):
    """Keep asking until user gives a valid integer in range or 0."""
    while True:
        val = Prompt.ask(prompt_text).strip()
        try:
            n = int(val)
            if n == 0 or min_val <= n <= max_val:
                return n
            console.print(f"[red]  [!] Enter a number between 1 and {max_val}, or 0 to cancel.[/red]")
        except ValueError:
            console.print(f"[red]  [!] '{val}' is not a number. Enter 1–{max_val} or 0 to cancel.[/red]")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run():
    banner()

    while True:
        # ── Subject input ──────────────────────────────────────────────────
        query = Prompt.ask("[bold cyan]\n[?] Subject name[/bold cyan] [dim](or 'exit')[/dim]").strip()
        if query.lower() in ("exit", "quit", "q"):
            console.print("\n[bold yellow]  Exiting. Good luck! 🔥[/bold yellow]\n")
            break
        if not query:
            console.print("[red]  [!] Cannot be empty.[/red]")
            continue

        # ── 1. Search ──────────────────────────────────────────────────────
        console.print(f"\n[bold white]  Searching:[/bold white] [cyan]'{query}'[/cyan]")
        with console.status("[yellow]  Contacting server...[/yellow]"):
            results = search_on_site(query)

        if not results:
            console.print("[red]  [!] No results found. Try full name e.g. 'Machine Learning', 'Computer Networks'.[/red]")
            continue

        # ── 2. Rank & show ─────────────────────────────────────────────────
        ranked = fuzzy_rank(query, results)[:8]
        console.print(f"\n[green]  [+] {len(results)} result(s) — top {len(ranked)} shown:[/green]")
        show_results(ranked, query)

        # ── 3. Pick — loop until valid number or 0 ─────────────────────────
        choice = pick_number(
            f"\n[bold cyan][?] Select number[/bold cyan] [dim](1–{len(ranked)}, 0 to cancel)[/dim]",
            1, len(ranked)
        )
        if choice == 0:
            console.print("[yellow]  Cancelled.[/yellow]")
            continue

        selected = ranked[choice - 1]
        console.print(Panel(
            f"[bold white]Title:[/bold white] [cyan]{selected['title']}[/cyan]\n"
            f"[bold white]Code: [/bold white] [green]{get_code(selected['title'])}[/green]",
            title="[bold yellow]Selected[/bold yellow]", border_style="yellow",
        ))
        if not Confirm.ask("[bold cyan][?] Proceed?[/bold cyan]", default=True):
            continue

        # ── 4. Scrape ──────────────────────────────────────────────────────
        console.print(f"\n[bold white]  Scraping download links...[/bold white]")
        with console.status("[yellow]  Extracting...[/yellow]"):
            links = scrape_pdf_links(selected["url"])

        if not links:
            console.print("[red]  [!] No downloadable PYQ links found on this page.[/red]")
            console.print(f"[dim]  The page may use a different structure. Please check the website manually.[/dim]")
            continue

        # ── 5. Show links ──────────────────────────────────────────────────
        console.print(f"\n[bold green]  [+] {len(links)} downloadable PYQ link(s) found:[/bold green]")
        show_links(links)

        gdrive_n = sum(1 for l in links if l["type"] == "gdrive")
        if gdrive_n:
            console.print(f"\n[yellow]  [!] {gdrive_n} Google Drive link(s) — needs gdown:[/yellow]")
            console.print("[dim]      pip install gdown --break-system-packages[/dim]")

        # ── 6. Select which to download ────────────────────────────────────
        console.print(
            f"\n[bold cyan][?] Which to download?[/bold cyan]\n"
            f"    [white]0[/white]       = all {len(links)} files\n"
            f"    [white]n[/white]       = skip\n"
            f"    [white]1,3,5[/white]   = specific numbers (comma separated)"
        )
        sel = Prompt.ask("[bold cyan]    Choice[/bold cyan]", default="0").strip()

        if sel.lower() in ("n", "no", "skip"):
            console.print("[yellow]  Skipped.[/yellow]")
            continue

        if sel == "0":
            to_download = links
        else:
            chosen, invalid = [], []
            for part in sel.split(","):
                part = part.strip()
                try:
                    i = int(part)
                    if 1 <= i <= len(links):
                        chosen.append(i - 1)
                    else:
                        invalid.append(part)
                except ValueError:
                    invalid.append(part)
            if invalid:
                console.print(f"[yellow]  [!] Ignored invalid: {', '.join(invalid)}[/yellow]")
            if not chosen:
                console.print("[red]  [!] Nothing valid selected.[/red]")
                continue
            seen_i = set()
            chosen = [i for i in chosen if not (i in seen_i or seen_i.add(i))]
            to_download = [links[i] for i in chosen]
            console.print(f"[green]  [+] Downloading {len(to_download)} selected file(s).[/green]")

        # ── 7. Download ────────────────────────────────────────────────────
        dest = get_dest_dir(selected["title"])
        console.print(f"\n[bold white]  Saving to:[/bold white] [cyan]{dest}[/cyan]\n")
        ok_count, fail_count = 0, 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=28),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("• {task.fields[status]}"),
            console=console,
        ) as prog:
            task = prog.add_task("[cyan]Downloading", total=len(to_download), status="…")
            for i, lnk in enumerate(to_download, 1):
                fname = sanitize(lnk["name"])
                if not fname.lower().endswith(".pdf"):
                    fname += ".pdf"
                dest_path = os.path.join(dest, fname)
                prog.update(task, description=f"[cyan]  [{i}/{len(to_download)}] {fname[:35]}", status="⬇")

                if lnk["type"] == "gdrive":
                    try:
                        import gdown
                        gdown.download(lnk["url"], dest_path, quiet=True)
                        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 5000:
                            ok_count += 1
                            prog.update(task, advance=1, status="[green]✓ GDrive[/green]")
                        else:
                            fail_count += 1
                            prog.update(task, advance=1, status="[red]✗ GDrive failed[/red]")
                    except ImportError:
                        fail_count += 1
                        prog.update(task, advance=1, status="[yellow]⚠ install gdown[/yellow]")
                    time.sleep(1)
                    continue

                ok, msg = download_file(lnk["url"], dest_path)
                if ok:
                    ok_count += 1
                    prog.update(task, advance=1, status=f"[green]✓ {msg}[/green]")
                else:
                    fail_count += 1
                    prog.update(task, advance=1, status=f"[red]✗ {msg}[/red]")
                time.sleep(0.8)

        console.print()
        console.print(Panel(
            f"[bold green]  ✓ Downloaded: {ok_count}[/bold green]\n"
            f"[bold red]  ✗ Failed:     {fail_count}[/bold red]\n"
            f"[bold white]  📁 {dest}[/bold white]"
            + ("\n\n[dim]  GDrive: pip install gdown --break-system-packages[/dim]"
               if any(l["type"] == "gdrive" for l in to_download) else ""),
            title="[bold white]Done[/bold white]",
            border_style="green" if fail_count == 0 else "yellow",
        ))

        if not Confirm.ask("\n[?] Search another subject?", default=True):
            console.print("\n[bold yellow]  Exiting. Padhai karo bhai. 🔥[/bold yellow]\n")
            break


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]  Ctrl+C — Exiting.[/bold yellow]\n")
        sys.exit(0)
