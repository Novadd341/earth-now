"""earth-now 的 MCP 入口。

只读同目录下的 world_cams.json，不发任何外部请求，不需要任何 API key。
运行：python mcp_server.py            （stdio，默认）
     TRANSPORT=streamable-http python mcp_server.py
"""
import json
import math
import os

from mcp.server.fastmcp import FastMCP

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "world_cams.json")

mcp = FastMCP("earth-now")
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
    """按国家码查机位，如 JP / AT / IS。hd_only=True 只看高清源。"""
    cc = country.upper()
    rows = [c for c in cams() if c.get("co") == cc]
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


if __name__ == "__main__":
    mcp.run(transport=os.getenv("TRANSPORT", "stdio"))
