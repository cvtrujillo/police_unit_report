import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger(__name__)


def send_email_alert(df, crit_count: int, run_ts: str, cfg):
    if not cfg.SMTP_USER or not cfg.ALERT_RECIPIENTS:
        log.warning("Email omitida: credenciales no configuradas.")
        return

    crit_df = df[df["semaforo"].str.contains("Crítico")][
        ["sku", "name", "available_sizes", "semaforo", "url"]
    ].head(20)

    table_html = crit_df.to_html(index=False, border=0)

    html = f"""
    <html><body style="font-family:Arial,sans-serif">
      <h2 style="color:#C0392B">🔴 Alerta de Inventario Crítico</h2>
      <p><b>{crit_count} SKUs</b> con stock crítico detectados en el run <code>{run_ts}</code>.</p>
      <style>table{{border-collapse:collapse;width:100%}}
      th{{background:#1F3864;color:white;padding:8px}}
      td{{padding:6px;border:1px solid #ddd}}</style>
      {table_html}
      <p style="color:#888;font-size:12px">Sistema automático — adidas Inventory Intelligence</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔴 Inventario Crítico [{run_ts}] — {crit_count} SKUs"
    msg["From"] = cfg.SMTP_USER
    msg["To"] = ", ".join(cfg.ALERT_RECIPIENTS)
    msg.attach(MIMEText(html, "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT) as s:
        s.starttls(context=ctx)
        s.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
        s.sendmail(cfg.SMTP_USER, cfg.ALERT_RECIPIENTS, msg.as_string())

    log.info(f"Email enviada a {cfg.ALERT_RECIPIENTS}")
