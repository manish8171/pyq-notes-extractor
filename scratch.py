import cloudscraper
from bs4 import BeautifulSoup
import re

url = "https://notesgallery.com/3rd-year-aktu-pyqs-cn/"
scraper = cloudscraper.create_scraper(browser={'browser': 'firefox', 'platform': 'windows', 'mobile': False})
resp = scraper.get(url)
soup = BeautifulSoup(resp.text, "html.parser")

for r_str in ["widget", "(?<!elementor-)widget"]:
    print(f"\n--- Testing Regex: {r_str} ---")
    NOISE = re.compile(f"sidebar|{r_str}|related", re.I)
    
    content = None
    for cls in [re.compile(r"td-post-content|entry-content|post-content|article-content|post-body|main-content", re.I)]:
        content = soup.find("div", class_=cls)
        if content: break
    if not content: content = soup.find("article") or soup.find("main") or soup.find("body")
    
    import copy
    c = copy.copy(content)
    
    for div in c.find_all("div", class_=NOISE):
        div.decompose()
    
    links = c.find_all("a", href=True)
    print("Found total links:", len(links))
    pdf_links = [a['href'] for a in links if 'drive.google.com' in a['href'] or '.pdf' in a['href']]
    print("Found PDF/Drive links:", len(pdf_links))
