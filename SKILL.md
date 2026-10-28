---
name: goni
description: 고니 GitHub 저장소를 확인하고 SCV·Graphify 개발 작업을 이어갈 때 사용한다. 저장소 위치 확인, 도구 점검, 코드 관계 질의, 작업 기억 기록을 돕는다.
---

# 고니 개발 작업

이 스킬의 절차와 스크립트는 고니 작업용으로 작성했다. SCV와 Graphify는 각각 원저작자의 별도 도구이며 이 스킬에 포함하지 않는다.

## 시작

1. 현재 프로젝트의 `AGENTS.md`와 `memory/development-workflow.md`가 있으면 읽는다. 프로젝트 기억이 없으면 `C:/Users/USER/.codex/memory/development-workflow.md`를 전역 설치 상태의 참고로 읽되 프로젝트 상태로 오인하지 않는다. 최신 사용자 지시가 기록된 기본값보다 우선한다.
2. GitHub 계정 기준점은 [qwer777qq](https://github.com/qwer777qq)다. 현재 프로젝트의 실제 저장소는 `git remote get-url origin`으로 확인하고, 없으면 원격을 추측하지 않는다. `gh repo view`로 대상 저장소와 공개 범위를 다시 확인한다.
3. 이 스킬 폴더에서 `python -X utf8 scripts/goni.py --project <프로젝트 경로> doctor`로 SCV 플러그인, Graphify CLI·패키지, GitHub CLI와 프로젝트 준비 상태를 확인한다. 설치 상태와 프로젝트 초기화 상태를 구분한다.

## 반복 작업

- `repo`: 현재 Git 원격과 고니 GitHub 저장소의 연결 상태를 확인한다. `--live`는 GitHub에 읽기 전용 조회를 한다.
- `resume`: 프로젝트의 개발 작업 기록과 최근 상태를 불러온다.
- `checkpoint --summary "검증한 결과" --next "다음 작업"`: 확인한 사실과 남은 일을 프로젝트 `memory/`에 기록한다. 비밀 값은 기록하지 않는다.
- `graph --scope scripts`: 프로젝트 `scripts/` 코드만 로컬 구조 분석한다. 결과는 `.workspace-tools/graphs/scripts/`에 둔다.
- `query "질문" --scope scripts`: 생성된 그래프를 질의한다. 코드가 바뀌면 그래프를 다시 만든다. 실제 동작은 별도로 실행 검증한다.

SCV 계획·구현·회귀 검사는 설치된 공식 `scv:*` 스킬을 따른다. Graphify의 분석 범위는 요청한 코드 폴더로 제한한다. 개인 미디어·문서나 자격 증명을 설치의 부수 작업으로 인덱싱하지 않는다. GitHub 게시 전에는 올릴 파일과 공개 범위를 확인하고, 작업 요청에서 허용된 저장소에만 반영한다.

작업을 마치면 실제 변경 파일, 실행한 명령, 검증 결과, 공개 URL과 남은 항목을 구분해 남긴다.
