# 고니 스킬

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
