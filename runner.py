# runner.py

import logging
import pandas as pd
from datetime import datetime
from pytz import timezone

from config import load_config
from scraper.plp import run_plp_batch
from scraper.pdp import run_pdp_batch
from storage.sharepoint import upload_to_sharepoint
from storage.local import save_excel
from alerts.email_alert import send_email_alert
from alerts.teams_alert import send_teams_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("run.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def main():
    cfg = load_config()
    tz = timezone(cfg.TIMEZONE)
    now = datetime.now(tz)
    session_label = "mañana" if now.hour < 13 else "tarde"
    run_ts = now.strftime("%Y%m%d_%H%M")

    log.info(f"Iniciando run {run_ts} [{session_label}]")

    # 1. Scraping PLP
    log.info(f"Scrapeando {len(cfg.PLP_URLS)} PLP(s)...")
    plp_df = run_plp_batch(cfg.PLP_URLS, cfg)
    log.info(f"PLP: {len(plp_df)} productos encontrados")

    if plp_df.empty:
        log.warning("No se encontraron productos. Abortando.")
        return

    # 2. Scraping PDP para los críticos
    critical_skus = plp_df[plp_df["semaforo"].str.contains("Crítico")]["sku"].tolist()
    log.info(f"SKUs críticos para PDP: {len(critical_skus)}")

    pdp_df = run_pdp_batch(critical_skus, cfg) if critical_skus else pd.DataFrame()

    # 3. Guardar Excel localmente y subir a SharePoint
    excel_path = save_excel(plp_df, pdp_df, run_ts)
    log.info(f"Excel guardado: {excel_path}")

    sp_url = upload_to_sharepoint(excel_path, f"inventory_{run_ts}.xlsx", cfg)
    log.info(f"Subido a SharePoint: {sp_url}")

    # 4. Alertas si hay críticos
    crit_count = len(critical_skus)
    if crit_count > 0:
        log.info(f"Enviando alertas ({crit_count} críticos)...")
        send_email_alert(plp_df, crit_count, run_ts, cfg)
        if cfg.TEAMS_WEBHOOK_URL:
            send_teams_alert(plp_df, crit_count, run_ts, cfg)

    log.info("Run completado exitosamente.")


if __name__ == "__main__":
    main()
