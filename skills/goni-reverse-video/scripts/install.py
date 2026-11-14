"""Install the complete local skill in Codex and/or Claude without changing settings."""
from pathlib import Path
import argparse,shutil,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def files():
    return [f for f in ROOT.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc']
def main():
    p=argparse.ArgumentParser();p.add_argument('--target',choices=['codex','claude','both'],default='both');a=p.parse_args()
    targets=['codex','claude'] if a.target=='both' else [a.target];destinations=[]
    for target in targets:
        dest=Path.home()/('.'+target)/'skills'/ROOT.name
        if dest.resolve()==ROOT:continue
        for f in files():
            other=dest/f.relative_to(ROOT)
            if other.exists() and hashlib.sha256(other.read_bytes()).digest()!=hashlib.sha256(f.read_bytes()).digest():
                raise SystemExit('Existing installation differs: back it up before updating '+str(dest))
        destinations.append(dest)
    for dest in destinations:
        for f in files():
            other=dest/f.relative_to(ROOT);other.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,other)
    print(json.dumps({'installed':[str(d) for d in destinations],'settings_changed':False},ensure_ascii=False))
if __name__=='__main__':main()
