from __future__ import annotations

import asyncio
import hashlib
import random
import re
from dataclasses import dataclass
from typing import Awaitable, Callable, Protocol
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from slugify import slugify

from app.config import Settings

ProgressCallback = Callable[[int], Awaitable[None]]


class ScraperError(RuntimeError):
    pass


@dataclass(slots=True)
class ScrapeRequest:
    query: str
    category_url: str | None
    max_pages: int
    max_items: int
    sort: str


class ScraperProvider(Protocol):
    async def scrape(self, request: ScrapeRequest, progress: ProgressCallback) -> list[dict]: ...


def _parse_number(text: str | None) -> int | None:
    if not text:
        return None
    normalized = text.lower().replace(".", "").replace(",", ".")
    multiplier = 1000 if "mil" in normalized else 1
    match = re.search(r"(\d+(?:\.\d+)?)", normalized)
    return int(float(match.group(1)) * multiplier) if match else None


def _parse_price(text: str | None) -> float | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d,\.]", "", text)
    if not cleaned:
        return None
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


class MockScraper:
    async def scrape(self, request: ScrapeRequest, progress: ProgressCallback) -> list[dict]:
        seed = int(hashlib.sha256(request.query.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        total = min(request.max_items, request.max_pages * 32)
        products: list[dict] = []
        base = rng.uniform(150, 4500)

        for index in range(total):
            await asyncio.sleep(0.01)
            price = round(max(20, rng.gauss(base, base * 0.28)), 2)
            products.append(
                {
                    "external_id": f"DEMO-{seed}-{index + 1}",
                    "title": f"{request.query.title()} — Modelo {index + 1}",
                    "price": price,
                    "currency": "BRL",
                    "rating": round(rng.uniform(3.6, 5.0), 1),
                    "review_count": rng.randint(0, 2500),
                    "sold_quantity": rng.randint(0, 5000),
                    "product_url": f"https://example.com/products/{slugify(request.query)}-{index + 1}",
                    "image_url": f"https://picsum.photos/seed/{seed + index}/320/240",
                    "position": index + 1,
                }
            )
            await progress(min(95, int(((index + 1) / total) * 95)))

        return _sort_products(products, request.sort)


class MercadoLivreApiScraper:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def scrape(self, request: ScrapeRequest, progress: ProgressCallback) -> list[dict]:
        headers = {"User-Agent": self.settings.user_agent}
        if self.settings.meli_access_token:
            headers["Authorization"] = f"Bearer {self.settings.meli_access_token}"

        products: list[dict] = []
        page_size = 50
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            for page in range(request.max_pages):
                offset = page * page_size
                response = await client.get(
                    "https://api.mercadolibre.com/sites/MLB/search",
                    params={"q": request.query, "limit": page_size, "offset": offset},
                )
                if response.status_code in {401, 403}:
                    raise ScraperError(
                        "A API recusou a requisição. Configure MELI_ACCESS_TOKEN com credenciais válidas."
                    )
                response.raise_for_status()
                data = response.json()
                for item in data.get("results", []):
                    products.append(
                        {
                            "external_id": item.get("id"),
                            "title": item.get("title") or "Produto sem título",
                            "price": float(item.get("price") or 0),
                            "currency": item.get("currency_id") or "BRL",
                            "rating": None,
                            "review_count": None,
                            "sold_quantity": item.get("sold_quantity"),
                            "product_url": item.get("permalink") or "https://www.mercadolivre.com.br/",
                            "image_url": item.get("thumbnail"),
                            "position": len(products) + 1,
                        }
                    )
                    if len(products) >= request.max_items:
                        break
                await progress(min(95, int(((page + 1) / request.max_pages) * 95)))
                if len(products) >= request.max_items or not data.get("results"):
                    break
                await asyncio.sleep(self.settings.request_delay_seconds)

        return _sort_products(products[: request.max_items], request.sort)


class MercadoLivreBrowserScraper:
    CARD_SELECTORS = ["li.ui-search-layout__item", ".ui-search-layout__item", ".poly-card"]
    TITLE_SELECTORS = ["a.poly-component__title", ".ui-search-item__title", "h2"]
    PRICE_SELECTORS = [".andes-money-amount__fraction", ".poly-price__current .andes-money-amount__fraction"]
    RATING_SELECTORS = [".poly-reviews__rating", ".ui-search-reviews__rating-number"]
    REVIEW_SELECTORS = [".poly-reviews__total", ".ui-search-reviews__amount"]
    SALES_SELECTORS = [".poly-component__advantage", ".ui-search-item__group__element"]

    def __init__(self, settings: Settings):
        self.settings = settings

    async def _robots_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            async with httpx.AsyncClient(timeout=15, headers={"User-Agent": self.settings.user_agent}) as client:
                response = await client.get(robots_url)
                if response.status_code >= 400:
                    return False
                parser.parse(response.text.splitlines())
            return parser.can_fetch(self.settings.user_agent, url)
        except Exception:
            return False

    @staticmethod
    def _validate_url(url: str) -> str:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if parsed.scheme not in {"http", "https"} or not (
            host == "mercadolivre.com.br" or host.endswith(".mercadolivre.com.br")
        ):
            raise ScraperError("A URL deve pertencer ao domínio mercadolivre.com.br.")
        return url

    async def scrape(self, request: ScrapeRequest, progress: ProgressCallback) -> list[dict]:
        if not self.settings.scraping_enabled:
            raise ScraperError(
                "O modo browser está desabilitado. Defina SCRAPING_ENABLED=true após validar as regras do site."
            )

        target_url = request.category_url or f"https://lista.mercadolivre.com.br/{slugify(request.query)}"
        target_url = self._validate_url(target_url)
        if not await self._robots_allowed(target_url):
            raise ScraperError(
                "A política robots.txt não autorizou a coleta para este agente. Use o provedor API ou mock."
            )

        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise ScraperError("Playwright não instalado. Execute: playwright install chromium") from exc

        products: list[dict] = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.settings.user_agent, locale="pt-BR")
            page = await context.new_page()
            url = target_url
            try:
                for page_number in range(request.max_pages):
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                    if response and response.status >= 400:
                        raise ScraperError(f"Página respondeu HTTP {response.status}.")
                    await page.wait_for_timeout(1200)

                    cards = None
                    for selector in self.CARD_SELECTORS:
                        candidate = page.locator(selector)
                        if await candidate.count() > 0:
                            cards = candidate
                            break
                    if cards is None:
                        title = await page.title()
                        if "captcha" in title.lower() or "acesso" in title.lower():
                            raise ScraperError("O site solicitou verificação. A execução foi interrompida sem contorno.")
                        raise ScraperError("Nenhum card de produto foi encontrado; os seletores podem ter mudado.")

                    for i in range(await cards.count()):
                        if len(products) >= request.max_items:
                            break
                        card = cards.nth(i)
                        title = await _first_text(card, self.TITLE_SELECTORS)
                        price_text = await _first_text(card, self.PRICE_SELECTORS)
                        price = _parse_price(price_text)
                        link = await _first_attr(card, self.TITLE_SELECTORS, "href")
                        if not title or price is None or not link:
                            continue
                        rating = _parse_price(await _first_text(card, self.RATING_SELECTORS))
                        review_count = _parse_number(await _first_text(card, self.REVIEW_SELECTORS))
                        sales_text = await _first_text_containing(card, self.SALES_SELECTORS, "vend")
                        image = await _first_attr(card, ["img"], "src")
                        products.append(
                            {
                                "external_id": None,
                                "title": title.strip(),
                                "price": price,
                                "currency": "BRL",
                                "rating": rating,
                                "review_count": review_count,
                                "sold_quantity": _parse_number(sales_text),
                                "product_url": link,
                                "image_url": image,
                                "position": len(products) + 1,
                            }
                        )

                    await progress(min(95, int(((page_number + 1) / request.max_pages) * 95)))
                    if len(products) >= request.max_items:
                        break
                    next_link = page.locator('a[title="Seguinte"], a.andes-pagination__link[aria-label*="Seguinte"]').first
                    if await next_link.count() == 0:
                        break
                    href = await next_link.get_attribute("href")
                    if not href:
                        break
                    url = self._validate_url(href)
                    await asyncio.sleep(self.settings.request_delay_seconds)
            finally:
                await context.close()
                await browser.close()

        return _sort_products(products[: request.max_items], request.sort)


async def _first_text(card, selectors: list[str]) -> str | None:
    for selector in selectors:
        locator = card.locator(selector).first
        if await locator.count():
            try:
                text = await locator.inner_text(timeout=1500)
                if text.strip():
                    return text.strip()
            except Exception:
                continue
    return None


async def _first_attr(card, selectors: list[str], attribute: str) -> str | None:
    for selector in selectors:
        locator = card.locator(selector).first
        if await locator.count():
            try:
                value = await locator.get_attribute(attribute, timeout=1500)
                if value:
                    return value
            except Exception:
                continue
    return None


async def _first_text_containing(card, selectors: list[str], term: str) -> str | None:
    for selector in selectors:
        locator = card.locator(selector)
        for idx in range(await locator.count()):
            try:
                text = await locator.nth(idx).inner_text(timeout=1000)
                if term.lower() in text.lower():
                    return text
            except Exception:
                continue
    return None


def _sort_products(products: list[dict], sort: str) -> list[dict]:
    if sort == "price_asc":
        products.sort(key=lambda p: float(p["price"]))
    elif sort == "price_desc":
        products.sort(key=lambda p: float(p["price"]), reverse=True)
    for index, product in enumerate(products, start=1):
        product["position"] = index
    return products


def build_scraper(settings: Settings) -> ScraperProvider:
    provider = settings.scraper_provider.lower().strip()
    if provider == "mock":
        return MockScraper()
    if provider == "api":
        return MercadoLivreApiScraper(settings)
    if provider == "browser":
        return MercadoLivreBrowserScraper(settings)
    raise ScraperError(f"SCRAPER_PROVIDER desconhecido: {provider}")
