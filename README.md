# earth-now

给我一个时间，我给你那一刻的地球云图。

MCP server，接 NOAA GOES-19 的公开数据源，不用注册、不用 key，装上就能用。

![此刻的地球](assets/preview.jpg)

## 能做什么

| 工具 | 作用 |
| --- | --- |
| `latest_cloud` | 取此刻最新的地球全盘云图，可选出图尺寸 |
| `cloud_animation` | 按十分钟一帧往回抓，拼成一张会动的 GIF，看云怎么走 |

## 安装

需要 Python 3.10 以上。

```bash
git clone https://github.com/Novadd341/earth-now.git
cd earth-now
pip install -r requirements.txt
```

不想预装也行，`uv run --with mcp --with pillow server.py` 会自动把依赖拉进临时环境。

## 在 MCP 客户端里配置

以 Operit 为例，在 MCP 设置里加一条 stdio 服务：

```json
{
  "earth-now": {
    "command": "uv",
    "args": ["run", "--with", "mcp", "--with", "pillow", "/path/to/earth-now/server.py"]
  }
}
```

args 里那个路径要写绝对的。其他客户端同理，能起 stdio 就行。

## 用法

装上以后直接跟模型说话：

- 「看看此刻的地球」
- 「给我最近两小时的云，做成动图」
- 「要清晰一点的，1080 那张」

工具会把图存到 `~/earth-now/out/` 并把路径返回，模型再把它交给你。

## 数据从哪来

NOAA 的 GOES-19 静止卫星，GEOCOLOR 全彩通道，十分钟一张，公开 CDN，不需要任何凭据。

```
https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR/
```

同一套接口还有 `1808x1808.jpg`、`5424x5424.jpg`、`10848x10848.jpg` 这些固定尺寸的图可以直接拿。

## 路线图

- [ ] 按经纬度裁出指定区域，现在只能给全盘
- [ ] 静止卫星拼两个半球，做一张没有拼接缝的全球底图
- [ ] 顺手给当地的公开实景快照，天上一张地上一张

## 说明

数据是 NOAA 的公开产品，图和代码分开算：代码 MIT，图按 NOAA 的使用条款来。

拼图那步依赖 Pillow。除此之外全是标准库。
