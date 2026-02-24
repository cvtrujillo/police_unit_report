import re
import logging
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from scraper.models import SizeStock
from config import Config

log = logging.getLogger(__name__)


def _semaforo(units: int, cfg: Config) -> str:
    if units <= cfg.CRIT_MAX:
        return "🔴 Crítico"
    if units <= cfg.LOW_MAX:
        return "🟡 Bajo"
    return "🟢 OK"


def _size_sort_key(size: str) -> float:
    m = re.match(r"^\s*(\d+(\.\d+)?)", str(size))
    return float(m.group(1)) if m else 999999.0


def scrape_pdp(sku: str, base_url: str, cfg: Config) -> list[SizeStock]:
    try:
        r = requests.get(
            f"{base_url}/api/products/{sku}/availability",
            headers=cfg.HEADERS,
            timeout=30
        )
        r.raise_for_status()
        variations = r.json().get("variation_list", [])
    except Exception as e:
        log.warning(f"PDP error {sku}: {e}")
        return []

    sizes = []
    for v in variations:
        units = int(v.get("availability", 0) or 0)
        sizes.append(SizeStock(
            sku=sku,
            size=v.get("size", ""),
            units=units,
            status=v.get("availability_status", "NA"),
            is_available=v.get("availability_status") != "NOT_AVAILABLE",
            semaforo=_semaforo(units, cfg),
        ))

    return sorted(sizes, key=lambda s: _size_sort_key(s.size))


def run_pdp_batch(skus: list[str], cfg: Config, base_url: str = "") -> pd.DataFrame:
    # base_url se infiere de la primera PLP_URL si no se pasa
    if not base_url and cfg.PLP_URLS:
        parts = cfg.PLP_URLS[0].split("/")
        base_url = f"https://{parts[2]}"

    all_sizes = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(scrape_pdp, sku, base_url, cfg): sku for sku in skus}
        for future in as_completed(futures):
            all_sizes.extend(future.result())

    return pd.DataFrame([vars(s) for s in all_sizes]) if all_sizes else pd.DataFrame()
