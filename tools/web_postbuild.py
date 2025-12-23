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
    # - Script src/prefetch are under /archives/0.9/
    # - IMPORTANT: config.cdn is used inside ES modules (e.g. pythons.js via import()).
    #   If we set a relative cdn like "./archives/0.9/", it gets resolved relative to the
    #   importing module URL (already /archives/0.9/...), resulting in double paths:
    #   "/archives/0.9/archives/0.9/...".
    #   Therefore, we must use an absolute path from site root: "/archives/0.9/".
    html = html.replace("https://pygame-web.github.io/archives/0.9/", "/archives/0.9/")
    html = html.replace("/archives/0.9//", "/archives/0.9/")  # Some templates contain double slashes
    html = html.replace('cdn : "./archives/0.9/",', 'cdn : "/archives/0.9/",')
    html = html.replace('cdn : "./",', 'cdn : "/archives/0.9/",')

    # Avoid "MEDIA USER ACTION REQUIRED" by disabling sound in the runtime config.
    # - Remove 'snd' from data-os (pygame-web modules)
    # - Disable UME blocking in JS config
    html = html.replace("data-os=vtx,fs,snd,gui", "data-os=vtx,fs,gui")
    html = html.replace("ume_block : 1,", "ume_block : 0,")

    # NOTE: Do NOT hide debug UI here.
    # Some environments fail to load certain assets; keeping the default console/debug
    # makes it much easier to diagnose issues (shows "Downloading..." and errors).

    index_path.write_text(html, encoding="utf-8")


def main() -> None:
    build_web = Path("build/web")
    if not (build_web / "index.html").exists():
        raise SystemExit("build/web/index.html not found. Run web_build.bat first.")

    cache = build_web / "_cdn_cache" / "archives" / "0.9"
    local_archives = build_web / "archives" / "0.9"

    # Vendor cached pygame-web runtime into build/web/archives/0.9/...
    copytree_overwrite(cache, local_archives)

    # Some templates prefetch "pythonrc.py" (not "cpythonrc.py").
    # Provide a compatibility copy so the prefetch doesn't 404.
    cpythonrc = local_archives / "cpythonrc.py"
    pythonrc = local_archives / "pythonrc.py"
    if cpythonrc.exists() and not pythonrc.exists():
        shutil.copy2(cpythonrc, pythonrc)

    # Patch build/web/index.html to use local runtime
    patch_index_html(build_web / "index.html")

    print("OK: vendored pygame-web runtime into build/web/archives/0.9 and patched index.html")


if __name__ == "__main__":
    main()


