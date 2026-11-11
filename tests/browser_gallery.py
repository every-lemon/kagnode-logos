"""Account-free hosted and downloaded gallery journeys using committed artwork."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import tempfile
import threading
from urllib.parse import unquote, urlsplit

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "catalog.json").read_text())
CORE_VERSION = json.loads((ROOT / "vendor/core-bundle.json").read_text())["version"]


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = f"http://127.0.0.1:{server.server_port}"
try:
    with tempfile.TemporaryDirectory(prefix="kagnode-gallery-browser-") as temporary:
        with sync_playwright() as playwright:
            engine = os.environ.get("KAGNODE_BROWSER_ENGINE", "chromium")
            executable = os.environ.get("KAGNODE_BROWSER_EXECUTABLE")
            browser = getattr(playwright, engine).launch(
                **({"executable_path": executable} if executable else {})
            )
            context = browser.new_context(
                accept_downloads=True, reduced_motion="reduce"
            )
            failures = []
            unavailable = {"value": False}

            def route_request(route):
                url = route.request.url
                if url.startswith(origin) or url.startswith(
                    ("file:", "blob:", "data:")
                ):
                    return route.continue_()
                if not url.startswith(
                    "https://raw.githubusercontent.com/every-lemon/kagnode-logos/"
                ):
                    failures.append(
                        "Unexpected external request: " + urlsplit(url).netloc
                    )
                    return route.abort()
                if unavailable["value"]:
                    return route.abort()
                name = unquote(urlsplit(url).path).split("/", 4)[-1]
                path = ROOT / name
                if not path.resolve().is_relative_to(ROOT) or not path.is_file():
                    return route.fulfill(status=404, body="Not found")
                return route.fulfill(
                    path=str(path),
                    content_type=mimetypes.guess_type(path)[0]
                    or "application/octet-stream",
                    headers={"Access-Control-Allow-Origin": "*"},
                )

            context.route("**/*", route_request)
            page = context.new_page()
            page.on("pageerror", lambda error: failures.append(str(error)))
            for width in [390, 820, 1440]:
                page.set_viewport_size({"width": width, "height": 1000})
                page.goto(origin + "/index.html")
                expect(page.locator(".asset")).to_have_count(24)
                page.bring_to_front()
                try:
                    page.wait_for_function(
                        "() => !!window.KagNodeCore && [...document.querySelectorAll('#grid img')].some(i=>i.naturalWidth > 0)"
                    )
                except Exception:
                    print(
                        json.dumps(
                            {
                                "failures": failures,
                                "core": page.evaluate("!!window.KagNodeCore"),
                                "previews": page.locator(
                                    "#grid .preview"
                                ).all_inner_texts(),
                                "images": page.locator("#grid img").evaluate_all(
                                    "imgs=>imgs.map(i=>({src:i.src,complete:i.complete,width:i.naturalWidth}))"
                                ),
                            }
                        )
                    )
                    raise
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth+1"
                )
                assert page.evaluate("KagNodeCore.version") == CORE_VERSION
                assert page.locator("[data-core-account-trigger]").count() == 0
                page.locator("#search").fill("Entropy")
                expect(page.locator(".asset").first).to_be_visible()
                assert "Entropy" in page.locator(".asset").first.inner_text()
                page.locator("#search").fill("")
                page.locator("[data-menu=format]").evaluate(
                    "n=>n.closest('details').querySelector('summary').click()"
                )
                page.locator("[data-menu=format] button").get_by_text(
                    "EPS", exact=True
                ).click()
                page.locator(".asset-actions button").first.click()
                expect(page.locator("#asset-dialog")).to_be_visible()
                page.wait_for_function(
                    "() => document.querySelector('#dialog-preview img')?.naturalWidth>0"
                )
                with page.expect_download() as event:
                    page.locator("#file-options button").first.click()
                target = Path(temporary) / f"{engine}-{width}.eps"
                event.value.save_as(target)
                assert target.read_bytes().startswith(b"%!PS")
                page.keyboard.press("Escape")
                expect(page.locator("#asset-dialog")).not_to_be_visible()
            page.goto(origin + "/index.html")
            while page.locator("#more").is_visible():
                page.locator("#more").click()
            page.evaluate(
                "document.querySelectorAll('#grid .preview').forEach(n=>n.loadArtwork?.())"
            )
            page.wait_for_function(
                "() => document.querySelectorAll('#grid .preview.pending').length===0"
            )
            assert page.locator(".asset").count() == len(
                {item["design"] for item in CATALOG["assets"]}
            )
            assert page.locator("#grid .preview-error").count() == 0
            assert page.locator("#grid img").evaluate_all(
                "imgs=>imgs.every(i=>i.complete&&i.naturalWidth>0)"
            )
            with page.expect_download() as event:
                page.locator("#viewer-download").click()
            viewer = Path(temporary) / "kagnode-logos.html"
            event.value.save_as(viewer)
            page.goto(viewer.as_uri())
            expect(page.locator(".asset")).to_have_count(24)
            page.wait_for_function(
                "() => document.querySelector('#grid img')?.naturalWidth>0"
            )
            assert (
                page.locator('link[rel="icon"]')
                .get_attribute("href")
                .startswith("data:")
            )
            page.set_viewport_size({"width": 390, "height": 1000})
            page.locator("[data-core-mobile]").click()
            assert page.locator(".kn-core-drawer-scrim:not([hidden])").count() == 1
            assert page.locator("#sidebar").evaluate("e=>!e.inert")
            page.keyboard.press("Escape")
            assert page.locator("#sidebar").evaluate("e=>e.inert")
            assert page.locator("[data-core-toggle]").count() == 1
            assert page.locator(".kn-core-drawer-scrim").count() == 1
            unavailable["value"] = True
            page.locator("#refresh").click()
            expect(page.locator("#status")).to_be_visible()
            assert "included catalog" in page.locator("#status").inner_text()
            assert not failures, failures
            browser.close()
            print(
                json.dumps(
                    {
                        "engine": engine,
                        "layouts": [390, 820, 1440],
                        "downloadedViewer": True,
                        "originalEpsDownloads": 3,
                        "networkFailureVisible": True,
                        "allDesignsDecoded": True,
                        "accountFree": True,
                    }
                )
            )
finally:
    server.shutdown()
    server.server_close()
