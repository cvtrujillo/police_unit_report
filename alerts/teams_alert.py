import requests
import logging

log = logging.getLogger(__name__)


def send_teams_alert(df, crit_count: int, run_ts: str, cfg):
    if not cfg.TEAMS_WEBHOOK_URL:
        return

    top5 = df[df["semaforo"].str.contains("Crítico")].head(5)
    facts = [
        {"name": row["sku"], "value": f"{row['available_sizes']} tallas disponibles"}
        for _, row in top5.iterrows()
    ]

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "FF0000",
        "summary": f"Alerta inventario — {crit_count} críticos",
        "sections": [{
            "activityTitle": f"🔴 {crit_count} SKUs en estado crítico",
            "activitySubtitle": f"Run: {run_ts} | adidas Inventory System",
            "facts": facts,
            "markdown": True,
        }],
    }

    resp = requests.post(cfg.TEAMS_WEBHOOK_URL, json=payload, timeout=30)
    resp.raise_for_status()
    log.info("Teams alert enviada")
```

---

Y los `__init__.py` vacíos que necesitas:
```
scraper/__init__.py      # vacío
storage/__init__.py      # vacío
alerts/__init__.py       # vacío
```

---

**`requirements.txt`**
```
requests
pandas
beautifulsoup4
lxml
pytz
openpyxl
msal
