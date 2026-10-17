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
