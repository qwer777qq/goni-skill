# 분석 실행과 산출물

## 환경

- Python 표준 라이브러리만 사용한다.
- 이웃부스터 v1.0.1 배포본은 Python 3.13 바이트코드다. 검증 환경은 Python 3.13.4.
- 다른 minor 버전은 PYZ magic 검사에서 중단한다. 대상 앱을 import하거나 실행하여 버전 문제를 해결하지 않는다.
- 128MiB 입력/개별 압축 항목, ZIP 최대 10,000개 항목·총 512MiB, zlib 출력 상한이 있다. 범용 악성 파일 샌드박스는 아니다.

```powershell
python -X utf8 scripts/inspect_bundle.py "C:/research/program.zip" --output "C:/research/analysis-v1"
python -X utf8 -m unittest discover -s scripts -p "test_inspect_bundle.py"
```

출력 폴더는 새 경로여야 한다. 원본 ZIP 내부 이름은 인벤토리 라벨로만 쓰고 파일 경로로 추출하지 않는다.

## 결과 파일

| 파일 | 의미 |
|---|---|
| `summary.json` | 입력 SHA-256, 수량, 오류, 범위 한계 |
| `archive.json` | ZIP의 모든 일반 파일 이름·크기·해시 |
| `carchive.json` | EXE의 PyInstaller 내장 리소스 인벤토리 |
| `pyz-inventory.json` | PYZ에 담긴 앱·의존 모듈 전체 목록 |
| `modules.json` | 앱 코드 객체·심볼·import·SQL 통계 |
| `desktop/*.code.json` | 함수/클래스/모듈 코드 객체, 인자 이름, 참조 이름, 시작 줄 |
| `desktop/*.dis.txt` | 재귀 바이트코드 디스어셈블리 |
| `desktop/*.constants.json` | 코드 객체별 문자열 및 튜플 안 문자열 |
| `desktop/*.sql.json` | SQL로 추정되는 문자열; 실행하지 않음 |
| `web-inventory.json` | HTML·CSS·JS·JSON 해시와 정규식 기반 함수/메시지/경로 발견 목록 |
| `extension-manifest.json` | 배포 확장 선언 |

`complete_for_selected_modules=true`는 선택한 `src.*` 및 앱 진입점의 분석에 오류가 없었다는 뜻이다. 프로그램 전체의 원본 복구·실행 검증이나 서버 분석 완료를 뜻하지 않는다.

`marshal.loads`와 `dis`는 코드 객체를 읽고 표시한다. `exec`, `eval`, 대상 import는 사용하지 않는다. JWT·일부 키·URL query는 치환하지만 완전한 비밀정보 탐지는 아니므로 상세 결과를 공개 전 검토한다.

## 확장 정적 의미 분석

REA 6.5.0을 사용할 수 있으면 압축에서 이미 확보한 확장 폴더를 분석한다.

```powershell
python -X utf8 "<goni-rea>/scripts/rea_cli.py" analyze-javascript-application `
  "C:/research/extracted/extension" `
  --max-semantic-nodes 100000 --max-semantic-nodes-per-file 20000 --format json
```

stdout은 로컬 JSON, stderr는 별도 로그에 저장한다. 실제 화면이나 서버에 연결하지 않는다.

읽을 필드:

- `evidence_id`, `subject.digest`, `provider`, `parameters`
- `normalized_result.statistics`
- `normalized_result.semantic_graph.coverage`의 status/truncated/omitted 수량
- `limitations`와 unresolved 항목 수

노드가 모두 보존돼도 동적 호출이 unresolved일 수 있다. `unknown`을 성공이나 부재로 바꾸지 않는다.

## 재사용 프롬프트

```text
$goni-app-analysis
이 ZIP을 실행 없이 분석해줘.
기존 조사 자료가 있으면 SHA-256을 비교하고 재사용해.
전체 파일 인벤토리, 앱 모듈·코드 객체·데이터 구조,
확장 HTML/CSS/JS 구조와 메시지 흐름, 서버에 의존하는 기능을 정리해.
결과마다 파일/함수 근거와 미확인 사항을 적어.
내 GitHub에는 직접 작성한 분석 도구와 검토한 기술 문서만 올려.
추출된 원본과 상세 디스어셈블리는 로컬 조사 폴더에 보존해.
```
