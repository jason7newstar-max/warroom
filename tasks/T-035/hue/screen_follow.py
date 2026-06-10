import json,os,ssl,urllib.request,subprocess,colorsys,time
from PIL import Image
d=json.load(open(os.path.expanduser('~/.phantom/hue.json')))
ip,key=d['ip'],d['appkey']
ctx=ssl.create_default_context();ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE
def v1(p,b):
    req=urllib.request.Request(f"https://{ip}/api/{key}{p}",data=json.dumps(b).encode(),method="PUT")
    try: urllib.request.urlopen(req,timeout=4,context=ctx)
    except Exception: pass
LIGHTS=["5","6","7","9"]
def dominant():
    subprocess.run(["screencapture","-x","-t","jpg","-r","/tmp/scr.jpg"],
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    im=Image.open("/tmp/scr.jpg").convert("RGB").resize((48,30))
    px=list(im.getdata())
    # weight toward saturated pixels so the lights pick up real color, not grey UI
    best=(0,0,0); bs=-1; r=g=b=n=0
    for (R,G,B) in px:
        h,s,v=colorsys.rgb_to_hsv(R/255,G/255,B/255)
        r+=R;g+=G;b+=B;n+=1
        if s*v>bs: bs=s*v; best=(R,G,B)
    avg=(r//n,g//n,b//n)
    # blend avg + most-vivid
    return tuple(int(0.45*a+0.55*c) for a,c in zip(avg,best))
print("screen-follow START 30s")
import sys
for _ in range(40):
    R,G,B=dominant()
    h,s,v=colorsys.rgb_to_hsv(R/255,G/255,B/255)
    hue=int(h*65535); sat=int(min(254,s*254+40)); bri=int(min(254,max(60,v*254)))
    for i in LIGHTS: v1(f"/lights/{i}/state",{"on":True,"hue":hue,"sat":sat,"bri":bri,"transitiontime":3})
    print(f"screen RGB({R},{G},{B}) -> hue{hue} sat{sat} bri{bri}",flush=True)
    time.sleep(0.75)
print("screen-follow DONE")
