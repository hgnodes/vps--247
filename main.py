import asyncio
import threading
import aiohttp
import uvicorn
import os

from config import PING_INTERVAL, DASHBOARD_HOST, DASHBOARD_PORT
from pinger import ping_target
from dashboard import update_status, app
from logger import log


# 🔒 always resolve file relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IPS_FILE = os.path.join(BASE_DIR, "ips.txt")


def load_ips():
    if not os.path.exists(IPS_FILE):
        log(f"❌ ips.txt NOT FOUND at {IPS_FILE}")
        return []

    with open(IPS_FILE, "r") as f:
        ips = [x.strip() for x in f.readlines() if x.strip()]

    return ips


async def ping_once():
    ips = load_ips()

    if not ips:
        log("⚠️ No IPs found in ips.txt (file exists but empty)")
        return

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[ping_target(session, ip) for ip in ips],
            return_exceptions=True
        )

    for ip, ok in zip(ips, results):
        update_status(ip, bool(ok))


async def monitor_loop():
    # instant first ping
    await ping_once()

    while True:
        await asyncio.sleep(PING_INTERVAL)
        await ping_once()


def start_dashboard():
    uvicorn.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT)


def main():
    log("🚀 IDX MONITOR STARTED")
    log(f"📂 Reading IPs from: {IPS_FILE}")

    threading.Thread(target=start_dashboard, daemon=True).start()

    while True:
        try:
            asyncio.run(monitor_loop())
        except Exception as e:
            log(f"🔄 LOOP CRASHED → {e}")


if __name__ == "__main__":
    main()
