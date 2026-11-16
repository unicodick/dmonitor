import json
import os
from http.client import HTTPException
from urllib.error import URLError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

PAGE_URL = "https://datalix.eu/rent-epyc-kvm-server"


def get_servers():
    with urlopen(PAGE_URL, timeout=30) as response:
        soup = BeautifulSoup(response.read(), "html.parser")

    servers = []
    for card in soup.select("#service_display_voxility > .dx-card"):
        sold_out = "sold out" in card.get_text(" ", strip=True).lower()
        order_link = card.select_one(
            'a[href]:not([href=""]):not([href^="#"]):not([disabled]):not([aria-disabled="true"])'
        )
        if not sold_out and order_link is None:
            return []
        servers.append({
            "name": card.select_one("h3").get_text(strip=True),
            "price": card.select_one(".dx-price").get_text(strip=True),
            "available": not sold_out,
        })

    return servers


def send_telegram(servers):
    text = "Dlix EPYС:\n\n" + "\n".join(
        f"{server['name']} : {server['price']}" for server in servers
    ) + f"\n\n{PAGE_URL}"
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=30):
        pass


def main():
    try:
        servers = get_servers()
        available = [server for server in servers if server["available"]]
        if available:
            send_telegram(available)
    except (URLError, TimeoutError, ConnectionError, HTTPException):
        pass


if __name__ == "__main__":
    main()
