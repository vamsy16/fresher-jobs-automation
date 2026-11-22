from datetime import datetime
import time
import urllib.parse
from fpdf import FPDF
from playwright.sync_api import sync_playwright

QUERIES = [
    'site:://linkedin.com "fresher" OR "0-1 years"',
    'site:://naukri.com "fresher"',
    'site:://internshala.com "fresher"',
    'site:foundit.in/job "fresher"',
]


def clean_and_add(href, extracted_links):
  if not href:
    return
  # Unwrap DuckDuckGo redirects
  if "uddg=" in href:
    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
    href = parsed.get("uddg", [""])
  # Unwrap Yahoo redirects (RU=...)
  elif "/RU=" in href:
    try:
      encoded_part = href.split("/RU=").split("/RK=")
      href = urllib.parse.unquote(encoded_part)
    except Exception:
      pass

  if href.startswith("http") and not any(
      bad in href
      for bad in ["duckduckgo.com", "bing.com", "yahoo.com", "microsoft.com"]
  ):
    extracted_links.add(href)


def fetch_all_engines(queries):
  extracted_links = set()

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()

    for query in queries:
      # 1. DuckDuckGo (df=d -> Past 24 hours)
      try:
        ddg_params = urllib.parse.urlencode({"q": query, "df": "d"})
        ddg_url = "https://duckduckgo.com" + "/html/?" + ddg_params
        page.goto(ddg_url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        for link in page.locator("a.result__url").all():
          clean_and_add(link.get_attribute("href"), extracted_links)
      except Exception as e:
        print(f"DuckDuckGo skipped for '{query}': {e}")

      # 2. Bing (filters=ex1:"ez1" -> Past 24 hours)
      try:
        bing_params = urllib.parse.urlencode(
            {"q": query, "filters": 'ex1:"ez1"'}
        )
        bing_url = "https://bing.com" + "/search?" + bing_params
        page.goto(bing_url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        for link in page.locator("li.b_algo h2 a").all():
          clean_and_add(link.get_attribute("href"), extracted_links)
      except Exception as e:
        print(f"Bing skipped for '{query}': {e}")

      # 3. Yahoo Search (btf=d -> Past 24 hours)
      try:
        yahoo_params = urllib.parse.urlencode({"p": query, "btf": "d"})
        yahoo_url = "https://yahoo.com" + "/search?" + yahoo_params
        page.goto(yahoo_url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        for link in page.locator("div#web ol li h3 a").all():
          clean_and_add(link.get_attribute("href"), extracted_links)
      except Exception as e:
        print(f"Yahoo skipped for '{query}': {e}")

    browser.close()
  return sorted(list(extracted_links))


def save_to_pdf(links):
  pdf = FPDF()
  pdf.add_page()
  today = datetime.now().strftime("%Y-%m-%d")

  pdf.set_font("Arial", "B", 14)
  pdf.cell(
      0,
      10,
      f"Fresher Job Links (DDG + Bing + Yahoo | Last 24 Hrs) - {today}",
      ln=True,
      align="C",
  )
  pdf.ln(5)

  pdf.set_font("Arial", size=9)
  if not links:
    pdf.cell(
        0,
        10,
        "No new fresher job links matched across DuckDuckGo, Bing, or Yahoo.",
        ln=True,
    )
  else:
    for idx, link in enumerate(links, 1):
      pdf.set_text_color(0, 0, 255)
      pdf.multi_cell(0, 6, f"{idx}. {link}")
      pdf.ln(2)

  filename = f"fresher_links_{today}.pdf"
  pdf.output(filename)
  print(f"Saved {filename} with {len(links)} unique links.")


if __name__ == "__main__":
  job_links = fetch_all_engines(QUERIES)
  save_to_pdf(job_links)
