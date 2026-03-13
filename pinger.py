import aiohttp
import ssl
from config import TIMEOUT, MAX_FAILS, DISCORD_WEBHOOK
from logger import log

fail_count = {}

# create permissive SSL context (required for csb / cloudflare)
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


def normalize(target):
    target = target.strip().rstrip("/")
    if target.startswith("http://") or target.startswith("https://"):
        return target
    return "https://" + target


async def send_discord(msg):
    if not DISCORD_WEBHOOK:
        return
    async with aiohttp.ClientSession() as s:
        await s.post(
            DISCORD_WEBHOOK,
            json={"content": msg},
            headers={"User-Agent": "IDX-Monitor"}
        )


async def try_url(session, url):
    return await session.get(
        url,
        timeout=TIMEOUT,
        ssl=ssl_ctx,
        headers={"User-Agent": "Mozilla/5.0"}
    )


async def ping_target(session, target):
    base = normalize(target)

    urls_to_try = [
        f"{base}/ping",
        f"{base}/",
    ]

    for url in urls_to_try:
        try:
            async with await try_url(session, url) as r:
                if 200 <= r.status < 400:
                    fail_count[target] = 0
                    log(f"✅ ONLINE → {base}")
                    return True
        except Exception:
            pass

    # failed all attempts
    fail_count[target] = fail_count.get(target, 0) + 1
    log(f"❌ OFFLINE ({fail_count[target]}) → {base}")

    if fail_count[target] == MAX_FAILS:
        await send_discord(f"⚠️ IDX DOWN\n{base}")

    return False
