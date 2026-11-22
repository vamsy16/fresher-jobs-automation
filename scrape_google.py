from datetime import datetime
import subprocess
import time
import urllib.parse
from fpdf import FPDF
from playwright.sync_api import sync_playwright

QUERIES = [
    'site:://linkedin.com "fresher"',
    'site:naukri.com "fresher" jobs',
    'site:internshala.com "fresher"',
    '"fresher" jobs bengaluru apply',
]

TARGET_DOMAINS = [
    "linkedin.com",
    "naukri.com",
    "internshala.com",
    "foundit.in",
    "indeed.com",
    "wellfound.com",
]


def fetch_google_links(queries):
  extracted_links = set()

  with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context()
    page = context.new_page()

    for query in queries:
      params = urllib.parse.urlencode({"q": query, "tbs": "qdr:d", "num": "20"})
      url = "https://google.com" + "/search?" + params

      page.goto(url, wait_until="networkidle")
      time.sleep(3)

      # If Google asks for CAPTCHA, wait 25 seconds for you to click it
      if (
          "sorry" in page.url
          or page.locator("iframe[src*='recaptcha']").count() > 0
      ):
        print("CAPTCHA shown! Please click 'I am not a robot' in Chrome...")
        time.sleep(25)

      all_a = page.locator("a").all()
      print(f"Query: {query} | Total <a> tags on page: {len(all_a)}")

      for link in all_a:
        href = link.get_attribute("href")
        if not href:
          continue
        if href.startswith("/url?"):
          parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
          q_list = parsed.get("q", [])
          href = q_list.pop(0) if q_list else ""

        if (
            isinstance(href, str)
            and href.startswith("http")
            and "google." not in href
            and any(domain in href for domain in TARGET_DOMAINS)
        ):
          extracted_links.add(href)

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
      f"Google Fresher Job Links (Last 24 Hrs) - {today}",
      ln=True,
      align="C",
  )
  pdf.ln(5)

  pdf.set_font("Arial", size=9)
  if not links:
    pdf.cell(0, 10, "No links extracted in this run.", ln=True)
  else:
    for idx, link in enumerate(links, 1):
      pdf.set_text_color(0, 0, 255)
      pdf.multi_cell(0, 6, f"{idx}. {link}")
      pdf.ln(2)

  filename = f"fresher_links_{today}.pdf"
  pdf.output(filename)
  print(f"Saved {filename} with {len(links)} links.")
  return filename


def push_to_github(filename):
  subprocess.run(["git", "add", "scrape_google.py", filename], check=True)
  subprocess.run(
      ["git", "commit", "-m", f"Add Google fresher job links: {filename}"],
      check=False,
  )
  subprocess.run(["git", "push"], check=True)
  print("Successfully uploaded PDF to GitHub!")


if __name__ == "__main__":
  job_links = fetch_google_links(QUERIES)
  pdf_file = save_to_pdf(job_links)
  push_to_github(pdf_file)
