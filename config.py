import os
from dataclasses import dataclass, field


@dataclass
class Config:
    PLP_URLS: list[str] = field(default_factory=list)
    HEADERS: dict = field(default_factory=dict)
    CRIT_MAX: int = 3
    LOW_MAX: int = 10
    THRESHOLD: int = 3
    TIMEZONE: str = "America/Bogota"

    SP_TENANT_ID: str = ""
    SP_CLIENT_ID: str = ""
    SP_CLIENT_SECRET: str = ""
    SP_SITE_ID: str = ""
    SP_PARENT_ITEM_ID: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_RECIPIENTS: list[str] = field(default_factory=list)

    TEAMS_WEBHOOK_URL: str = ""


def load_config() -> Config:
    return Config(
        PLP_URLS=[u.strip() for u in os.getenv("PLP_URLS", "").split(",") if u.strip()],
        HEADERS={"User-Agent": os.getenv("USER_AGENT", "inventory-bot/1.0")},
        CRIT_MAX=int(os.getenv("CRIT_MAX", 3)),
        LOW_MAX=int(os.getenv("LOW_MAX", 10)),
        THRESHOLD=int(os.getenv("THRESHOLD", 3)),
        TIMEZONE=os.getenv("TIMEZONE", "America/Bogota"),
        SP_TENANT_ID=os.getenv("SP_TENANT_ID", ""),
        SP_CLIENT_ID=os.getenv("SP_CLIENT_ID", ""),
        SP_CLIENT_SECRET=os.getenv("SP_CLIENT_SECRET", ""),
        SP_SITE_ID=os.getenv("SP_SITE_ID", ""),
        SP_PARENT_ITEM_ID=os.getenv("SP_PARENT_ITEM_ID", ""),
        SMTP_HOST=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", 587)),
        SMTP_USER=os.getenv("SMTP_USER", ""),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
        ALERT_RECIPIENTS=[e.strip() for e in os.getenv("ALERT_EMAILS", "").split(",") if e.strip()],
        TEAMS_WEBHOOK_URL=os.getenv("TEAMS_WEBHOOK_URL", ""),
    )
