from datetime import datetime
import subprocess
import time
import urllib.parse
from fpdf import FPDF
from playwright.sync_api import sync_playwright

# Google Search queries (filtered to past 24 hours via tbs=qdr:d)
QUERIES = [
    'site:://linkedin.com "fresher" OR "0-1 years"',
    'site:://naukri.com "fresher"',
    'site:://internshala.com "fresher"',
    'site:foundit.in/job "fresher"',
]


def fetch_google_links(queries):
  extracted_links = set()

  with sync_playwright() as p:
    # Visible Chrome window prevents Google CAPTCHAs on your home/mobile internet
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    for query in queries:
      params = urllib.parse.urlencode({"q": query, "tbs": "qdr:d", "num": "20"})
      url = "https://google.com" + "/search?" + params

      page.goto(url, wait_until="domcontentloaded")
      time.sleep(5)

      links = page.locator("div#search a").all()
      for link in links:
        href = link.get_attribute("href")
        if (
            href
            and href.startswith("http")
            and "google.com" not in href
            and "webcache" not in href
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
