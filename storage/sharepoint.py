import requests
import logging
from msal import ConfidentialClientApplication

log = logging.getLogger(__name__)


def _get_token(cfg) -> str:
    app = ConfidentialClientApplication(
        cfg.SP_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{cfg.SP_TENANT_ID}",
        client_credential=cfg.SP_CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"Token error: {result.get('error_description')}")
    return result["access_token"]


def upload_to_sharepoint(local_path: str, filename: str, cfg) -> str:
    if not cfg.SP_CLIENT_ID:
        log.warning("SharePoint no configurado, omitiendo upload.")
        return ""

    token = _get_token(cfg)
    url = (
        f"https://graph.microsoft.com/v1.0/sites/{cfg.SP_SITE_ID}"
        f"/drive/items/{cfg.SP_PARENT_ITEM_ID}:/{filename}:/content"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    with open(local_path, "rb") as f:
        resp = requests.put(url, headers=headers, data=f, timeout=60)
    resp.raise_for_status()
    web_url = resp.json().get("webUrl", "")
    log.info(f"Subido: {web_url}")
    return web_url


def download_latest_from_sharepoint(cfg) -> "pd.DataFrame":
    import pandas as pd
    token = _get_token(cfg)
    headers = {"Authorization": f"Bearer {token}"}
    url = (
        f"https://graph.microsoft.com/v1.0/sites/{cfg.SP_SITE_ID}"
        f"/drive/items/{cfg.SP_PARENT_ITEM_ID}/children"
        f"?$orderby=lastModifiedDateTime desc&$top=1"
    )
    items = requests.get(url, headers=headers, timeout=30).json()
    dl_url = items["value"][0]["@microsoft.graph.downloadUrl"]
    return pd.read_excel(dl_url)
