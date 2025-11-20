import cloudscraper

scraper = cloudscraper.create_scraper(browser={
    'browser': 'firefox',
    'platform': 'windows',
    'mobile': False
})

print("Fetching notesgallery.com/?s=math")
resp = scraper.get("https://notesgallery.com/?s=math")
print("Status:", resp.status_code)
print("Title in HTML:", "<title>" in resp.text)
