# Codex·Claude 공용 설치·실행

필수: Python 3.11 이상, FFmpeg·ffprobe. OFL 폰트 13개가 포함돼 있다. 편집·합성에는 GPU·API 키가 필요 없다. 기본 TTS는 Windows SAPI 음성이 설치돼 있어야 한다. 영상 생성 서비스는 호출하지 않는다.

## 폰트·텍스트 효과 선택

`studio.py fonts`로 실제 폰트 가족명과 파일 출처, `studio.py presets`로 8개 프리셋을 확인한다. 타임라인의 `fonts_dir`를 생략하면 포함된 폰트를 사용한다. 외부 폰트 폴더를 지정하면 그 폴더의 TTF·OTF를 사용한다.

| preset | 폰트 | 효과 |
|---|---|---|
| original | Paperlogy 7 Bold | 원본 팝 |
| clean | Pretendard Bold | 페이드 |
| headline | Paperlogy 9 Black | 줌 |
| question | Do Hyeon | 바운스 |
| step | Paperlogy 6 SemiBold | 위로 슬라이드 |
| detail | Pretendard Regular | 타자기 |
| compare | Pretendard Black | 옆으로 슬라이드 |
| note | Paperlogy 4 Regular | 정지 |

자막 예시: `{"start":0,"end":5.6,"text":"선택 옵션을 확인하세요","preset":"step","x":540,"y":1728,"size":54,"color":"#FFFFFF"}`. start/end는 배속 적용 전 조립 타임라인 기준이다. font·animation·bold·color·highlight_color를 자막마다 덮어쓸 수 있다. 글자가 얼굴·제품·설명과 겹치지 않는지 실제 출력에서 확인한다. 타자기 효과는 1~120자, 글자당 최소 0.01초가 필요하다.

## 설치

```powershell
git clone https://github.com/qwer777qq/goni-skill.git goni-skill
python goni-skill/skills/goni-reverse-video/scripts/install.py --target both
python -m venv "$env:USERPROFILE/.goni-video-env"
$py = "$env:USERPROFILE/.goni-video-env/Scripts/python.exe"
$cli = "$env:USERPROFILE/.codex/skills/goni-reverse-video/scripts/studio.py"
& $py -m pip install -r "$env:USERPROFILE/.codex/skills/goni-reverse-video/scripts/requirements.txt"
& $py $cli doctor
```

이미 저장소를 받았다면 새 폴더로 중복 clone하지 말고 해당 checkout에서 최신 커밋을 확인한다. 설치기는 Codex `~/.codex/skills/goni-reverse-video`와 Claude Code `~/.claude/skills/goni-reverse-video`로 복사한다. 기존 설치가 다르면 덮어쓰지 않고 중단한다. FFmpeg는 별도 설치 도구이며 PATH에서 호출 가능해야 한다. `doctor` 성공은 모든 입력의 품질 보장이 아니다.

## 제품 사진으로 설명영상

먼저 장면별 설명을 UTF-8 TXT로 저장해 로컬 WAV를 만든다. 녹음한 WAV를 대신 사용해도 된다.

```powershell
& $py $cli narrate scene1.txt scene1.wav
```

`cards.json` 예시:

```json
{
  "image": "product.jpg",
  "font_file": "fonts/Paperlogy-7Bold.ttf",
  "output_dir": "cards-v1",
  "final_output": "review.mp4",
  "product_name": "제품명",
  "model": "정확한 모델 · 확인한 선택 옵션",
  "speed": 1.4,
  "minimum_duration": 0,
  "scenes": [
    {"title": "사진보다\n선택 옵션", "lines": ["메모리 · 저장공간", "운영체제 확인"], "voice": "scene1.wav", "steps": ["RAM", "SSD", "OS"]}
  ]
}
```

```powershell
& $py "$env:USERPROFILE/.codex/skills/goni-reverse-video/scripts/cards.py" cards.json
& $py $cli render cards-v1/timeline.json
```

사진은 사진으로 표시하고 설명 읽기 진행과 단계 표지만 움직인다. 새로운 사람·제품 동작을 생성하지 않는다. 최대 3줄의 짧은 정보와 최대 3개의 단계 표지를 권장한다. 한 장면의 길이는 음성 길이를 따른다. 최종 50초가 필요하면 실제 설명을 충분히 준비하고 `minimum_duration: 50`으로 지정한다. 글자가 길면 오류를 내므로 줄바꿈하거나 장면을 나눈다.

## 기존 영상 편집

```json
{
  "output": "final.mp4", "speed": 1.4, "minimum_duration": 50,
  "fonts_dir": "fonts",
  "clips": [{"path": "a.mp4", "in": 0, "out": 35}, {"path": "b.mp4", "in": 0, "out": 35}],
  "captions": [{"start": 0, "end": 4.2, "lines": ["무엇을 확인할까?"], "highlight": 0, "y": 1450}]
}
```

```powershell
& $py $cli render timeline.json --dry-run
& $py $cli render timeline.json
```

경로는 JSON 위치 기준이다. 자막 시간은 이어 붙인 배속 전 시간이고 CLI가 배속을 나눠 적용한다. 영상·음성을 함께 변환하며 `atempo`로 음높이를 보존한다. 기본 1080×1920, 원본 Paperlogy 7 Bold 자막 스타일이다. 비율이 다르면 제품을 자동으로 잘라내지 않고 오류를 낸다. 기존 출력은 덮어쓰지 않는다. 출력 옆 `.ass`, `.render.json`, `.render.log`가 생성된다.

## 고정 화면 합성

```json
{
  "source": "fixed-shot.mp4", "screen": "screen-demo.mp4", "output": "composite.mp4",
  "fixed_camera_confirmed": true, "duration": 4,
  "corners": [[100,200],[900,200],[900,700],[100,700]],
  "protected_polygons": [[[450,200],[550,200],[550,230],[450,230]]],
  "brightness": 0.91, "offset": 3
}
```

좌표는 원본 픽셀의 왼쪽 위→오른쪽 위→오른쪽 아래→왼쪽 아래다. 예시 좌표를 다른 영상에 그대로 쓰지 않는다. 보호 다각형은 노치 등 원본을 유지할 영역이다. 두 입력 모두 요청 길이를 충족해야 하며 자동 반복하지 않는다. 원본 음성을 보존한다.

```powershell
& $py $cli compose-screen screen.json
```

## 음성 시간 분석·검수

```powershell
# segments.json = [{"start":0.3,"end":2.6}]
& $py $cli align-voice original.wav generated.mp4 segments.json alignment.json
& $py $cli inspect final.mp4 --decode --output qa.json
& $py $cli frames final.mp4 qa-frames --count 24
```

음량 변화 패턴으로 0.9~1.1배 길이와 ±0.6초 범위를 탐색한다. 서로 다른 대사·무음은 신뢰하기 어렵다. 실제 발화 일치·음색·입싱크를 자동 판정하거나 수정하지 않는다. 검수 프레임은 영상 전체를 균등 추출하며 자연스러움 판정은 사람이 한다.

## 한 번에 요청하기

> 고니 GitHub qwer777qq/goni-skill의 skills/goni-reverse-video 전체를 내 Codex·Claude 스킬 폴더에 설치해줘. SKILL.md와 references/cli.md를 읽고 필요한 로컬 도구를 확인해. 유료 API나 모델 다운로드 없이 내가 준 상품 자료로 사진·도해형 소개영상을 만들고, 원본 영상이 있으면 컷·자막·배속·고정 화면 합성을 적용해줘. 1.4배속 후 최종 50초 이상을 확인하고 MP4·타임라인·ASS·검수 결과를 남겨줘. 실제 촬영·성능 실측과 설명용 합성을 구분해줘.
