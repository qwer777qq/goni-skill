# 다른 PC 설치

전체 전달 세트를 먼저 압축 해제한다. Windows 10/11 x64, Node.js 24.15 이상, Python 3.12 또는 3.13, FFmpeg/ffprobe가 필요하다. 최초 설치는 인터넷과 6GiB 이상 여유 공간이 필요하다. CPU 전사도 가능하지만 large-v3는 느릴 수 있다.

1. 세트의 START-HERE.md에 따라 선행 도구를 설치한다.
2. `00-check.cmd`로 점검한 다음 `01-install.cmd`를 실행한다. Python 가상환경과 고정 버전 패키지, 검증된 large-v3 모델을 내려받고 스킬을 설치한다.
3. Codex를 다시 열고 `$goni-cliploom-highlights`로 호출한다. `02-start.cmd`는 기본 4187 포트에서 앱을 시작한다.

설정은 LocalAppData/GoniCliploom/cliploom.env, 영상·DB·모델은 같은 위치의 data, 가상환경은 .venv다. 설치기는 실제 경로를 해석하므로 Windows 앱 가상화 경로도 현재 PC에 맞게 저장한다. 기존 설정과 같은 이름의 스킬은 자동 덮어쓰지 않는다.

Windows에서는 FFMPEG_PATH/PYTHON_EXECUTABLE/YTDLP_PATH에 슬래시(/)가 들어간 절대 실행파일 경로가 필요하다. PYTHONUTF8=1과 PYTHONIOENCODING=utf-8을 유지해야 한글 전사 결과가 깨지지 않는다. 모델 경로는 WHISPER_MODEL_PATH다.

원본 provision-whisper.mjs는 스크립트 상대 경로에 모델을 저장하므로 설치기가 런타임 scripts에 복사해 실행한다. 원본 데이터·모델을 전달 세트에 복사하지 않는다. doctor 종료코드만 보지 말고 media.transcription 등 실제 플래그를 확인한다. 결제·메일·공개 서버 운영 점검은 로컬 편집 모드에서 미설정일 수 있다.
