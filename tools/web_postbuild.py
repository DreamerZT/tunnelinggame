import os
import shutil
from pathlib import Path


def copytree_overwrite(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    dst.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for name in files:
            shutil.copy2(Path(root) / name, dst / rel / name)


def patch_index_html(index_path: Path) -> None:
    html = index_path.read_text(encoding="utf-8")

    # Make pygame-web runtime fully local (no external CDN)
    # Original: https://pygame-web.github.io/archives/0.9/...
    html = html.replace(
        "https://pygame-web.github.io/archives/0.9/",
        "./archives/0.9/",
    )
    # Some templates contain double slashes
    html = html.replace("./archives/0.9//", "./archives/0.9/")

    # Hide debug UI by default (keep it lightweight for internal sharing)
    # - xtermjs: console UI
    # - gui_debug: debug widgets
    html = html.replace("xtermjs : \"1\" ,", "xtermjs : \"0\" ,")
    html = html.replace("gui_debug : 3,", "gui_debug : 0,")

    index_path.write_text(html, encoding="utf-8")


def main() -> None:
    build_web = Path("build/web")
    if not (build_web / "index.html").exists():
        raise SystemExit("build/web/index.html not found. Run web_build.bat first.")

    cache = build_web / "_cdn_cache" / "archives" / "0.9"
    local_archives = build_web / "archives" / "0.9"

    # Vendor cached pygame-web runtime into build/web/archives/0.9/...
    copytree_overwrite(cache, local_archives)

    # Patch build/web/index.html to use local runtime
    patch_index_html(build_web / "index.html")

    print("OK: vendored pygame-web runtime into build/web/archives/0.9 and patched index.html")


if __name__ == "__main__":
    main()


