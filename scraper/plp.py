import re
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from pytz import timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from scraper.models import SKUItem
from config import Config

log = logging.getLogger(__name__)
SKU_REGEX = re.compile(r"^(?=.*\d)[A-Z0-9]{5,10}$")


def _semaforo(units: int, cfg: Config) -> str:
    if units <= cfg.CRIT_MAX:
        return "🔴 Crítico"
    if units <= cfg.LOW_MAX:
        return "🟡 Bajo"
    return "🟢 OK"


def _parse_url(plp_url: str):
    plp_url = plp_url.strip().rstrip("/")
    parts = plp_url.split("/")
    domain = parts[2]
    country = domain.split(".")[-1]
    catalog = parts[3] if len(parts) > 3 else "unknown"
    base_url = f"https://{domain}"
    return plp_url, base_url, country, catalog


def _scrape_page(url: str, base_url: str, headers: dict) -> list[dict]:
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 404:
            return []
        r.raise_for_status()
    except Exception as e:
        log.warning(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    products = []
    seen = set()

    for a in soup.select('a[href*=".html"]'):
        href = a.get("href", "")
        name = " ".join(a.get_text(" ", strip=True).split())
        if not href or not name:
            continue

        full_url = urljoin(base_url, href)
        sku = full_url.split("/")[-1].replace(".html", "").split("#")[0].split("?")[0].upper()

        if not SKU_REGEX.match(sku) or full_url in seen:
            continue

        products.append({"name": name, "url": full_url, "sku": sku})
        seen.add(full_url)

    return products


def _get_availability(sku: str, base_url: str, headers: dict) -> int:
    try:
        r = requests.get(f"{base_url}/api/products/{sku}/availability", headers=headers, timeout=30)
        r.raise_for_status()
        variations = r.json().get("variation_list", [])
        available = sum(1 for v in variations if v.get("availability_status") != "NOT_AVAILABLE")
        return available, len(variations)
    except Exception as e:
        log.warning(f"Availability error for {sku}: {e}")
        return 0, 0


def scrape_plp(plp_url: str, cfg: Config) -> list[SKUItem]:
    plp_url, base_url, country, catalog = _parse_url(plp_url)
    tz = timezone(cfg.TIMEZONE)
    date_str = datetime.now(tz).strftime("%Y-%m-%d")

    # Paginar
    all_products = []
    seen_urls = set()
    start = 0

    while True:
        page_url = f"{plp_url}?start={start}"
        products = _scrape_page(page_url, base_url, cfg.HEADERS)
        new_products = [p for p in products if p["url"] not in seen_urls]

        if not new_products:
            break

        for p in new_products:
            seen_urls.add(p["url"])
        all_products.extend(new_products)
        start += 48

    log.info(f"PLP {catalog}: {len(all_products)} productos encontrados")

    # Availability en paralelo
    items = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {
            ex.submit(_get_availability, p["sku"], base_url, cfg.HEADERS): p
            for p in all_products
        }
        for future in as_completed(futures):
            p = futures[future]
            available, total = future.result()

            if available <= cfg.THRESHOLD:
                items.append(SKUItem(
                    date=date_str,
                    catalog=catalog,
                    country=country,
                    name=p["name"],
                    sku=p["sku"],
                    url=p["url"],
                    available_sizes=available,
                    total_sizes=total,
                    semaforo=_semaforo(available, cfg),
                    page=0,
                ))

    return items


def run_plp_batch(urls: list[str], cfg: Config) -> pd.DataFrame:
    all_items = []
    for url in urls:
        try:
            all_items.extend(scrape_plp(url, cfg))
        except Exception as e:
            log.error(f"Error scraping PLP {url}: {e}")

    if not all_items:
        return pd.DataFrame()

    df = pd.DataFrame([vars(i) for i in all_items])
    return df.sort_values("available_sizes").reset_index(drop=True)
