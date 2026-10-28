# Final Cut 인수 · 자동화

## 담당자가 한 번 준비할 자료

평소 프로젝트의 **사본**에서 대표 자막·점수판·주제 표시를 하나씩 남긴 작은 프로젝트를 FCPXML로 내보낸다. 글자 자리에는 `{{TEXT}}`, 별도 강조 run에는 `{{KEYWORD}}`처럼 토큰을 넣는다. 연결된 Motion 템플릿·설치 폰트 이름과 사용 가능한 라이선스도 기록한다. 자료를 공개 저장소에 넣을 필요는 없다.

타이틀 이름 예시: `JY_LESSON_WHITE`, `JY_REPLY_NAVY`, `JY_COURSE_CYAN`, `JY_ASIDE_HAND`, `JY_MATCH_SCORE`, `JY_PRODUCT_BOLD`. 템플릿마다 좌표·색·굵기·외곽선·그림자·화자 태그·입출 모션·기본 지속시간을 seed에 보존한다. 점수판은 선수명·홀·PAR·거리·타수를 각기 토큰화하며 확인한 데이터만 입력한다.

정확한 폰트와 모션은 원본 seed가 기준이다. 화면을 보고 추정한 값은 시험용으로만 쓴다. 사진·음악·협찬 자산도 프로젝트에서 합법적으로 사용할 수 있는 경로로 연결한다.

## 실행

Python 3.10 이상 표준 라이브러리만 필요하다. 원본 미디어는 사용자의 컴퓨터에 둔다. `examples/plan.json`을 복사해 파일 URI, 프레임레이트, 해상도, 원본 길이와 컷을 **실제 ffprobe/편집기 값으로** 바꾼다.

```sh
python scripts/assemble.py plan.json --out output
python scripts/assemble.py plan.json --seed personal-titles.fcpxml --out output-with-style
```

출력: `edit.fcpxml`, `captions.srt`, `edit-map.json`, `validation.json`. 기존 출력 폴더를 덮어쓰지 않는다. 자막은 원본 프레임 기준이고 삭제 컷을 통과하며 분할·리플 이동된다. fps는 `30000/1001`처럼 유리수로 유지한다. 무음 탐지나 모델 판단으로 컷을 자동 삭제하지 않는다.

seed 없이도 영상·음성 조립과 별도 SRT를 만들 수 있지만 스타일은 미반영이다. `--seed`를 줬는데 요청한 타이틀/토큰이 없으면 실패한다. 리소스 참조와 text-style을 복사한다. 키프레임이 있는 타이틀의 길이를 임의 변경하지 않고 원본 지속시간과 다르면 실패한다. 이때 편집자가 원하는 길이의 템플릿을 추가하거나 모션을 검수해야 한다. 복합 점수판·멀티캠·속도변경·전환은 이 작은 조립 스크립트의 자동 처리 범위가 아니다.

## Mac에서 인수

1. 기존 라이브러리 사본에 출력 FCPXML 가져오기. 번들 `.fcpxmld` seed는 내부 FCPXML 파일을 선택한다.
2. 미디어·폰트·Motion 효과 연결과 실제 fps·해상도 확인. SRT와 스타일 타이틀을 같은 화면에 중복 켜지 않는다.
3. 각 장르·화자·긴 문장·공 이동·점수 갱신을 재생해 원본 편집과 비교한다. 텍스트를 바꿔도 상자/모션이 유지되는지 확인한다.
4. 저장·종료·재열기 후 짧은 내보내기. 프레임·소리·블랙·자막 중첩·공 위치를 확인하고 본편 전체를 출력한다.

이 배포판의 FCPXML은 구조/시간 매핑 단위 테스트까지 검증했다. Windows에서 Final Cut 실행·렌더는 검증하지 않았다. XML 파싱 성공은 Final Cut 가져오기 성공과 다르다.

공식 근거: [Apple XML 전송](https://support.apple.com/guide/final-cut-pro/use-xml-to-transfer-projects-verdbd66ae/mac), [자막 가져오기](https://support.apple.com/guide/final-cut-pro/import-captions-ver4185ef95a/mac), [FCPXML](https://developer.apple.com/documentation/professional-video-applications/fcpxml), [DTD](https://developer.apple.com/documentation/professional-video-applications/document-type-definition), [Motion 템플릿](https://help.apple.com/motion/mac/5.0/help/English/en/motion/usermanual/chapter_11_section_1.html).
