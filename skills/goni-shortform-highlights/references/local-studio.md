# 로컬 장면집 연결

사용자가 받은 goni-shortform-highlights 저장소의 local_studio 폴더를 사용한다. 실제 설치 경로를 먼저 확인한다. 해당 README.md와 검증 기록을 먼저 읽는다. `python server.py` 또는 start.cmd로 실행하며 기본 주소 http://127.0.0.1:8767 은 이 PC 전용이다.

```powershell
python scripts/studio_client.py --root "C:/project/local_studio" prepare --video "C:/video/lecture.mp4" --srt "C:/video/lecture.srt"
python scripts/studio_client.py --root "C:/project/local_studio" prepare --url "https://www.youtube.com/watch?v=VIDEO_ID" --model small
python scripts/studio_client.py --root "C:/project/local_studio" export --plan "C:/project/selection.json"
```

prepare는 새 프로젝트와 SRT 또는 로컬 Whisper 자막을 만든다. 반환된 transcript.json을 에이전트가 읽고 구간을 선정한다. URL 다운로드가 거부되면 파일 입력으로 전환한다.

선정 파일:
```json
{"project_id":"prepare가 반환한 ID","brief":"초보자 기능 소개","clips":[{"start":12.4,"end":53.2,"speed":1.2,"title":"실제 시연에서 확인한 기능","footer":"채널명","theme":"dark","layout":"fit","captions":true,"reason":"문제와 해결 시연이 한 구간에서 완결됨"}]}
```

export는 전체 구간 검증 후 차례로 저장/출력한다. 이전 렌더를 유지하고 마지막 구간을 편집 상태로 남긴다. 중간 실패 시 완료된 결과를 export-result.json에 기록하고 오류로 종료한다. 사용자가 편집 중인 프로젝트 대신 새 prepare 프로젝트를 사용한다. 결과 썸네일은 초안/검수용으로 별도 브랜드 썸네일 제작을 대체하지 않는다.

제목이 긴 쇼츠는 `theme: "safe"`(다크 · 제목 안전형)을 우선한다. 현재 로컬 스튜디오는 단어 단위 줄바꿈·크기 자동 조절로 제목을 2줄 및 상단 안전영역 안에 배치한다. 다른 테마도 같은 안전 배치를 적용한다. 출력 MP4 첫·중간 프레임에서 제목이 영상 경계와 겹치지 않는지 확인한다. EasyCut 화면 비교 근거는 프로젝트 `workspace/rea-easycut/title-template-evidence.md`에 있고, 타사 자산은 로컬 앱에 포함하지 않는다.

쓰기 API는 JSON + X-Studio-Request: 1. import/youtube/transcribe/render는 jobs/{id}의 done을 확인해야 한다. 자막은 원본 시간 기준이며 구간 교집합 후 (time-start)/speed로 출력 시각을 계산한다. 결과는 data/프로젝트/exports/버전 아래 MP4/SRT/JPG/설정으로 남는다.
