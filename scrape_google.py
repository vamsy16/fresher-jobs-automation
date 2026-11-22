from datetime import datetime
import time
import urllib.parse
from fpdf import FPDF
from playwright.sync_api import sync_playwright

# Edit these queries anytime to match your specific skills or city (e.g., Bengaluru)
QUERIES = [
    'site:://linkedin.com "fresher" OR "0-1 years"',
    'site:://naukri.com "fresher"',
    'site:://internshala.com "fresher"',
    'site:foundit.in/job "fresher"',
]


def fetch_google_links(queries):
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
      encoded_query = urllib.parse.quote(query)
      # tbs=qdr:d filters results to the last 24 hours
      url = f"https://google.com{encoded_query}&tbs=qdr:d&num=20"

      page.goto(url, wait_until="domcontentloaded")
      time.sleep(4)  # Pause to let page load and reduce rate-limiting

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
  return list(extracted_links)


def save_to_pdf(links):
  pdf = FPDF()
  pdf.add_page()
  today = datetime.now().strftime("%Y-%m-%d")

  pdf.set_font("Arial", "B", 14)
  pdf.cell(0, 10, f"Fresher Job Links (Last 24 Hrs) - {today}", ln=True, align="C")
  pdf.ln(5)

  pdf.set_font("Arial", size=9)
  if not links:
    pdf.cell(
        0,
        10,
        "No links found (Google may have shown a CAPTCHA or 0 jobs matched).",
        ln=True,
    )
  else:
    for idx, link in enumerate(links, 1):
      pdf.set_text_color(0, 0, 255)
      pdf.multi_cell(0, 6, f"{idx}. {link}")
      pdf.ln(2)

  filename = f"fresher_links_{today}.pdf"
  pdf.output(filename)
  print(f"Saved {filename} with {len(links)} links.")


if __name__ == "__main__":
  job_links = fetch_google_links(QUERIES)
  save_to_pdf(job_links)
