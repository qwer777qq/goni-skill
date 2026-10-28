# 장면집 화면 절차와 기능 범위

실제 설치 버전의 메뉴와 [공개 README](https://github.com/qwer777qq/goni-shortform-highlights/blob/main/local_studio/README.md)를 먼저 대조한다. 이 안내는 2026-10-17에 확인한 버전 기준이다.

1. Windows에 Python 3.11 이상과 FFmpeg·ffprobe를 준비하고 `local_studio/start.cmd`로 켠다. 기본 주소는 `http://127.0.0.1:8767`이다. 처음 설치하는 PC에서는 공개 README의 가상환경·의존성 설치 순서를 따른다.
2. `영상 불러오기`에서 로컬 MP4·MOV·MKV·WebM 파일을 고른다. 한 파일의 허용 크기는 최대 10GB다. 공개 YouTube 주소 가져오기는 설치·접근 조건에 따라 실패할 수 있으므로 실제 성공 여부를 확인한다.
3. `자동 자막 만들기`의 `Small · 균형` 모델이나 `SRT 불러오기`를 사용한다. 자동 인식 결과의 고유명사·숫자와 시작·끝 초를 원음과 대조한다.
4. `목표 길이`와 `구간 찾기`로 후보를 보거나 `시작 (초)`·`끝 (초)`를 직접 지정한다. 추천은 키워드·발화 밀도·문장 경계의 규칙 기반 제안이다. 한 출력물에는 원본의 연속된 한 구간만 담긴다.
5. `영상 꾸미기`의 `상단 제목`에 첫 화면 훅을 최대 56자·두 줄로 입력한다. `채널명 / 하단 문구`는 최대 42자다. `댓글 카드형`을 택하면 직접 작성한 문구를 최대 80자까지 표시할 수 있다.
6. 실제 선택 가능한 템플릿은 [카탈로그](https://github.com/qwer777qq/goni-shortform-highlights/blob/main/local_studio/template_catalog.json)의 11종이다. 새 프로젝트 기본값은 `다크 · 제목 안전형(safe)`이며 기존 프로젝트의 선택은 유지된다. 68종 참고 갤러리와 다른 도구에서 관찰한 글꼴·색 메뉴는 현재 앱 기능으로 안내하지 않는다.
7. `원본 전체 맞춤`과 `가운데 채움`의 크롭을 비교한다. 속도 범위는 0.5~2배다. 자막 팝·강조 효과의 어절 타이밍은 균등 추정이므로 실제 발음과 비교한다.
8. `저장` 후 `MP4 내보내기`를 실행한다. 결과는 `local_studio/data/<프로젝트>/exports/<버전>/`의 MP4·SRT·썸네일 JPG·편집 설정으로 남는다. 최종 MP4를 재생해 첫·중간·끝, 자막, 소리와 제목 안전영역을 확인한다.

로고 업로드·자유 텍스트 상자·임의 글꼴/색/위치 조절·비연속 장면 연결·자동 게시가 필요한 작업은 지원하는 다른 편집 도구에서 완성한다. 브라우저 미리보기와 출력 MP4의 줄바꿈이 다를 수 있다.

출처: [사용자 제공 Notion 페이지](https://app.notion.com/p/3fb787051d5d815b8528e85a463fccac), [장면집 README](https://github.com/qwer777qq/goni-shortform-highlights/blob/main/local_studio/README.md), [템플릿 카탈로그](https://github.com/qwer777qq/goni-shortform-highlights/blob/main/local_studio/template_catalog.json).
