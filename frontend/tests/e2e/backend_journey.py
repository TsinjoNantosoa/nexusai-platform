import asyncio
import os
import re

from playwright.async_api import async_playwright

from isolation import assert_isolated_e2e_environment


assert_isolated_e2e_environment()


BASE_URL = os.environ.get("NEXUSAI_FRONTEND_URL", "http://localhost:8081")


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        email = f"browser-{os.getpid()}@example.test"
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        await page.goto(f"{BASE_URL}/register", wait_until="networkidle")
        await page.locator("#email").fill(email)
        await page.locator("#password").fill("fictional-password-123")
        await page.locator("#confirmPassword").fill("fictional-password-123")
        await page.locator('input[type="checkbox"]').nth(0).check()
        await page.locator('input[type="checkbox"]').nth(1).check()
        await page.locator('form button[type="submit"]').click()
        await page.wait_for_url(re.compile(r".*/wallet$"), timeout=10000)
        balance = await page.locator('[data-testid="wallet-balance"]').inner_text()
        assert balance.strip() == "20", balance

        await page.reload(wait_until="networkidle")
        assert (await page.locator('[data-testid="wallet-balance"]').inner_text()).strip() == "20"
        await page.goto(f"{BASE_URL}/pricing", wait_until="networkidle")
        assert await page.locator("body").inner_text() != ""

        logout = page.get_by_role("button", name=re.compile(r"se déconnecter|sign out", re.I))
        await page.goto(f"{BASE_URL}/wallet", wait_until="networkidle")
        await logout.click()
        await page.wait_for_url(re.compile(r".*/$"), timeout=10000)
        assert errors == [], errors
        print("real backend browser journey passed", email)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
