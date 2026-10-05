import csv
import re
from pathlib import Path

import requests

CSV_PATH = Path(__file__).parent / "books.csv"
OUTPUT_DIR = Path(__file__).parent / "books"


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def download(url: str, destination: Path) -> None:
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            title = row["title"]
            pdf_url = row["pdf_url"]
            destination = OUTPUT_DIR / f"{slugify(title)}.pdf"

            if destination.exists():
                print(f"Skipping {title} (already downloaded)")
                continue

            print(f"Downloading {title} from {pdf_url}")
            try:
                download(pdf_url, destination)
            except requests.RequestException as e:
                print(f"Failed to download {title}: {e}")
                destination.unlink(missing_ok=True)


if __name__ == "__main__":
    main()