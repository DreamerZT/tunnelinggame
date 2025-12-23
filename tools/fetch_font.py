import os
import urllib.request
from pathlib import Path


# Google Fonts (OFL) - Noto Sans KR variable font (Korean)
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
FONT_DIR = Path("fonts")
FONT_PATH = FONT_DIR / "NotoSansKR.ttf"


def main() -> None:
    FONT_DIR.mkdir(parents=True, exist_ok=True)

    if FONT_PATH.exists() and FONT_PATH.stat().st_size > 0:
        print(f"OK: font already exists: {FONT_PATH}")
        return

    print(f"Downloading Korean font -> {FONT_PATH}")
    print(f"Source: {FONT_URL}")

    # Download
    with urllib.request.urlopen(FONT_URL) as resp:
        data = resp.read()

    if not data or len(data) < 100_000:
        raise RuntimeError(f"Downloaded file looks too small ({len(data)} bytes).")

    tmp = FONT_PATH.with_suffix(".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, FONT_PATH)
    print("OK: downloaded font")


if __name__ == "__main__":
    main()


