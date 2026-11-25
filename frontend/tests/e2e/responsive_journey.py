import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright


BASE_URL = "http://localhost:8080"
VIEWPORTS = [
    (280, 800),
    (320, 800),
    (360, 800),
    (375, 812),
    (390, 844),
    (414, 896),
    (768, 1024),
    (1024, 900),
    (1440, 1000),
    (1920, 1080),
]
PUBLIC_ROUTES = [
    "/",
    "/login",
    "/register",
    "/explore",
    "/pricing",
    "/characters/atlas",
    "/billing/cancel",
]


async def inspect_layout(page, route, width):
    metrics = await page.evaluate(
        """
        () => {
          const viewport = { width: window.innerWidth, height: window.innerHeight };
          const offenders = Array.from(document.querySelectorAll("body *"))
            .filter((element) => {
              const style = window.getComputedStyle(element);
              const rect = element.getBoundingClientRect();
              return style.display !== "none" && style.visibility !== "hidden" &&
                (rect.right > viewport.width + 1 || rect.left < -1);
            })
            .slice(0, 8)
            .map((element) => ({
              tag: element.tagName.toLowerCase(),
              className: typeof element.className === "string" ? element.className : "",
              left: Math.round(element.getBoundingClientRect().left),
              right: Math.round(element.getBoundingClientRect().right),
            }));
          return {
            documentOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
            bodyOverflow: document.body.scrollWidth - document.body.clientWidth,
            offenders,
            images: Array.from(document.images).map((image) => ({
              src: image.currentSrc || image.src,
              width: image.naturalWidth,
            })),
          };
        }
        """
    )
    if metrics["documentOverflow"] > 1 or metrics["bodyOverflow"] > 1 or metrics["offenders"]:
        raise AssertionError(
            json.dumps(
                {"route": route, "width": width, "metrics": metrics},
                ensure_ascii=False,
            )
        )
    broken_images = [image for image in metrics["images"] if image["width"] == 0]
    remote_images = [image for image in metrics["images"] if "lovable.app" in image["src"]]
    if broken_images or remote_images:
        raise AssertionError(
            json.dumps(
                {
                    "route": route,
                    "width": width,
                    "broken_images": broken_images,
                    "remote_images": remote_images,
                },
                ensure_ascii=False,
            )
        )
    return metrics


async def authenticate(page):
    await page.goto(f"{BASE_URL}/login", wait_until="networkidle")
    await page.get_by_role(
        "button", name=re.compile(r"Compte de|Demo account", re.IGNORECASE)
    ).click()
    await page.get_by_test_id("wallet-balance").wait_for()


async def create_chat_route(page):
    await page.get_by_role(
        "link", name=re.compile(r"Explorer|Explore", re.IGNORECASE)
    ).first.click()
    await page.locator('a[href="/characters/atlas"]').first.click()
    await page.get_by_role(
        "button", name=re.compile(r"Commencer|Start", re.IGNORECASE)
    ).click()
    await page.wait_for_url(re.compile(r".*/chat/.*"), timeout=10000)
    return page.url.removeprefix(BASE_URL)


async def test_public_menu(page):
    await page.goto(BASE_URL, wait_until="networkidle")
    menu_button = page.locator(".public-menu-trigger")
    await menu_button.click()
    menu = page.locator("#public-mobile-menu")
    await menu.wait_for()
    await page.keyboard.press("Escape")
    await menu.wait_for(state="hidden")
    await menu_button.click()
    await menu.get_by_role("link", name=re.compile(r"Explorer|Explore", re.IGNORECASE)).click()
    await page.wait_for_url(re.compile(r"/explore$"))


async def run_viewport(browser, width, height):
    context = await browser.new_context(viewport={"width": width, "height": height})
    page = await context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    screenshots = Path("browser-artifacts/phase-1-1") / str(width)
    screenshots.mkdir(parents=True, exist_ok=True)
    results = {"width": width, "height": height, "routes": []}
    await page.goto(BASE_URL, wait_until="networkidle")
    if width < 768:
        await test_public_menu(page)
    await page.screenshot(path=str(screenshots / "landing.png"), full_page=True)
    for route in PUBLIC_ROUTES:
        await page.goto(f"{BASE_URL}{route}", wait_until="networkidle")
        metrics = await inspect_layout(page, route, width)
        results["routes"].append(
            {
                "route": route,
                "documentOverflow": metrics["documentOverflow"],
                "bodyOverflow": metrics["bodyOverflow"],
            }
        )
    await authenticate(page)
    chat_route = await create_chat_route(page)
    metrics = await inspect_layout(page, chat_route, width)
    results["routes"].append(
        {
            "route": chat_route,
            "documentOverflow": metrics["documentOverflow"],
            "bodyOverflow": metrics["bodyOverflow"],
        }
    )
    await page.screenshot(path=str(screenshots / "chat.png"), full_page=True)
    protected_routes = [
        "/conversations",
        "/wallet",
        "/settings",
        "/admin",
        "/billing/success?order=missing",
    ]
    for route in protected_routes:
        await page.goto(f"{BASE_URL}{route}", wait_until="networkidle")
        metrics = await inspect_layout(page, route, width)
        results["routes"].append(
            {
                "route": route,
                "documentOverflow": metrics["documentOverflow"],
                "bodyOverflow": metrics["bodyOverflow"],
            }
        )
    results["pageErrors"] = errors
    await context.close()
    if errors:
        raise AssertionError(json.dumps({"width": width, "errors": errors}, ensure_ascii=False))
    return results


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        results = []
        for width, height in VIEWPORTS:
            result = await run_viewport(browser, width, height)
            results.append(result)
            print(json.dumps(result, ensure_ascii=False))
        await browser.close()
        print(json.dumps({"viewports": len(results), "routes_per_viewport": 13}))


if __name__ == "__main__":
    asyncio.run(main())
