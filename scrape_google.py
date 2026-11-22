from datetime import datetime
import time
import urllib.parse
from bs4 import BeautifulSoup
from fpdf import FPDF
import requests

# LinkedIn public guest search queries (f_TPR=r86400 strictly filters to last 24 hours)
SEARCH_TERMS = [
    ("fresher", "India"),
    ("entry level", "India"),
    ("graduate trainee", "India"),
]


def fetch_linkedin_24h_links():
  extracted_links = set()
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
      )
  }

  for keywords, location in SEARCH_TERMS:
    params = urllib.parse.urlencode({
        "keywords": keywords,
        "location": location,
        "f_TPR": "r86400",  # 86400 seconds = Posted in last 24 hours
        "start": "0",
    })
    url = (
        "https://linkedin.com?"
        + params
    )
    try:
      resp = requests.get(url, headers=headers, timeout=15)
      if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, "html.parser")
        for a_tag in soup.find_all("a", href=True):
          href = a_tag["href"]
          if "/jobs/view/" in href:
            # Strip tracking parameters so URLs are clean
            clean_url = href.split("?")
            extracted_links.add(clean_url)
      time.sleep(2)
    except Exception as e:
      print(f"Error fetching {keywords}: {e}")

  return sorted(list(extracted_links))


def save_to_pdf(links):
  pdf = FPDF()
  pdf.add_page()
  today = datetime.now().strftime("%Y-%m-%d")

  pdf.set_font("Arial", "B", 14)
  pdf.cell(0, 10, f"Fresher Job Links (Last 24 Hrs) - {today}", ln=True, align="C")
  pdf.ln(5)

  pdf.set_font("Arial", size=9)
  if not links:
    pdf.cell(0, 10, "No fresher job links found in the last 24 hours.", ln=True)
  else:
    for idx, link in enumerate(links, 1):
      pdf.set_text_color(0, 0, 255)
      pdf.multi_cell(0, 6, f"{idx}. {link}")
      pdf.ln(2)

  filename = f"fresher_links_{today}.pdf"
  pdf.output(filename)
  print(f"Saved {filename} with {len(links)} unique links.")


if __name__ == "__main__":
  job_links = fetch_linkedin_24h_links()
  save_to_pdf(job_links)
