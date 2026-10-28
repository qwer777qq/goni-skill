"""Install the Goni skill set into Codex or Claude Code, preserving existing copies."""
import argparse
from datetime import datetime
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--client',choices=['codex','claude','both'],default='both')
    parser.add_argument('--name',action='append',help='Skill name; omit to install all Goni skills')
    parser.add_argument('--update',action='store_true',help='Back up an existing skill, then overlay maintained files')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    sources={'goni':ROOT}
    sources.update({p.name:p for p in (ROOT/'skills').iterdir() if (p/'SKILL.md').is_file()})
    names=args.name or sorted(sources)
    if set(names)-sources.keys(): parser.error('Unknown skill: '+', '.join(set(names)-sources.keys()))
    clients=['codex','claude'] if args.client=='both' else [args.client]
    for client in clients:
        base=Path.home()/('.'+client)/'skills'
        for name in names:
            src=sources[name]; dest=base/name
            if dest.exists() and not args.update:
                print(f'SKIP {client}/{name}: exists (use --update to back up and overlay)'); continue
            print(f'{"PLAN" if args.dry_run else "INSTALL"} {client}/{name}')
            if args.dry_run: continue
            if dest.exists():
                backup=Path.home()/'.goni-skill-backups'/datetime.now().strftime('%Y%m%d-%H%M%S-%f')/client/name
                shutil.copytree(dest,backup)
            if name=='goni':
                dest.mkdir(parents=True,exist_ok=True)
                shutil.copy2(src/'SKILL.md',dest/'SKILL.md')
                for folder in ('scripts','agents'):
                    shutil.copytree(src/folder,dest/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            else:
                shutil.copytree(src,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))


if __name__=='__main__': main()
