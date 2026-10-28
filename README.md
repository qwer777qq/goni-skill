# 고니 스킬

## 고니 스킬 전체 묶음 · 11종

| 스킬 | 역할 |
|---|---|
| [goni](SKILL.md) | GitHub 위치·개발 도구 점검·작업 기억 |
| [goni-project-workflow](skills/goni-project-workflow/SKILL.md) | 반복 개발 작업 흐름 |
| [goni-rea](skills/goni-rea/SKILL.md) | 기능 분석·독립 구현 설계 |
| [goni-app-analysis](skills/goni-app-analysis/SKILL.md) | 배포 앱·확장 정적 분석 |
| [goni-alphacut](skills/goni-alphacut/SKILL.md) | 영상 편집 화면·템플릿 조사 |
| [goni-community](skills/goni-community/SKILL.md) | 로컬 소통 목록·댓글 초안 관리 |
| [goni-naver-community](skills/goni-naver-community/SKILL.md) | 계정별 브라우저 업무·중복 기록 |
| [goni-shortform-highlights](skills/goni-shortform-highlights/SKILL.md) | 맥락 기반 숏폼 구성·장면집 출력 |
| [goni-cliploom-highlights](skills/goni-cliploom-highlights/SKILL.md) | 별도 Cliploom 설치·제작 세트 점검 |
| [goni-jiyoung-skill5](skills/goni-jiyoung-skill5/SKILL.md) | 파크골프 편집·검수·편집기 인수 |
| [goni-reel-studio](skills/goni-reel-studio/SKILL.md) | 다중 장면·반전·명암·MCP 릴스 출력 |

**고니 사용자 스킬 묶음**입니다. 타사 플러그인 전체나 모델·편집 앱·원본 영상·로그인 정보는 포함하지 않습니다. 스킬 설치와 실제 도구 설치/연결은 별개입니다.

```powershell
git clone https://github.com/qwer777qq/goni-skill.git
cd goni-skill
python scripts/install_skills.py --client both --dry-run
python scripts/install_skills.py --client both
# 기존 설치를 백업하고 갱신할 때만:
python scripts/install_skills.py --client both --update
```

새 Codex·Claude Code 세션에서 사용합니다. **[실행 앱·MCP 설치·상세 프롬프트](https://github.com/qwer777qq/goni-shortform-highlights/blob/main/docs/reel-studio.md)**는 장면집 저장소에서 제공합니다. Cliploom과 다른 편집 도구는 각 스킬의 설치 전제 조건을 따릅니다. 개인 PC 위치 파일과 작업 데이터는 배포에서 제외했습니다.

고니 GitHub 저장소 확인, SCV·Graphify 점검, 코드 관계 분석, 작업 기억을 위한 개인 Codex 스킬입니다.

## 설치

```powershell
git clone https://github.com/qwer777qq/goni-skill.git "$HOME/.codex/skills/goni"
```

이미 `goni` 스킬 폴더가 있으면 내용을 비교한 뒤 갱신합니다. 설치 후 새 Codex 채팅에서 `$goni`를 사용할 수 있습니다.

SCV와 Graphify는 별도 도구입니다. 공식 저장소: [SCV for Codex](https://github.com/wookiya1364/scv-codex), [Graphify](https://github.com/Graphify-Labs/graphify).

```powershell
python -X utf8 scripts/goni.py --project "C:/path/to/project" doctor
python -X utf8 scripts/goni.py --project "C:/path/to/project" repo --live
python -X utf8 scripts/goni.py --project "C:/path/to/project" resume
```

`checkpoint`는 프로젝트의 `memory/workflow-state.json`과 `memory/workflow-log.jsonl`에 검증한 결과를 기록합니다. `graph`는 선택한 코드 범위만 로컬에서 분석합니다.

## AlphaCut 조사 스킬

`skills/goni-alphacut/`에는 템플릿·자막·편집 기능을 화면 증거로 조사하는 고니 스킬이 있습니다. 저장소를 받은 뒤 해당 폴더를 `$HOME/.codex/skills/goni-alphacut`에 복사하면 새 Codex 채팅에서 `$goni-alphacut`을 사용할 수 있습니다. 로그인 화면 HTML과 테스트 미디어는 이 공개 저장소에 포함하지 않습니다.

## 배포 앱 기술 분석 스킬

[goni-app-analysis](skills/goni-app-analysis/SKILL.md)는 사용자가 제공한 Windows 앱·Chrome 확장 ZIP을 실행 없이 분석합니다. 이웃부스터의 모듈·데이터·통신·화면 분석과 반복 실행 스크립트가 포함됩니다.

저장소 폴더에서 설치:

```powershell
Copy-Item -LiteralPath "skills/goni-app-analysis" -Destination "$HOME/.codex/skills/goni-app-analysis" -Recurse
```

기존 설치 폴더가 있으면 파일을 비교해 갱신합니다. Claude Code에서는 같은 폴더를 `$HOME/.claude/skills/goni-app-analysis`에 둡니다.

새 채팅에서 `$goni-app-analysis 이 배포 ZIP의 기술 구조를 분석해줘`로 사용합니다.

- [이웃부스터 기술 분석](skills/goni-app-analysis/references/neighbor-booster-architecture.md)
- [전체 모듈·데이터 색인](skills/goni-app-analysis/references/neighbor-booster-index.json)
- [분석 명령·산출물·복사 프롬프트](skills/goni-app-analysis/references/workflow.md)

타사 앱의 실행파일과 추출 원본은 이 공개 저장소에 포함하지 않습니다.

## 고니 소통 작업실 프로그램

[goni-community](skills/goni-community/SKILL.md)는 실행 가능한 로컬 UI와 CLI입니다. 계정별 글 목록, 본문 메모, Claude Code·Codex 댓글 초안, 중복 방지, 검토와 직접 처리한 결과를 관리합니다. 네이버 로그인·본문 자동 수집·자동 공감·댓글 등록은 포함하지 않습니다.

```powershell
python -X utf8 skills/goni-community/scripts/install.py
& "$HOME/.goni-community/bin/goni-community.cmd" serve
```

브라우저에서 `http://127.0.0.1:8877`을 엽니다. Codex와 Claude Code용 스킬을 함께 설치하고 같은 로컬 DB를 사용합니다.

[초보자 사용법·복사 프롬프트·전체 CLI 명령](skills/goni-community/references/quickstart.md)
