---
name: goni-project-workflow
description: 고니 프로젝트에서 SCV·Graphify 설치 상태를 점검하고 반복 개발 명령·담당 에이전트·작업 기억을 연결한다. 도구 셋업, 반복 절차 정리, 이전 개발 이어가기 요청에 사용한다.
---

# 고니 프로젝트 작업 이어가기

현재 프로젝트의 `AGENTS.md`와 `memory/development-workflow.md`를 읽고 최신 사용자 지시를 우선한다. 프로젝트 기억 파일이 없으면 `C:/Users/USER/.codex/memory/development-workflow.md`를 전역 설치 참고로 읽는다. 이 스킬은 도구 셋업과 개발 기록을 담당한다. 영상 구성·렌더링은 기존 `goni-shortform-highlights` 및 프로젝트 제작 스킬을 사용한다.

## 실행 환경

`scripts/project_workflow.py`가 있으면 아래 명령을 사용한다. 없으면 현재 프로젝트의 기존 도구를 확인하고, 이 프로젝트 전용 경로나 미디어 설정을 다른 저장소에 무조건 복사하지 않는다.

```powershell
python -X utf8 scripts/project_workflow.py doctor
python -X utf8 scripts/project_workflow.py resume
python -X utf8 scripts/project_workflow.py scv-status
python -X utf8 scripts/project_workflow.py graph --scope local_studio
python -X utf8 scripts/project_workflow.py query "render_video" --scope local_studio
python -X utf8 scripts/project_workflow.py checkpoint --summary "검증한 결과" --next "남은 작업"
```

SCV는 설치된 공식 `scv:*` 스킬을 읽고 사용한다. 플러그인 캐시의 버전 경로를 하드코딩하지 않는다. `doctor`는 설치/설정 확인이며 전체 기능 시험이 아니다. 설치된 항목을 재설치한 것처럼 보고하지 않는다.

Graphify 원본은 Graphify-Labs/graphify, Python 패키지는 `graphifyy`다. 위 래퍼는 `local_studio`와 `scripts`만 허용하고 코드 전용 로컬 추출을 실행한다. 코드 관계를 물으면 그래프를 먼저 질의하고, 실제 동작은 별도 테스트한다. 미디어·개인 폴더 전체 분석이나 외부 모델 호출을 설치의 부수 작업으로 확대하지 않는다.

## 역할과 기억

- `goni_workflow_maintainer`는 도구·스크립트·SCV 상태·기억 정리용 등록 역할이다. 주 에이전트가 기본 수행하며 사용자가 위임을 요청할 때 한정된 소유 범위를 정해 호출한다.
- 제목·썸네일·영상 검수는 기존 역할을 재사용한다. 동시에 작업하면 다른 변경을 되돌리지 말고 소유 파일을 구분한다.
- 기록은 실제 확인 결과, 최종 파일/공개 URL, 미완료 항목과 다음 작업을 구분한다. `checkpoint`는 최근 상태와 누적 JSONL에 기록하고 게시를 수행하지 않는다.
- 비밀번호·키·토큰·학생 실명은 기록하지 않는다. 기존 게시 승인을 새 영상이나 새로운 외부 공유에 확대하지 않는다.
- 새 명령을 추가하면 성공 경로와 영향이 큰 실패 경로를 실제 실행한다. 스킬은 quick_validate.py로, 에이전트 TOML은 tomllib로 확인한다. 새 역할의 런타임 호출을 확인하지 않았다면 등록·구문 검증까지만 보고한다.
