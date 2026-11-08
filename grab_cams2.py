import httpx, json, time

key = None
for line in open('/home/elsewhere/elsewhere-mcp-main/.env'):
    if 'WINDY' in line and '=' in line:
        key = line.split('=', 1)[1].strip().strip('"').strip("'")

CC = ['US','GB','DE','FR','IT','ES','NL','AT','CH','PT','PL','CZ','GR','NO','SE',
      'FI','DK','IE','TR','RU','IS','CN','TW','KR','TH','SG','MY','ID','VN',
      'PH','IN','AE','SA','IL','EG','ZA','MA','KE','BR','AR','CL','MX','CA','AU','NZ','JP']

NAT = {'landscape','mountain','beach','coast','forest','lake','river','village'}

def page(cc, off, cats=None):
    p = {'countries': cc, 'include': 'location,images,categories',
         'limit': 50, 'offset': off}
    if cats: p['categories'] = cats
    for _ in range(2):
        try:
            r = httpx.get('https://api.windy.com/webcams/api/v3/webcams',
                          params=p, headers={'x-windy-api-key': key}, timeout=15)
            if r.status_code == 200:
                d = r.json()
                return d.get('webcams', []), d.get('total', 0)
            print('  !', cc, off, cats, r.status_code, flush=True)
        except Exception as e:
            print('  !', cc, off, type(e).__name__, flush=True)
        time.sleep(1)
    return [], 0

out, seen = [], set()
stat = {}

def add(ws):
    n = 0
    for w in ws:
        if w.get('status') != 'active': continue
        if not ((w.get('images') or {}).get('current') or {}).get('preview'): continue
        wid = w.get('webcamId')
        if wid is None or wid in seen: continue
        seen.add(wid)
        loc = w.get('location') or {}
        cs = [c.get('id') for c in (w.get('categories') or []) if isinstance(c, dict)]
        kind = 'n' if any(c in NAT for c in cs) else 'c'
        out.append({'id': wid, 't': w.get('title'), 'c': loc.get('city'),
                    'r': loc.get('region'), 'la': loc.get('latitude'),
                    'lo': loc.get('longitude'), 'k': kind,
                    'img': 'https://imgproxy.windy.com/_/full/plain/current/%s/original.jpg?v=2' % wid,
                    'co': w['_cc']})
        n += 1
    return n

for i, cc in enumerate(CC):
    got = 0
    for off in (0, 50):
        ws, tot = page(cc, off)
        for w in ws: w['_cc'] = cc
        got += add(ws)
        if len(ws) < 50: break
        time.sleep(0.1)
    ws, tot = page(cc, 0, 'landscape')
    for w in ws: w['_cc'] = cc
    got += add(ws)
    if cc == 'JP':
        for off in (50, 100, 150, 200, 250):
            ws, tot = page(cc, off)
            for w in ws: w['_cc'] = cc
            got += add(ws)
            if len(ws) < 50: break
            time.sleep(0.1)
    stat[cc] = got
    if (i + 1) % 6 == 0:
        json.dump(out, open('/home/elsewhere/world_cams.json', 'w'), separators=(',', ':'))
        print('...', i + 1, 'total', len(out), flush=True)

json.dump(out, open('/home/elsewhere/world_cams.json', 'w'), separators=(',', ':'))
nat = sum(1 for x in out if x['k'] == 'n')
print('TOTAL', len(out), 'nature', nat, 'city', len(out) - nat, 'size', len(json.dumps(out)), flush=True)
print('countries', len(stat), flush=True)
print({k: v for k, v in stat.items()}, flush=True)