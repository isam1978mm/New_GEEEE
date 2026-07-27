"""Render every page of the exact Coal Creek LRC-50-F PDF for visual review."""
from pathlib import Path
import fitz
import requests

URL = (
    "https://www.ndic.nd.gov/sites/www/files/documents/Lignite-Research-Council/"
    "Grant-Rounds--Final-Reports/Proposals/Grant%20Rounds%2059-50/"
    "LRC-50-F-Alternative-Cover-Demonstration-Project-a.pdf"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)",
    "Referer": "https://www.ndic.nd.gov/lignite-research-program-grant-rounds-59-50",
}

root = Path(__file__).resolve().parents[1]
out = root / "artifacts" / "coal_creek_cover_scout_v3" / "all_pages"
out.mkdir(parents=True, exist_ok=True)
response = requests.get(URL, headers=HEADERS, timeout=600, allow_redirects=True)
response.raise_for_status()
if not response.content.startswith(b"%PDF-"):
    raise RuntimeError("official Coal Creek URL did not return PDF bytes")
pdf = Path("/tmp/coal_creek_all_pages.pdf")
pdf.write_bytes(response.content)
doc = fitz.open(pdf)
for index in range(doc.page_count):
    pix = doc.load_page(index).get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
    pix.save(out / f"page_{index + 1:04d}.png")
doc.close()
pdf.unlink(missing_ok=True)
print(f"rendered {index + 1} pages")
