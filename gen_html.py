import base64, io, json
from PIL import Image

im = Image.open('earth_mix.jpg').convert('RGB')
buf = io.BytesIO()
im.save(buf, format='JPEG', quality=82)
b64 = base64.b64encode(buf.getvalue()).decode()
js = open('three.min.js', encoding='utf-8').read()
geo_js = json.dumps(open('world_slim.json', encoding='utf-8').read())
cam_js = json.dumps(open('world_cams.json', encoding='utf-8').read())

html = open('ui.html', encoding='utf-8').read()
out = html.replace('__THREE__', js).replace('__GEO_JSON__', geo_js).replace('__CAM__', cam_js).replace('__IMG__', b64)
open('earth3d.html', 'w', encoding='utf-8').write(out)
print('HTML', len(out))