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


if __name__ == "__main__":
    mcp.run(transport=os.getenv("TRANSPORT", "stdio"))
