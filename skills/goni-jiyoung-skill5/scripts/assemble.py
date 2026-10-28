"""Frame-exact FCPXML assembly and optional user-owned title seed reuse. Python 3.10+."""
from pathlib import Path
from fractions import Fraction
from urllib.parse import urlparse, unquote
import argparse, copy, json, re, xml.etree.ElementTree as ET

def require(ok, message):
    if not ok: raise ValueError(message)

def integer(v):
    return isinstance(v,int) and not isinstance(v,bool)

def seconds(value):
    return Fraction(value.removesuffix('s'))

def stime(frames, fps):
    value=Fraction(frames)/fps
    return f'{value.numerator}/{value.denominator}s'

def validate(plan, check_file=True):
    fps=Fraction(plan['fps']);require(fps>0 and fps<=240,'Invalid fps')
    for k in ('width','height','source_frames'):
        require(integer(plan[k]) and plan[k]>0,f'Invalid {k}')
    uri=urlparse(plan['source_uri']);require(uri.scheme=='file','source_uri must be a local file URI')
    if check_file:
        p=unquote(uri.path)
        if re.match(r'^/[A-Za-z]:/',p):p=p[1:]
        if uri.netloc and uri.netloc!='localhost':p='//'+uri.netloc+p
        require(Path(p).is_file(),'Source media does not exist')
    require(plan.get('cuts'),'No explicit cuts')
    cursor=0; mapped=[]
    for c in plan['cuts']:
        a,b=c['in'],c['out'];require(integer(a) and integer(b) and 0<=a<b<=plan['source_frames'],'Invalid source cut')
        mapped.append({'source_in':a,'source_out':b,'timeline_in':cursor,'timeline_out':cursor+b-a});cursor+=b-a
    cues=[]
    for c in plan.get('captions',[]):
        a,b=c['in'],c['out'];require(integer(a) and integer(b) and 0<=a<b<=plan['source_frames'],'Invalid caption range')
        require(isinstance(c.get('text'),str) and c['text'].strip(),'Empty caption')
        require('-->' not in c['text'] and not re.search(r'\n\s*\n',c['text']),'Invalid SRT text')
        for cut in mapped:
            x,y=max(a,cut['source_in']),min(b,cut['source_out'])
            if x<y:
                cues.append(dict(c,source_in=x,source_out=y,start=cut['timeline_in']+x-cut['source_in'],end=cut['timeline_in']+y-cut['source_in'],cut_index=mapped.index(cut)))
    cues.sort(key=lambda c:(c['start'],c['end']))
    for a,b in zip(cues,cues[1:]):require(a['end']<=b['start'],'Overlapping captions; use separate graphics workflow for score overlays')
    return fps,mapped,cues,cursor

def seed_data(path,plan,fps):
    root=ET.parse(path).getroot();require(root.tag=='fcpxml','Seed must be FCPXML')
    resources=root.find('resources');require(resources is not None,'Seed has no resources')
    seq=root.find('.//sequence');require(seq is not None,'Seed has no sequence')
    fmt=next((x for x in resources.findall('format') if x.get('id')==seq.get('format')),None)
    require(fmt is not None and seconds(fmt.get('frameDuration'))==1/fps,'Seed fps mismatch')
    require(fmt.get('width')==str(plan['width']) and fmt.get('height')==str(plan['height']),'Seed dimensions mismatch')
    titles={}
    for t in root.findall('.//title'):
        name=t.get('name')
        require(name not in titles,f'Duplicate seed title name: {name}');titles[name]=t
    return root,resources,titles

def clone_title(seed,cue,fps,offset,index):
    t=copy.deepcopy(seed);duration=Fraction(cue['end']-cue['start'])/fps
    require(t.find('.//timeMap') is None,'Retime title requires editor review')
    if t.find('.//keyframeAnimation') is not None:
        require(seconds(t.get('duration'))==duration,'Animated title duration must match seed exactly')
    replacements=cue.get('replacements',{'{{TEXT}}':cue['text']})
    require(isinstance(replacements,dict) and replacements,'Missing token replacements')
    nodes=t.findall('./text/text-style')
    # Explicit tokens must each occur exactly once; never flatten multiple styles.
    for token,value in replacements.items():
        require(re.fullmatch(r'\{\{[A-Z_0-9]+\}\}',token) and isinstance(value,str),'Invalid replacement token/value')
        require(sum((n.text or '').count(token) for n in nodes)==1,f'Token {token} must appear exactly once in one text-style run')
        for n in nodes:n.text=(n.text or '').replace(token,value)
    require(not any(re.search(r'\{\{[^}]+\}\}',n.text or '') for n in nodes),'Unfilled title token')
    for d in t.findall('text-style-def'):
        old=d.get('id');new=f'jy-style-{index}-{old}';d.set('id',new)
        for n in nodes:
            if n.get('ref')==old:n.set('ref',new)
    # A title connected to an asset-clip is placed in the parent source-time coordinate system.
    t.set('offset',stime(offset,fps));t.set('duration',stime(cue['end']-cue['start'],fps));t.set('lane','1')
    return t

def timestamp(frames,fps):
    ms=round(Fraction(frames,1)/fps*1000);sec,ms=divmod(ms,1000);minute,sec=divmod(sec,60);hour,minute=divmod(minute,60)
    return f'{hour:02}:{minute:02}:{sec:02},{ms:03}'

def build(plan,out,seed=None,check_file=True):
    fps,cuts,cues,total=validate(plan,check_file)
    require(not out.exists(),'Output directory already exists')
    root=ET.Element('fcpxml',version='1.10');resources=ET.SubElement(root,'resources');titles={}
    if seed:
        sr,res,titles=seed_data(seed,plan,fps);root.set('version',sr.get('version'));resources.extend(copy.deepcopy(list(res)))
    ids={n.get('id') for n in resources};i=1
    def rid():
        nonlocal i
        while f'jy{i}' in ids:i+=1
        v=f'jy{i}';ids.add(v);i+=1;return v
    fmtid,assetid=rid(),rid()
    ET.SubElement(resources,'format',id=fmtid,frameDuration=stime(1,fps),width=str(plan['width']),height=str(plan['height']))
    asset=ET.SubElement(resources,'asset',id=assetid,name=plan.get('source_name','Source'),start='0s',duration=stime(plan['source_frames'],fps),hasVideo='1',format=fmtid,hasAudio='1',audioSources='1',audioChannels='2')
    ET.SubElement(asset,'media-rep',kind='original-media',src=plan['source_uri'])
    event=ET.SubElement(ET.SubElement(root,'library'),'event',name=plan.get('name','Jiyoung edit'))
    project=ET.SubElement(event,'project',name=plan.get('name','Jiyoung edit'))
    sequence=ET.SubElement(project,'sequence',format=fmtid,duration=stime(total,fps),tcStart='0s',tcFormat='NDF',audioLayout='stereo',audioRate='48k')
    spine=ET.SubElement(sequence,'spine');clips=[]
    for c in cuts:
        clips.append(ET.SubElement(spine,'asset-clip',ref=assetid,name=plan.get('source_name','Source'),offset=stime(c['timeline_in'],fps),start=stime(c['source_in'],fps),duration=stime(c['source_out']-c['source_in'],fps),audioRole='dialogue'))
    srt=[]
    for i,c in enumerate(cues,1):
        srt.append(f"{i}\n{timestamp(c['start'],fps)} --> {timestamp(c['end'],fps)}\n{c['text']}\n")
        if seed:
            require(c.get('template') in titles,f"Missing seed title: {c.get('template')}")
            clips[c['cut_index']].append(clone_title(titles[c['template']],c,fps,c['source_in'],i))
    report={'fps':str(fps),'duration_frames':total,'cuts':len(cuts),'caption_segments':len(cues),'styled_titles':len(cues) if seed else 0,'style_status':'seed_copied_pending_app_review' if seed else 'missing_seed_srt_only','final_cut_import_verified':False,'render_verified':False,'limitations':['single source; normal speed; no transitions; stereo audio declared; source properties must be verified externally','FCPXML structure is not proof of Final Cut compatibility']}
    # All validation before filesystem mutation.
    ET.indent(root);xml=ET.tostring(root,encoding='utf-8',xml_declaration=True);ET.fromstring(xml)
    out.mkdir(parents=True)
    (out/'edit.fcpxml').write_bytes(xml)
    (out/'captions.srt').write_text('\n'.join(srt),encoding='utf-8')
    for filename,data in [('edit-map.json',{'cuts':cuts,'captions':cues}),('validation.json',report)]:
        (out/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path);p.add_argument('--seed',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    try:print(json.dumps(build(json.loads(a.plan.read_text(encoding='utf-8-sig')),a.out,a.seed),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError,ET.ParseError) as e:p.exit(1,str(e)+'\n')
