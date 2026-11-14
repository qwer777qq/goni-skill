"""Independent reconstruction of observed video editing behavior. No generation API."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, math, mimetypes, os, re
import shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,data):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_name(p.name+'.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(temp,p)
def emit(x): print(json.dumps(x,ensure_ascii=False,indent=2))
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def finite(n):
    n=float(n)
    if not math.isfinite(n): raise ValueError('Non-finite time or speed')
    return n
def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],encoding='utf-8'))
def media(path):
    info=probe(path); v=next((x for x in info['streams'] if x['codec_type']=='video'),None)
    if v is None: raise ValueError('Video stream required')
    return info,v
def stamp(t):
    n=round(t*100); return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'
def safe_text(s):
    return str(s).replace('\\','／').replace('{','（').replace('}','）').replace('\r',' ').replace('\n',' ')
def tempo(speed):
    parts=[]
    while speed>2: parts.append('atempo=2'); speed/=2
    while speed<.5: parts.append('atempo=0.5'); speed/=.5
    parts.append(f'atempo={speed:.10g}'); return ','.join(parts)
def ass_color(value):
    if not re.fullmatch(r'#[0-9A-Fa-f]{6}',value):raise ValueError('Color must be #RRGGBB')
    return '&H00'+value[5:7]+value[3:5]+value[1:3]
def captions(rows,style,speed,duration):
    head=f'''[Script Info]
ScriptType: v4.00+
PlayResX: {style['width']}
PlayResY: {style['height']}
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{style['font']},{style['font_size']},{style['primary_ass']},&H000000FF,{style['outline_ass']},&H80000000,0,0,0,0,100,100,0,0,1,{style['outline']},{style['shadow']},5,70,140,80,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    out=[]
    for r in rows:
        start,end=finite(r['start'])/speed,finite(r['end'])/speed
        if not 0<=start<end<=duration+.05: raise ValueError('Caption outside final timeline')
        presets=read(ROOT/'assets/text-presets.json')['presets']
        if r.get('preset','original') not in presets:raise ValueError('Unknown caption preset')
        preset=presets[r.get('preset','original')]
        r={**preset,**r}
        lines=[safe_text(s) for s in r.get('lines',[r.get('text','')])]; highlight=r.get('highlight',-1)
        primary=ass_color(r['color']) if 'color' in r else style['primary_ass']
        hi=ass_color(r['highlight_color']) if 'highlight_color' in r else style['highlight_ass']
        def text_for(limit=None):
            parts=[];remaining=limit
            for j,line in enumerate(lines):
                part=line if remaining is None else line[:max(0,remaining)]
                parts.append('{\\1c'+(hi if j==highlight else primary)+'&}'+part)
                if remaining is not None:remaining-=len(line)
            return '\\N'.join(parts)
        y=finite(r.get('y',style['default_y'])); size=finite(r.get('size',style['font_size']))
        x=finite(r.get('x',style['x']));family=r.get('font',style['font'])
        if not re.fullmatch(r'[\w .-]+',family):raise ValueError('Invalid cue font')
        if not 0<=y<=style['height'] or not 0<=x<=style['width'] or not 8<=size<=220: raise ValueError('Invalid caption geometry')
        fade=style['fade_ms']; fi=0 if start==0 else fade
        animation=r.get('animation','original-pop')
        position=f'\\pos({x:g},{y:g})';motion=''
        if animation=='original-pop':motion=f'\\fad({fi},{fade})\\fscx94\\fscy94\\t(0,120,\\fscx103\\fscy103)\\t(120,200,\\fscx100\\fscy100)'
        elif animation=='fade':motion='\\fad(180,180)'
        elif animation=='slide-up':position=f'\\move({x:g},{y+65:g},{x:g},{y:g},0,250)';motion='\\fad(100,120)'
        elif animation=='slide-left':position=f'\\move({x-180:g},{y:g},{x:g},{y:g},0,250)';motion='\\fad(100,120)'
        elif animation=='zoom':motion='\\fscx70\\fscy70\\t(0,250,\\fscx100\\fscy100)\\fad(80,120)'
        elif animation=='bounce':motion='\\fscx60\\fscy60\\t(0,180,\\fscx112\\fscy112)\\t(180,300,\\fscx96\\fscy96)\\t(300,420,\\fscx100\\fscy100)'
        elif animation not in ['static','typewriter']:raise ValueError('Unknown caption animation')
        tag=f"{{\\an5{position}\\fn{family}\\b{1 if r.get('bold') else 0}\\fs{size:g}{motion}}}"
        def event(a,b,text):return f'Dialogue: 0,{stamp(a)},{stamp(b)},Caption,,0,0,0,,{tag}{text}'
        if animation=='typewriter':
            n=sum(map(len,lines))
            if not 1<=n<=120:raise ValueError('Typewriter needs 1–120 characters')
            reveal=min((end-start)*.6,n*.05)
            if reveal/n<.01:raise ValueError('Typewriter cue too short for its text')
            for j in range(1,n+1):out.append(event(start+(j-1)*reveal/n,start+j*reveal/n if j<n else end,text_for(j)))
        else:out.append(event(start,end,text_for()))
    return head+'\n'.join(out)+'\n'

def render(manifest,dry_run=False):
    m=read(manifest); base=Path(manifest).resolve().parent
    style=read(ROOT/'assets/owner-review-style.json')
    style.update(m.get('style',{}))
    if not re.fullmatch(r'[\w .-]+',style['font']): raise ValueError('Invalid font family')
    speed=finite(m.get('speed',1))
    if not .125<=speed<=8: raise ValueError('Speed must be 0.125–8')
    clips=m.get('clips',[])
    if not clips: raise ValueError('At least one clip required')
    total=0; validated=[]; sources=[]
    for c in clips:
        source=(base/c['path']).resolve(); info,v=media(source)
        start=finite(c.get('in',0)); end=finite(c.get('out',info['format']['duration']))
        if not 0<=start<end<=float(info['format']['duration'])+.05: raise ValueError('Invalid source trim')
        if abs(v['width']/v['height']-style['width']/style['height'])>.01:
            raise ValueError('Aspect ratio mismatch; prepare explicit composition before rendering')
        total+=end-start; sources.append(source)
        validated.append((source,start,end,any(s['codec_type']=='audio' for s in info['streams'])))
    duration=total/speed; minimum=finite(m.get('minimum_duration',0))
    if duration+.001<minimum: raise ValueError(f'Final duration {duration:.3f}s below {minimum}s; more genuine footage required')
    out=(base/m['output']).resolve()
    if out in sources or out.exists(): raise ValueError('Output exists or aliases a source; choose a new output')
    fonts=(base/m['fonts_dir']).resolve() if m.get('fonts_dir') else ROOT/'assets/fonts'
    font_files=[f for f in fonts.iterdir() if f.suffix.lower() in ['.ttf','.otf']] if fonts.is_dir() else []
    if not font_files: raise ValueError('No TTF/OTF fonts available')
    ass=captions(m.get('captions',[]),style,speed,duration)
    result={'duration_before_speed':total,'speed':speed,'expected_final_duration':duration,'output':str(out),'clips':len(clips),'caption_time_basis':'pre-speed assembled timeline'}
    if dry_run: return result
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='goni-render-',dir=out.parent) as tmp:
        tmp=Path(tmp); (tmp/'captions.ass').write_text(ass,encoding='utf-8-sig')
        (tmp/'fonts').mkdir()
        for f in font_files: shutil.copy2(f,tmp/'fonts'/f.name)
        cmd=['ffmpeg','-y','-hide_banner','-threads','4']; graph=[]; cats=[]
        for i,(source,start,end,has_audio) in enumerate(validated):
            cmd+=['-i',str(source)]
            graph.append(f'[{i}:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,scale={style["width"]}:{style["height"]}:flags=lanczos,setsar=1,fps=30,format=yuv420p[v{i}]')
            if has_audio: graph.append(f'[{i}:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={end-start}[a{i}]')
            else: graph.append(f'anullsrc=r=48000:cl=stereo,atrim=duration={end-start}[a{i}]')
            cats.extend([f'[v{i}]',f'[a{i}]'])
        graph.append(''.join(cats)+f'concat=n={len(clips)}:v=1:a=1[v][a]')
        graph.append(f'[v]setpts=(PTS-STARTPTS)/{speed},fps=30,ass=captions.ass:fontsdir=fonts[outv]')
        graph.append(f'[a]{tempo(speed)},loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[outa]')
        cmd+=['-filter_complex_threads','4','-filter_complex',';'.join(graph),'-map','[outv]','-map','[outa]','-c:v','libx264','-threads','4','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
        with out.with_suffix('.render.log').open('w',encoding='utf-8') as log:
            subprocess.run(cmd,cwd=tmp,stdout=log,stderr=log,check=True)
        shutil.copy2(tmp/'captions.ass',out.with_suffix('.ass'))
    info,v=media(out); result['actual_duration']=float(info['format']['duration'])
    result['dimensions']=[v['width'],v['height']]
    if result['actual_duration']+.05<minimum: raise ValueError('Rendered duration failed minimum')
    write(out.with_suffix('.render.json'),result); return result

def inspect(path,decode=False,output=None):
    p=Path(path).resolve(); info,v=media(p)
    result={'path':str(p),'duration':float(info['format']['duration']),'width':v['width'],'height':v['height'],'fps':v.get('avg_frame_rate'),'video_codec':v['codec_name'],'audio_present':any(x['codec_type']=='audio' for x in info['streams']),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'human_listening':False,'continuous_visual_review':False}
    if decode:
        r=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
        result['decode_exit_code']=r.returncode; result['decode_errors']=r.stderr.strip()
    if output: write(output,result)
    return result

def frames_export(path,directory,count=12):
    info,_=media(path);duration=float(info['format']['duration']);dest=Path(directory).resolve()
    if dest.exists(): raise ValueError('Frame directory exists; choose a new directory')
    if not 2<=count<=120: raise ValueError('Frame count must be 2–120')
    dest.mkdir(parents=True);rows=[]
    for i in range(count):
        t=i*max(0,duration-.1)/(count-1);out=dest/f'frame_{i:03}.jpg'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(t),'-i',str(Path(path).resolve()),'-frames:v','1','-q:v','2',str(out)],check=True)
        rows.append({'time':t,'file':out.name})
    write(dest/'frames.json',rows);return {'directory':str(dest),'frames':len(rows),'naturalness_verified':False}

def screen_compose(manifest):
    import cv2,numpy as np
    m=read(manifest);base=Path(manifest).resolve().parent
    if m.get('fixed_camera_confirmed') is not True: raise ValueError('Fixed camera must be checked; this compositor does not track moving screens')
    src=(base/m['source']).resolve();ui=(base/m['screen']).resolve();out=(base/m['output']).resolve()
    if out.exists() or out in [src,ui]: raise ValueError('Output exists or aliases input')
    info,v=media(src);si,sv=media(ui);width,height=v['width'],v['height']
    duration=finite(m.get('duration',info['format']['duration']))
    if not 0<duration<=min(float(info['format']['duration']),float(si['format']['duration']))+.01: raise ValueError('Screen and source must cover the entire requested duration; no automatic loop')
    q=np.asarray(m['corners'],dtype=np.float32)
    if q.shape!=(4,2) or not np.isfinite(q).all() or not cv2.isContourConvex(q.astype(np.int32)) or abs(cv2.contourArea(q))<16:
        raise ValueError('corners must describe a convex TL,TR,BR,BL screen')
    if np.any(q<0) or np.any(q[:,0]>=width) or np.any(q[:,1]>=height): raise ValueError('Corners outside source frame')
    brightness=finite(m.get('brightness',1));offset=finite(m.get('offset',0))
    if not 0<brightness<=2 or not -255<=offset<=255: raise ValueError('Invalid screen brightness')
    mask=np.zeros((height,width),np.uint8);cv2.fillConvexPoly(mask,q.astype(np.int32),255)
    for polygon in m.get('protected_polygons',[]):
        points=np.asarray(polygon,dtype=np.int32)
        if points.ndim!=2 or points.shape[1]!=2 or len(points)<3: raise ValueError('Invalid protected polygon')
        cv2.fillPoly(mask,[points],0)
    alpha=cv2.GaussianBlur(mask,(3,3),.55).astype(np.float32)[:,:,None]/255
    matrix=cv2.getPerspectiveTransform(np.float32([[0,0],[sv['width']-1,0],[sv['width']-1,sv['height']-1],[0,sv['height']-1]]),q)
    fps_num,fps_den=map(float,v['avg_frame_rate'].split('/'));fps=fps_num/fps_den
    sf_num,sf_den=map(float,sv['avg_frame_rate'].split('/'));screen_fps=sf_num/sf_den
    count=round(duration*fps);cv2.setNumThreads(4);out.parent.mkdir(parents=True,exist_ok=True)
    a=cv2.VideoCapture(str(src));b=cv2.VideoCapture(str(ui));ui_index=-1;screen=None
    try:
        with tempfile.TemporaryDirectory(prefix='goni-compose-',dir=out.parent) as td:
            temp=Path(td)/'composite.mp4'
            cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{width}x{height}','-r',str(fps),'-i','-','-an','-c:v','libx264','-threads','4','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(temp)]
            with out.with_suffix('.compose.log').open('w',encoding='utf-8') as log:
                proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
                try:
                    for i in range(count):
                        ok,frame=a.read()
                        if not ok: raise ValueError('Source ended before expected frame count')
                        target=int(i*screen_fps/fps)
                        while ui_index<target:
                            ok,screen=b.read();ui_index+=1
                            if not ok: raise ValueError('Screen clip ended early')
                        screen_adjusted=np.clip(cv2.GaussianBlur(screen,(3,3),.45).astype(np.float32)*brightness+offset,0,255).astype(np.uint8)
                        warped=cv2.warpPerspective(screen_adjusted,matrix,(width,height))
                        result=np.clip(frame*(1-alpha)+warped*alpha,0,255).astype(np.uint8)
                        proc.stdin.write(result.tobytes())
                finally:
                    proc.stdin.close();rc=proc.wait()
                if rc: raise RuntimeError('Composite encoding failed; inspect local log')
            subprocess.run(['ffmpeg','-n','-hide_banner','-loglevel','error','-i',str(temp),'-i',str(src),'-map','0:v:0','-map','1:a:0?','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(count/fps),'-movflags','+faststart',str(out)],check=True)
    finally:a.release();b.release()
    result={'output':str(out),'frames':count,'duration':count/fps,'source_audio_preserved':True,'corners':q.tolist(),
            'protected_polygon_count':len(m.get('protected_polygons',[])),'actual_device_recording':False,'method':'independently authored fixed-camera perspective replacement; manual geometry'}
    write(out.with_suffix('.compose.json'),result);return result

def align_voice(reference,generated,segments,output):
    """Measured timing suggestion only; never claims speech or lip-sync equivalence."""
    import numpy as np
    if Path(output).exists(): raise ValueError('Alignment output exists')
    def envelope(path):
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ac','1','-ar','8000','-f','f32le','-'])
        samples=np.frombuffer(raw,np.float32)
        if len(samples)<80: raise ValueError('Audio too short')
        samples=samples[:len(samples)//80*80].reshape(-1,80)
        return np.sqrt(np.mean(samples*samples,axis=1))
    original=envelope(reference);target=envelope(generated);rows=[]
    for seg in read(segments):
        start,end=finite(seg['start']),finite(seg['end'])
        if not 0<=start<end<=len(original)*.01: raise ValueError('Segment outside reference audio')
        ts=np.arange(start,end,.01);ref=np.interp(ts,np.arange(len(original))*.01,original);ref-=ref.mean()
        best=(-1,1,0)
        for scale in np.arange(.90,1.101,.002):
            for shift in np.arange(-.6,.601,.01):
                times=start+shift+(ts-start)*scale
                if times[0]<0 or times[-1]>=len(target)*.01: continue
                values=np.interp(times,np.arange(len(target))*.01,target);values-=values.mean()
                score=float(values@ref/(np.linalg.norm(values)*np.linalg.norm(ref)+1e-12))
                if score>best[0]:best=(score,float(scale),float(shift))
        correlation,scale,shift=best
        rows.append({'start':start,'end':end,'scale':scale,'shift':shift,'correlation':correlation,'target_start':start+shift,'target_end':start+shift+(end-start)*scale,'atempo_for_reference':1/scale})
    result={'method':'audio-envelope timing suggestions','same_words_verified':False,'lip_sync_verified':False,'segments':rows};write(output,result);return result

def narrate(text_file,output,voice='Microsoft Heami Desktop',rate=0):
    if os.name!='nt': raise ValueError('OS narration requires Windows SAPI; use a local recorded WAV on other systems')
    dest=Path(output).resolve();source=Path(text_file).resolve()
    if dest.exists() or dest==source: raise ValueError('Output exists or aliases input')
    if not -10<=rate<=10: raise ValueError('SAPI rate must be -10 to 10')
    if not source.read_text(encoding='utf-8-sig').strip(): raise ValueError('Narration text is empty')
    dest.parent.mkdir(parents=True,exist_ok=True)
    import win32com.client
    speaker=win32com.client.Dispatch('SAPI.SpVoice')
    voices=speaker.GetVoices();chosen=None
    for i in range(voices.Count):
        token=voices.Item(i)
        if voice in token.GetDescription():chosen=token;break
    if chosen is None:raise ValueError('Requested installed SAPI voice not found')
    speaker.Voice=chosen;speaker.Rate=rate
    stream=win32com.client.Dispatch('SAPI.SpFileStream')
    try:
        stream.Open(str(dest),3,False)
        speaker.AudioOutputStream=stream
        speaker.Speak(source.read_text(encoding='utf-8-sig'),16) # SVSFIsNotXML
    finally:stream.Close()
    info=probe(dest)
    return {'output':str(dest),'duration':float(info['format']['duration']),'voice':voice,'backend':'Windows installed SAPI voice','voice_cloning':False,'provider_charge':0}

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor');sub.add_parser('capabilities');sub.add_parser('fonts');sub.add_parser('presets')
    a=sub.add_parser('render');a.add_argument('manifest');a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('inspect');a.add_argument('path');a.add_argument('--decode',action='store_true');a.add_argument('--output')
    a=sub.add_parser('frames');a.add_argument('path');a.add_argument('directory');a.add_argument('--count',type=int,default=12)
    a=sub.add_parser('compose-screen');a.add_argument('manifest')
    a=sub.add_parser('align-voice');a.add_argument('reference');a.add_argument('generated');a.add_argument('segments');a.add_argument('output')
    a=sub.add_parser('narrate');a.add_argument('text');a.add_argument('output');a.add_argument('--voice',default='Microsoft Heami Desktop');a.add_argument('--rate',type=int,default=0)
    args=p.parse_args()
    if args.command=='doctor':
        import importlib.util
        result={'python':sys.version.split()[0],'ffmpeg':shutil.which('ffmpeg'),'ffprobe':shutil.which('ffprobe'),
                'packages':{k:bool(importlib.util.find_spec(k)) for k in ['numpy','cv2','win32com']},'paid_api_enabled':False,'generative_model_included':False}
    elif args.command=='capabilities':result=read(ROOT/'assets/capabilities.json')
    elif args.command=='fonts':result=read(ROOT/'assets/fonts/manifest.json')
    elif args.command=='presets':result=read(ROOT/'assets/text-presets.json')
    elif args.command=='render':result=render(args.manifest,args.dry_run)
    elif args.command=='inspect':result=inspect(args.path,args.decode,args.output)
    elif args.command=='frames':result=frames_export(args.path,args.directory,args.count)
    elif args.command=='compose-screen':result=screen_compose(args.manifest)
    elif args.command=='align-voice':result=align_voice(args.reference,args.generated,args.segments,args.output)
    else:result=narrate(args.text,args.output,args.voice,args.rate)
    emit(result)

if __name__=='__main__':
    try:main()
    except Exception as e:
        print(json.dumps({'error':str(e),'type':type(e).__name__},ensure_ascii=False),file=sys.stderr);sys.exit(1)
