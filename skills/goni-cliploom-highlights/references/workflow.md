# 제작·보존·출력 계약

근거: 앱 `README.md`, `docs/API.md`, `docs/EDITOR-IMPROVEMENTS-20261021.md`, `public/editor-core.js`, `src/media.mjs`. 소스 버전이 바뀌면 관련 계약을 재확인한다.

## UI 제작 흐름

1. 대상 계정의 작업실에서 공개 YouTube URL과 스타일을 입력해 **쇼츠 만들기**. 다운로드 → 전사 → 후보 → 최대 3개 자동 MP4가 기본 흐름이다. 추가 후보는 별도 선택한다. 파일 입력은 **영상 파일 올리기**에서 MP4/MOV/WebM/MKV를 사용한다.
2. 제작 탭에 시청자·목적·목표 길이·편수·포함/제외 원본 구간·용어 사전을 설정한다. 제약을 만족할 후보가 없으면 조건을 수정하며 자막/후보를 꾸며내지 않는다.
3. 제목·첫 3초 후킹 선정 이유에서 원문 위치·조건·예외와 안전한 발화 경계를 확인한다. 3초 안에 안전한 도입이 불가능하면 원래 순서를 유지하는 것이 정상이다. 후킹 발언은 본문에서 중복되지 않아야 한다. 최초 생성 근거는 수동 편집 후 현재 타임라인과 다를 수 있다.
4. 자막은 문구·구간·배치·글꼴을 편집한다. 낮은 Whisper 점수는 정답률이 아니다. 선택 구간 재인식은 교정문과 비교한 proposal이며 사용자가 선택한 것만 초안에 적용한다.
5. **영상에 적용**은 저장 후 새 렌더다. 원본에 구운 자막은 captionsEnabled로 지워지지 않는다. 하단 자르기 등 실제 화면과 얼굴을 확인해 처리한다.
6. 이력에서 기존 버전/MP4가 남는지 확인하고 선택한 완성본을 내려받는다. MP4 외에 출력/원본 기준 SRT, JPG, 편집 JSON, 타임코드·검수 정보를 담은 ZIP을 받을 수 있다.

기본 한도(설정에 따라 달라짐): 파일 512MiB, 영상 2시간, 계정 원본 2GiB/50프로젝트. 기본 세로 출력 720×1280 H.264/AAC. 확장 편집은 최대 24구간, 0.5~2배속, 720p/1080p, 배속 반영 최대 180초. 무음 후보는 선택분만 삭제하며 경계 양쪽 0.12초 여유를 둔다.

## 보존 규칙

- 자막·words의 start/end는 **원본 절대 시간**이다. 결과 영상 길이와 타임코드는 segments·speed로 변환된다.
- `baseRevision`을 최신 값으로 전송한다. `409 EDIT_CONFLICT`는 최신 서버 편집과 초안을 비교해야 한다. baseRevision 생략으로 충돌 보호를 우회하지 않는다.
- 렌더 중 편집/중복 렌더의 409는 완료·실패 상태를 확인한 뒤 처리한다.
- 재분석은 기존 클립을 유지하면서 새 후보를 추가한다. 복원은 새 저장 버전이며 과거 MP4를 덮지 않는다.
- captionsEnabled만 바꾸면 자막 원문·내용 버전은 유지한다. 제목·문구·구간·스타일·글꼴이 바뀌면 양쪽 출력이 무효화되므로 다시 렌더한다.
- UI 초안은 계정·클립별 localStorage이다. 브라우저 초안 저장과 서버 저장을 구분한다.
- 네트워크 실패 시 동일 프로젝트/작업과 같은 requestId를 사용해 재시도한다. 실패를 이유로 기존 프로젝트나 data/를 삭제하지 않는다.

## API가 적합할 때

세션·소유권·Origin 검사를 보존하고 실제 계약을 읽는다. 새 토큰을 만들거나 브라우저 쿠키를 추출하는 방식 대신 지원되는 인증 세션/도구를 사용한다. 브라우저 조작 도구가 허용하지 않는 네트워크 접근으로 우회하지 않는다.

| 작업 | 경로 / 핵심 계약 |
|---|---|
| 대상 확인 | `GET /api/config`, `/api/me`, `/api/health`, `/api/readiness` |
| 프로젝트 | `GET /api/projects`, `GET /api/projects/:id` |
| YouTube 자동 제작 | `POST /api/projects/youtube {url,style,requestId}`; 동일 제출 재시도는 같은 requestId (8~100자 영숫자/하이픈/밑줄) |
| 파일 분석 | `POST /api/projects {name}` → `POST /api/projects/:id/upload` raw body, application/octet-stream, X-Filename=encodeURIComponent(name) → `/analyze {}` |
| 외부 자막 분석 | `/analyze {transcript:[{start,end,text}]}`는 실제 제공된 자막에만 사용 |
| 편집 저장 | `PATCH /api/clips/:id`에 최신 baseRevision과 변경 필드만 전달 |
| 렌더 | `POST /api/clips/:id/render {}` → 프로젝트/렌더 상태 확인 |
| 두 버전 | `GET /api/clips/:id/file?variant=withCaptions` 또는 `withoutCaptions`; 다운로드는 `&download=1` |
| 이력/고정 완성본 | `GET /api/clips/:id/history`, `/file?output=:outputId`, `/bundle?output=:outputId` |
| 재인식 | `POST /api/clips/:id/retranscribe {start,end}` 원본 기준 180초 이하, 기존 교정문 자동 변경 없음 |
| 작업 상태/재개 | `GET /api/projects/:id/jobs`, `POST /api/projects/:id/resume {jobId}` |

style: dark/white/minimal/paper/comments/pop/highlight. ratio: 9:16/16:9/5:4/1:1/4:5. captionFont는 카탈로그 ID만 사용한다. 알 수 없는 폰트 경로/URL을 전송하지 않는다.

상태는 empty/uploaded/queued/downloading/transcribing/analyzing/rendering/ready/failed. 폴링은 약 2초를 기준으로 하되 장기 작업은 간격을 늘리고 사용자에게 의미 있는 진행을 알린다. 실패 원인과 실제 파일 유무를 확인한다. 검수 API의 checked는 실제 사람이 검수한 상태를 뜻하므로 자동 검사만으로 사람 검수 완료를 만들어내지 않는다.
