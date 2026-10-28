# 고니 소통 작업실 사용법

## 무엇을 할 수 있나요?

| 기능 | 지원 |
|---|---|
| 계정과 카테고리별 목록 | 지원 |
| 게시글 주소·본문 메모 저장 | 지원 |
| 같은 계정·글·동작 중복 방지 | 지원 |
| Claude Code·Codex로 댓글 초안 작성 | 스킬이 저장된 본문을 읽고 CLI로 저장 |
| 5개 글 단위로 다음 작업 준비 | 지원 |
| 직접 처리한 결과·불명확·건너뜀 기록 | 지원 |
| 기존 community.py 기록 가져오기 | 지원, 원본 DB는 읽기 전용 |
| CSV 입력·JSON 내보내기·DB 백업 | 지원 |
| 네이버 로그인·본문 자동 수집·자동 공감·댓글 등록 | 이 버전에서 지원하지 않음 |

이웃부스터에서 분석한 계정 분리·중복 방지·본문 기반 문구·작업 상태·이력 관리를 고니 코드로 독립 구현했다. 타사 실행파일·코드·아이콘은 포함하지 않았다.

## 1. 설치

Windows에서 ZIP으로 받았다면 압축을 먼저 풀고 **INSTALL.cmd**를 더블클릭한다.
설치 후 **START.cmd**를 더블클릭하면 작업실이 열린다. 이미 실행 중이면 기존 화면을 연다.
실행 창은 사용 중 열어 두고, 종료할 때 화면의 **앱 종료** 또는 실행 창의 `Ctrl+C`를 사용한다.
버전 0.1.1부터 더블클릭 설치·실행을 지원한다. Python은 별도로 필요하다.

Python 3.10 이상이 필요하다. 외부 Python 패키지는 설치하지 않는다.

```powershell
git clone https://github.com/qwer777qq/goni-skill.git
cd goni-skill
python -X utf8 skills/goni-community/scripts/install.py
```

이미 저장소가 있으면 본인의 변경 사항을 보존하며 최신 파일을 받은 뒤 설치 명령만 실행한다.

설치 결과:

- 공용 앱: `~/.goni-community/app`
- 공용 데이터: `~/.goni-community/workspace.sqlite3`
- Codex 스킬: `~/.codex/skills/goni-community`
- Claude Code 스킬: `~/.claude/skills/goni-community`
- Windows 실행 파일: `~/.goni-community/bin/goni-community.cmd`

기존 계정/작업 데이터를 삭제하지 않는다. 전역 PATH, 브라우저 보안 설정, Claude/Codex 설정 파일을 바꾸지 않는다.

## 2. 화면 열기

### 여러 링크 붙여넣기 (0.1.2)

계정을 선택하고 **링크 한 번에 추가**를 누른다. 한 줄에 개별 블로그 게시글 URL 하나씩, 최대 200개를 넣는다.
공감·댓글·서로이웃 중 새 글에 만들 작업을 선택하고 **중복 제외하고 추가**를 누른다.
추가된 글·작업 수, 중복과 잘못된 주소 수가 표시된다. 잘못된 줄은 제외하고 정상 주소를 저장한다.
모바일·PC·PostView 주소를 같은 글로 정규화한다. 같은 네이버 ID로 등록된 기존 글은 다른 별칭에 있어도 제외하며 상태·초안을 바꾸지 않는다.
블로그 홈·단축 링크·클립은 지원하지 않는다. 자동 본문 수집·외부 반응 없이 준비 목록만 만든다.

CLI: `python -X utf8 scripts/cli.py add-links --profile "계정별칭" --file links.txt --actions like,comment`

현재 이 앱은 localhost용이다. 로그인·사용자별 권한 분리가 없으므로 공개 호스팅에 그대로 노출하지 않는다.

```powershell
& "$HOME/.goni-community/bin/goni-community.cmd" serve
```

터미널에 표시되는 `http://127.0.0.1:8877`을 브라우저에서 연다. 서버를 종료하려면 화면 오른쪽 위 **앱 종료**를 누르거나 실행한 터미널에서 `Ctrl+C`.

포트가 사용 중이면:

```powershell
& "$HOME/.goni-community/bin/goni-community.cmd" serve --port 8878
```

화면에서:

1. **계정 구분 추가**: 별칭, 네이버 ID, 카테고리 입력.
2. **글 추가**: 개별 게시글 주소와 직접 읽은 본문/메모 입력.
3. **Claude·Codex 초안 요청**: 최대 5개 글의 자료가 담긴 프롬프트 복사.
4. 댓글 초안 저장 → 본문과 비교 → **검토 완료**.
5. 직접 처리한 결과를 확인했다면 근거를 입력하고 **결과 기록**.

로그인 정보는 입력하지 않는다. 완료 버튼은 외부 게시 버튼이 아니다.

## 3. Claude Code와 Codex에서 쓰기

설치 후 새 대화에서 다음 프롬프트를 사용한다. 저장된 계정 별칭을 정확하게 넣는다.

```text
$goni-community
‘스타·연예’ 프로필의 대기 글 5개를 확인해.
저장된 본문 메모에 나온 구체적인 내용 하나씩을 짚어
자연스러운 존댓말 1~2문장 댓글 초안을 작성하고 해당 작업 ID에 저장해.
본문이 부족하면 필요한 자료를 알려줘.
아직 실제 게시하지 않았으니 완료로 기록하지 마.
```

Claude Code에서도 같은 `goni-community` 스킬을 지정한다. 자동으로 인식하지 못하면:

```text
내 홈 폴더의 .claude/skills/goni-community/SKILL.md를 읽고,
같은 폴더의 scripts/cli.py로 작업해.
```

Codex에서는 `.codex/skills/goni-community/SKILL.md`를 지정하면 된다. 별도 AI API 키가 필요하지 않으며, 사용하는 에이전트의 모델이 초안을 만든다.

본문 파일을 새로 등록하는 프롬프트:

```text
$goni-community
계정 별칭: 스타·연예
게시글 URL: [실제 개별 게시글 주소]
본문 파일: [내가 저장한 UTF-8 텍스트 파일 경로]
공감·댓글 작업을 중복 확인해서 목록에 넣고 댓글 초안까지만 저장해.
```

직접 처리한 결과 기록:

```text
$goni-community
작업 ID 12는 내가 직접 처리했고 화면에서 등록한 문구를 확인했어.
확인 근거: [내가 본 내용과 확인 시각]
이 내용을 사용자 확인 기록으로 저장해.
```

## 4. CLI 명령

모든 상태 데이터는 기본적으로 같은 폴더를 사용한다. 다른 프로젝트와 분리하려면 모든 명령 앞에 `--state "C:/my-data"`를 지정한다.

```powershell
$cli = "$HOME/.goni-community/app/scripts/cli.py"
python -X utf8 $cli status
python -X utf8 $cli profile --name "스타·연예" --naver-id "my_blog_id" --category "스타·연예"
python -X utf8 $cli list --profile "스타·연예"

python -X utf8 $cli add --profile "스타·연예" `
  --url "https://blog.naver.com/example_blog/123456789" `
  --title "실제 읽은 글 제목" --excerpt-file "C:/notes/post.txt" --actions like,comment

python -X utf8 $cli batch --profile "스타·연예" --count 5
python -X utf8 $cli prompt --profile "스타·연예" --count 5
python -X utf8 $cli draft --id 12 --file "C:/notes/comment.txt"
python -X utf8 $cli review --id 12
python -X utf8 $cli record --id 12 --status done --evidence "직접 확인한 등록 문구와 시각"
python -X utf8 $cli events --id 12
```

위 주소와 ID는 형식 예시이며 실행 전에 실제 등록된 작업 ID를 확인한다. 네이버 ID는 영문/숫자/밑줄/하이픈만 허용한다.

제목이나 본문 수정:

```powershell
python -X utf8 $cli source --id 12 --title "수정 제목" --file "C:/notes/post.txt"
```

수정하면 해당 글의 진행 중인 작업 검토가 취소된다. 이미 완료·건너뜀·확인 필요 상태는 그대로 유지한다.

불명확한 결과:

```powershell
python -X utf8 $cli record --id 12 --status uncertain --evidence "등록 여부를 확인하지 못함"
```

확인 필요와 마감 작업은 다음 batch에서 제외된다. 명시적으로 다시 준비할 때만:

```powershell
python -X utf8 $cli reopen --id 12 --reason "이전 결과를 직접 확인한 뒤 다시 준비"
```

## 5. 기존 기록과 CSV

```powershell
python -X utf8 $cli import-legacy --file "$HOME/.goni-naver-community/state.sqlite3"
```

원본 DB를 수정하지 않는다. 같은 원본의 같은 작업을 재가져와도 새 작업을 만들지 않는다. 이전 완료 기록은 `legacy_record`로 구분한다. 새 프로그램은 개별 블로그 게시글만 지원하므로 홈·클립 등 지원하지 않는 주소는 건너뛴 ID와 이유를 반환한다.

UTF-8 CSV의 첫 줄은 `url,title,excerpt`다.

```powershell
python -X utf8 $cli import-csv --profile "스타·연예" --file "C:/notes/posts.csv"
```

잘못된 행이 있으면 그 가져오기 전체를 취소한다. 최대 1,000행.

## 6. 백업과 내보내기

```powershell
python -X utf8 $cli backup --output "C:/backup/goni-2026-10-20.sqlite3"
python -X utf8 $cli export --profile "스타·연예" --output "C:/backup/goni-records.json"
```

기존 파일을 덮어쓰지 않는다. JSON에는 본문·초안·개인 작업 기록이 포함되므로 공개 GitHub에 올리지 않는다.

## 7. 문제 해결

- **포트 사용 중**: 다른 `--port`로 시작.
- **스킬을 못 찾음**: 새 대화를 열거나 SKILL.md의 전체 경로 지정.
- **프로필 설정이 다름**: 계정 ID를 바꾸지 말고 새 별칭 생성. 같은 네이버 ID의 같은 글은 기존 기록으로 연결.
- **완료 기록 불가**: 본문 메모, 필요한 초안, 검토 완료, 결과 근거 순서를 확인.
- **확인 필요 작업이 목록에 없음**: 상태 필터를 확인. batch에서는 재처리를 막기 위해 제외.
- **페이지가 연결되지 않음**: 로컬 서버가 실행 중인지 확인. 이 앱은 네이버 사이트 차단을 해제하는 도구가 아님.

## 개발 검증

```powershell
python -X utf8 -m unittest discover -s skills/goni-community/scripts -p test_app.py -v
```

실제 계정 없이 주소 정규화, 중복, 상태 전환, CSV 원자성, 기존 DB 가져오기, 백업, 로컬 HTTP 접근 검사를 실행한다.
