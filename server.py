"""earth-now: 给我一个时间，我给你那一刻的地球云图。

数据源是 NOAA GOES-19 的 GEOCOLOR 全盘图，公开 CDN，不需要凭据。
"""

from __future__ import annotations

import os
import urllib.request
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from PIL import Image

BASE = "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR"
OUT = Path(os.environ.get("EARTH_NOW_OUT", str(Path.home() / "earth-now" / "out")))
UA = {"User-Agent": "earth-now/0.1"}
SIZES = (339, 678, 1808, 5424, 10848)

mcp = FastMCP("earth-now")


def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _save(data: bytes, name: str) -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_bytes(data)
    return str(path)


@mcp.tool()
def latest_cloud(size: int = 1808) -> str:
    """拿此刻最新的地球全盘云图，返回图片在本机的保存路径。

    size 只能是 339、678、1808、5424、10848，越大越清晰、下载也越慢。
    """
    if size not in SIZES:
        raise ValueError(f"size 只支持 {SIZES}")
    data = _get(f"{BASE}/{size}x{size}.jpg")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    return _save(data, f"earth_now_{stamp}_{size}.jpg")


@mcp.tool()
def cloud_animation(frames: int = 12, step_minutes: int = 10, size: int = 678) -> str:
    """往回抓若干帧拼成一张 GIF，看云在这段时间里怎么走，返回 GIF 路径。

    frames 是帧数（2 到 48），step_minutes 是每帧间隔的分钟数，size 建议 678 或 1808。
    """
    if size not in SIZES:
        raise ValueError(f"size 只支持 {SIZES}")
    frames = max(2, min(int(frames), 48))
    step_minutes = max(1, int(step_minutes))

    now = datetime.now(timezone.utc)
    now -= timedelta(
        minutes=now.minute % step_minutes,
        seconds=now.second,
        microseconds=now.microsecond,
    )

    shots: list[tuple[str, bytes]] = []
    for i in range(frames):
        ts = now - timedelta(minutes=step_minutes * i)
        name = ts.strftime("%Y%j%H%M")
        url = f"{BASE}/{name}_GOES19-ABI-FD-GEOCOLOR-{size}x{size}.jpg"
        try:
            shots.append((name, _get(url, timeout=20)))
        except Exception:
            # 中间缺一帧不影响整体，静默跳过
            continue

    if len(shots) < 2:
        raise RuntimeError("这段时间一帧都没抓到，等几分钟再试")

    shots.sort()
    images = [Image.open(BytesIO(d)).convert("RGB") for _, d in shots]
    buf = BytesIO()
    images[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=max(80, step_minutes * 40),
        loop=0,
    )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    return _save(buf.getvalue(), f"earth_now_anim_{stamp}_{len(images)}f.gif")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()