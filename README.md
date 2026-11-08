# earth-now

一颗会自己转的地球，上面钉着 4419 个实时实景机位，分布在 44 个国家。
点一个国家，弹出它的地貌介绍和机位清单；点一个城市，看那儿此刻的样子。

![此刻的地球](assets/preview.jpg)

## 看一下

https://novadd341.github.io/earth-now/

拖一下转动，双指缩放（或者滚轮），点陆地选中国家，点海面看坐标。
点到球上会响一声，点到太空不响。

## 现在有什么

- 4419 个机位，44 国，其中 312 个是 1200×675 的高清源
- 50 个国家配了一段介绍，就算那个国家一个机位都没有，点开也有东西看
- 自然 / 城市两个筛子，能只看来山、湖、海岸，或者只来看街道
- 有高清源的机位会优先展示，标题后面标一个 HD
- 台湾和大陆合并成一个区域画，港澳单列

## 两个 MCP 入口

仓库里两个 server，互不依赖，想用哪个配哪个。

| 文件 | 干什么 | 需要 key |
| --- | --- | --- |
| `mcp_server.py` | 机位表 + 卫星图：国家/附近/单机位/全盘云图/云动图，六工具合一 | 不要 |
| `server.py` | NOAA GOES-19 云图：取此刻全盘、拼成动图 | 不要 |

机位查询只读同目录的 `world_cams.json`；卫星图工具实时抓 NOAA GOES-19 公开 CDN。

| 工具 | 作用 |
| --- | --- |
| `list_countries` | 列出所有国家的机位数和高清数 |
| `search_by_country` | 按国家码、中英文国名查机位，可只筛高清；查不到会按城市名兜底 |
| `search_nearby` | 按经纬度找附近机位，带距离 |
| `get_cam` | 取单个机位的信息和当前截图地址 |
| `latest_cloud` | 此刻最新的 GOES-19 地球全盘云图，存到本机 |
| `cloud_animation` | 回抓多帧卫星云图拼成 GIF，看云怎么走 |

## 安装

Python 3.10 以上。

```bash
git clone https://github.com/Novadd341/earth-now.git
cd earth-now
pip install -r requirements.txt
```

不想预装也行：

```bash
uv run --with mcp python mcp_server.py
```

## 在 MCP 客户端里配置

以 Operit 为例，加一条 stdio 服务：

```json
{
  "earthnow": {
    "command": "uv",
    "args": ["run", "--with", "mcp", "/path/to/earth-now/mcp_server.py"]
  }
}
```

路径要写绝对的。服务 ID 只用字母、数字、下划线，别带连字符，Operit 会静默不加载。

不走 stdio 也行，起个 HTTP 服务：

```bash
FASTMCP_HOST=127.0.0.1 FASTMCP_PORT=8000 TRANSPORT=streamable-http python mcp_server.py
```

然后在客户端里填远程地址 `http://127.0.0.1:8000/mcp`。

接好之后直接说话就行：

- 「奥地利有哪些高清机位」
- 「东京附近 50 公里内有什么能看的」
- 「冰岛此刻什么样」

云图那个入口把 `mcp_server.py` 换成 `server.py` 就行，那个还要 pillow。

## 数据从哪来

机位表来自 Windy Webcams 的公开数据，图片是各家源站自己的实时图。
欧洲那 312 张高清来自 foto-webcam.eu，都是 1200×675，直连就能拿。
日本 285 个还是 640×480，暂时没找到同级公开高清源。
云图来自 NOAA 的 GOES-19，GEOCOLOR 全彩通道，十分钟一张。

```
https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR/
```

## 重新生成网页

`gen_html.py` 把 `ui.html` 和 `world_cams.json` 拼成单文件 `index.html`，
图片和脚本全部内联，所以那个 HTML 有三兆多，但拿下来双击就能开，不用起服务器。

```bash
python gen_html.py
```

## 路线图

- [x] 三级点击：国家 → 城市 → 实景
- [x] 无机位国家也有文字介绍
- [x] 高清源接入与 HD 标注
- [ ] 亚洲的高清源
- [ ] 按时间回溯看同一个机位今天早上什么样
- [ ] 把机位表做成可以每天自动更新的

## 说明

代码 MIT。图片和机位归各家源站，用之前看一眼他们的条款。
