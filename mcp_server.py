"""earth-now 的 MCP 入口。

机位表只读同目录下的 world_cams.json；卫星图实时抓 NOAA GOES-19 的公开 CDN。都不需要 API key。
运行：python mcp_server.py            （stdio，默认）
     TRANSPORT=streamable-http python mcp_server.py
"""
import json
import math
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from mcp.server.fastmcp import FastMCP

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "world_cams.json")

mcp = FastMCP("earth-now")


# --- 卫星图（NOAA GOES-19 GEOCOLOR）---
SAT_BASE = "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR"
SAT_SIZES = (339, 678, 1808, 5424, 10848)
SAT_OUT = Path(os.environ.get("EARTH_NOW_OUT", "/sdcard/Download"))
SAT_UA = {"User-Agent": "earth-now/1.30"}

def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=SAT_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def _save(data: bytes, name: str) -> str:
    SAT_OUT.mkdir(parents=True, exist_ok=True)
    path = SAT_OUT / name
    path.write_bytes(data)
    return str(path)

_cams = None


def cams():
    global _cams
    if _cams is None:
        with open(DATA, encoding="utf-8") as f:
            _cams = json.load(f)
    return _cams


def slim(c, dist=None):
    out = {
        "id": c.get("id"),
        "title": c.get("t"),
        "city": c.get("c"),
        "region": c.get("r"),
        "country": c.get("co"),
        "lat": c.get("la"),
        "lon": c.get("lo"),
        "kind": "city" if c.get("k") == "c" else "nature",
        "hd": bool(c.get("hd")),
        "image": c.get("img"),
    }
    if dist is not None:
        out["distance_km"] = round(dist, 1)
    return out



COUNTRY_ALIAS = {
    "CA": ["CANADA", "加拿大"], "JP": ["JAPAN", "日本"], "US": ["UNITED STATES", "USA", "AMERICA", "美国"],
    "CN": ["CHINA", "中国"], "GB": ["UNITED KINGDOM", "UK", "BRITAIN", "英国"], "FR": ["FRANCE", "法国"],
    "DE": ["GERMANY", "德国"], "IT": ["ITALY", "意大利"], "ES": ["SPAIN", "西班牙"], "PT": ["PORTUGAL", "葡萄牙"],
    "GR": ["GREECE", "希腊"], "AT": ["AUSTRIA", "奥地利"], "CH": ["SWITZERLAND", "瑞士"], "NL": ["NETHERLANDS", "HOLLAND", "荷兰"],
    "SE": ["SWEDEN", "瑞典"], "NO": ["NORWAY", "挪威"], "FI": ["FINLAND", "芬兰"], "DK": ["DENMARK", "丹麦"],
    "PL": ["POLAND", "波兰"], "CZ": ["CZECH", "CZECHIA", "捷克"], "RU": ["RUSSIA", "俄罗斯"], "IS": ["ICELAND", "冰岛"],
    "IE": ["IRELAND", "爱尔兰"], "AU": ["AUSTRALIA", "澳大利亚"], "NZ": ["NEW ZEALAND", "新西兰"],
    "KR": ["SOUTH KOREA", "KOREA", "韩国"], "TH": ["THAILAND", "泰国"], "MY": ["MALAYSIA", "马来西亚"],
    "VN": ["VIETNAM", "越南"], "ID": ["INDONESIA", "印度尼西亚"], "PH": ["PHILIPPINES", "菲律宾"], "SG": ["SINGAPORE", "新加坡"],
    "IN": ["INDIA", "印度"], "IL": ["ISRAEL", "以色列"], "TR": ["TURKEY", "TURKIYE", "土耳其"], "EG": ["EGYPT", "埃及"],
    "MA": ["MOROCCO", "摩洛哥"], "KE": ["KENYA", "肯尼亚"], "ZA": ["SOUTH AFRICA", "南非"], "MX": ["MEXICO", "墨西哥"],
    "BR": ["BRAZIL", "巴西"], "CL": ["CHILE", "智利"], "AR": ["ARGENTINA", "阿根廷"], "TW": ["TAIWAN", "台湾"],
}

def _cc(country: str) -> str:
    q = country.strip().upper()
    if len(q) == 2 and any(c.get("co") == q for c in cams()):
        return q
    for code, names in COUNTRY_ALIAS.items():
        if q == code or q in names:
            return code
    return q


def _fuzzy(q: str):
    hits = []
    for c in cams():
        blob = " ".join(str(c.get(k) or "") for k in ("t", "c", "r")).upper()
        if q in blob:
            hits.append(c)
    return hits
def km(a, b, c, d):
    dy = (a - c) * 111.0
    dx = (b - d) * 111.0 * math.cos(math.radians((a + c) / 2))
    return math.hypot(dx, dy)


@mcp.tool()
def list_countries() -> list[dict]:
    """列出所有已接入实时机位的国家：国家码、机位数、高清机位数。"""
    agg = {}
    for c in cams():
        cc = c.get("co") or "?"
        row = agg.setdefault(cc, {"country": cc, "cams": 0, "hd": 0})
        row["cams"] += 1
        if c.get("hd"):
            row["hd"] += 1
    return sorted(agg.values(), key=lambda r: -r["cams"])


@mcp.tool()
def search_by_country(country: str, limit: int = 20, offset: int = 0,
                      hd_only: bool = False) -> list[dict]:
    """查机位：可传国家码(JP/CA)、英文国名(Japan/Canada)或中文国名(日本/加拿大)。hd_only=True 只看高清源。"""
    q = country.strip().upper()
    cc = _cc(country)
    rows = [c for c in cams() if c.get("co") == cc]
    if not rows and q:
        rows = _fuzzy(q)
    if hd_only:
        rows = [c for c in rows if c.get("hd")]
    rows.sort(key=lambda c: 0 if c.get("hd") else 1)
    return [slim(c) for c in rows[offset:offset + max(1, min(limit, 100))]]


@mcp.tool()
def search_nearby(lat: float, lon: float, radius_km: int = 50,
                  limit: int = 10) -> list[dict]:
    """按经纬度找附近的实时机位，按距离排序，带 distance_km。"""
    r = max(1, min(radius_km, 500))
    hits = []
    for c in cams():
        d = km(lat, lon, c["la"], c["lo"])
        if d <= r:
            hits.append((d, c))
    hits.sort(key=lambda t: (t[0], 0 if t[1].get("hd") else 1))
    return [slim(c, d) for d, c in hits[:max(1, min(limit, 50))]]


@mcp.tool()
def get_cam(cam_id: str) -> dict:
    """按 id 取单个机位的完整信息，含当前截图地址。"""
    for c in cams():
        if str(c.get("id")) == str(cam_id):
            return slim(c)
    raise ValueError("没有这个机位: %s" % cam_id)


@mcp.tool()
def latest_cloud(size: int = 1808) -> str:
    """拿此刻最新的地球全盘云图（GOES-19 GEOCOLOR），返回图片在本机的保存路径。
    size 只能是 339、678、1808、5424、10848，越大越清晰、下载越慢。"""
    if size not in SAT_SIZES:
        raise ValueError(f"size 只支持 {SAT_SIZES}")
    data = _get(f"{SAT_BASE}/{size}x{size}.jpg")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    return _save(data, f"earth_now_{stamp}_{size}.jpg")

@mcp.tool()
def cloud_animation(frames: int = 12, step_minutes: int = 10, size: int = 678) -> str:
    """往回抓若干帧卫星云图拼成 GIF，看云怎么走，返回 GIF 保存路径。
    frames 2-48，step_minutes 每帧间隔分钟数，size 建议 678 或 1808。"""
    if size not in SAT_SIZES:
        raise ValueError(f"size 只支持 {SAT_SIZES}")
    frames = max(2, min(int(frames), 48))
    step_minutes = max(1, int(step_minutes))
    now = datetime.now(timezone.utc)
    now -= timedelta(minutes=now.minute % step_minutes, seconds=now.second, microseconds=now.microsecond)
    shots = []
    for i in range(frames):
        ts = now - timedelta(minutes=step_minutes * i)
        name = ts.strftime("%Y%j%H%M")
        url = f"{SAT_BASE}/{name}_GOES19-ABI-FD-GEOCOLOR-{size}x{size}.jpg"
        try:
            shots.append((name, _get(url, timeout=20)))
        except Exception:
            continue
    if len(shots) < 2:
        raise RuntimeError("这段时间一帧都没抓到，等几分钟再试")
    shots.sort()
    from PIL import Image
    images = [Image.open(BytesIO(d)).convert("RGB") for _, d in shots]
    buf = BytesIO()
    images[0].save(buf, format="GIF", save_all=True, append_images=images[1:],
                    duration=max(80, step_minutes * 40), loop=0)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    return _save(buf.getvalue(), f"earth_now_anim_{stamp}_{len(images)}f.gif")

if __name__ == "__main__":
    mcp.run(transport=os.getenv("TRANSPORT", "stdio"))
