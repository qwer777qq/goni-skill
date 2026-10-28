# Premiere 실행과 경계

설치된 Premiere 버전과 연결 API를 먼저 읽는다. UXP/공개 스크립팅 API와 설치된 CEP 연결 수단을 사용한다. 프로그램 바이너리 추출·인증 우회는 필요하지 않다. 특정 사설 API를 전체 버전의 보장으로 취급하지 않는다.

현재 프로젝트 경로와 sequence ID를 새로 읽고 수정 범위를 고정한다. 원본 프로젝트를 보존하고, 컷·자막·효과를 별도 사본에서 시험한다. 자막 작업은 V1/A1의 소스 In/Out과 타임라인이 바뀌지 않았는지 비교한다. 저장된 닫힌 사본에서만 프로젝트 파일을 변환하고, 앱에서 열어 실제 글자·배경·폰트와 미디어 연결을 검증한다.

PNG·구워진 자막을 편집 가능한 타이틀로 부르지 않는다. SRT는 텍스트/시간 교환 파일이다. 실제 네이티브 텍스트 또는 문구 수정 가능한 MOGRT로 구현한다. 파크골프의 공·손·클럽 이동 영역은 강의의 얼굴 안전 영역과 다르다.

내보내기는 정확한 대상 sequence, 시작/끝, 출력 preset, 새 파일 경로를 확인한다. 범위를 임시 설정하면 복원하고 API 성공·실제 파일·ffprobe·디코딩·표본 프레임·청취 결과를 구별한다. 앱이 멈추거나 오류 창이 생기면 요청을 반복 적재하지 않는다.

Premiere용 xmeml XML과 Final Cut의 FCPXML은 다른 형식이다. 파일 확장자만 바꿔 전달하지 않는다. Premiere 시험 렌더 성공은 Final Cut의 폰트·모션·렌더 검증을 대신하지 않는다.

공식 자료: [Adobe Premiere UXP 샘플](https://github.com/AdobeDocs/uxp-premiere-pro-samples), [Adobe CEP PProPanel](https://github.com/Adobe-CEP/Samples/tree/master/PProPanel). 개인 작업장의 플러그인·템플릿·미디어는 이 배포판에 포함하지 않는다.
