"""Build narrated product-photo explainers locally; no generative model or API.
Usage: python cards.py manifest.json
Images stay identifiable as product photographs. Diagrams are not benchmarks.
"""
import json,math,subprocess,sys
from pathlib import Path
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFont,ImageOps
import studio

def build(manifest):
    p=Path(manifest).resolve();m=studio.read(p);base=p.parent
    dest=(base/m['output_dir']).resolve()
    if dest.exists():raise ValueError('Output directory exists; choose a new version')
    product=Image.open(base/m['image']).convert('RGB')
    font_path=(base/m['font_file']).resolve() if m.get('font_file') else studio.ROOT/'assets/fonts/Paperlogy-7Bold.ttf'
    width,height=1080,1920;fps=24
    @lru_cache(None)
    def font(size):return ImageFont.truetype(str(font_path),size)
    @lru_cache(None)
    def product_size(size):return ImageOps.contain(product,(size,size),Image.Resampling.LANCZOS)
    accent='#B9F5D8';bg='#101820';white='#F5F7F9';muted='#A8BAC6'
    def text(d,xy,s,size,fill=white):d.text(xy,s,font=font(size),fill=fill,spacing=16)
    # Validate everything before any render to avoid partial output from missing inputs.
    prepared=[]
    for scene in m['scenes']:
        audio=(base/scene['voice']).resolve();duration=float(studio.probe(audio)['format']['duration'])+.22
        if len(scene['lines'])>3:raise ValueError('Use at most three concise information lines')
        if len(scene.get('steps',[]))>3:raise ValueError('Use at most three step labels')
        for line in scene['title'].split('\n'):
            if font(76).getlength(line)>920:raise ValueError('Title too long; insert a line break')
        for line in scene['lines']:
            if font(45).getlength(line)>880:raise ValueError('Information line too long')
        prepared.append((scene,audio,duration))
    dest.mkdir(parents=True);timeline=[];captions=[];cursor=0
    for index,(scene,audio,duration) in enumerate(prepared):
        id=f'{index+1:02}';raw=dest/f'{id}-silent.mp4';out=dest/f'{id}.mp4'
        count=math.ceil(duration*fps);duration=count/fps
        canvas=Image.new('RGB',(width,height),bg);d=ImageDraw.Draw(canvas)
        d.rounded_rectangle((68,70,440,126),radius=28,fill=accent)
        text(d,(91,80),'구매 전 확인',32,bg);text(d,(900,80),id+' / '+f'{len(prepared):02}',24,muted)
        text(d,(74,169),m['product_name'],41);text(d,(74,229),m.get('model',''),28,muted)
        text(d,(72,300),scene['title'],76)
        d.rounded_rectangle((134,505,946,1317),radius=32,fill='white')
        picture=product_size(760);canvas.paste(picture,((width-picture.width)//2,531+(760-picture.height)//2))
        d.rounded_rectangle((68,1370,1012,1580),radius=24,fill='#1D2C38')
        for n,line in enumerate(scene['lines']):text(d,(100,1395+n*62),line,45,accent if n==0 else white)
        text(d,(74,1775),m.get('footer','상품 사진·설명용 화면 | 실제 성능 측정 아님'),26,muted)
        text(d,(74,1820),'제휴 링크 구매 시 수수료를 받을 수 있습니다',26,muted)
        cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r',str(fps),'-i','-','-an','-c:v','libx264','-threads','4','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(raw)]
        with (dest/f'{id}.log').open('w') as log:
            proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
            try:
                for i in range(count):
                    frame=canvas.copy();draw=ImageDraw.Draw(frame);u=i/max(1,count-1)
                    # An explicit reading guide, not fake hardware performance.
                    draw.rounded_rectangle((74,1660,1006,1680),radius=10,fill='#263B48')
                    draw.rounded_rectangle((74,1660,74+max(20,int(932*u)),1680),radius=10,fill=accent)
                    for n,label in enumerate(scene.get('steps',[])):
                        x=90+n*245;active=int(u*len(scene['steps']))>=n
                        draw.ellipse((x,1610,x+18,1628),fill=accent if active else '#40515D')
                        text(draw,(x+28,1602),label,26,white if active else muted)
                    proc.stdin.write(frame.tobytes())
            finally:proc.stdin.close();rc=proc.wait()
            if rc:raise RuntimeError('Card rendering failed; inspect scene log')
        subprocess.run(['ffmpeg','-n','-hide_banner','-loglevel','error','-i',str(raw),'-i',str(audio),'-map','0:v','-map','1:a','-c:v','copy','-af',f'apad,atrim=duration={duration}','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)],check=True)
        timeline.append({'path':str(out),'in':0,'out':duration})
        # A brief question at the start only; information cards remain readable below.
        if index==0:captions.append({'start':0,'end':min(4.2,duration),'lines':['사진보다 선택 옵션'],'highlight':0,'y':1728,'size':58})
        cursor+=duration;print(json.dumps({'scene':id,'duration':duration,'output':str(out)},ensure_ascii=False),flush=True)
    result={'output':str(dest.parent/m.get('final_output','product-review.mp4')),'speed':m.get('speed',1.4),'minimum_duration':m.get('minimum_duration',50),
            'fonts_dir':str(font_path.parent),'clips':timeline,'captions':captions}
    studio.write(dest/'timeline.json',result)
    return {'timeline':str(dest/'timeline.json'),'source_duration':cursor,'final_duration_expected':cursor/result['speed'],'generated_scene':False,'product_photo_explainer':True}

if __name__=='__main__':
    try:studio.emit(build(sys.argv[1]))
    except Exception as e:print(json.dumps({'error':str(e)},ensure_ascii=False),file=sys.stderr);sys.exit(1)
