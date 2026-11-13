# 자연스러운 배경·소품 변환 시험

아래는 합성 예시용 초안이다. 실제로 실행한 프롬프트와 성공한 결과를 구분해 기록한다. 원본 동작이 복잡하면 먼저 한 동작으로 축소한다.

## 기준 영상 프롬프트

Photorealistic live-action commercial test, one continuous locked tripod shot, 5 seconds, vertical 9:16. An anonymous adult wearing an ivory linen shirt sits at a clean oak desk inside a softly lit studio. Frame chest, both forearms and tabletop; face outside the top edge. One plain kraft paper cup without a lid, handle or print. The right hand gently grips the middle of the cup, lifts it 8 cm, pauses, and sets it back in the same position. Left hand rests on table. Restrained real-time movement, five fingers, stable contact and realistic occlusion. Soft window light from camera left, natural skin and paper texture, accurate contact shadows. 50mm perspective, no camera move, cuts, focus pumping, added objects, text, logos, music or speech. Preserve a physically rigid cup throughout.

## 원본 프레임 편집 프롬프트

Edit this extracted frame only. Keep the person's exact pose, ivory linen shirt, hands, finger positions, oak tabletop, composition and lens perspective unchanged. Replace only the indoor background with a quiet outdoor terrace with softly defocused foliage. Replace the kraft cup with a pale sage ceramic cup of identical outer dimensions, without a handle, lid or logo. Preserve the grip and occlusion at every finger. Soft light from camera left matching the source. Restrained glaze highlights, realistic contact shadows, natural photographic detail. No added people, objects or text.

## 영상 편집 프롬프트

Use the input video as the sole motion and timing reference. Across its full duration, change only the background and cup to match the edited reference image. Preserve the original person, clothes, hands, exact finger motion, oak desk, composition, duration and camera position. The cup must move rigidly with the same grip; maintain exact hand-object occlusion and stable dimensions. Keep its base in contact with the desk before lifting and after setting down. Match light direction and cast shadows. No new cuts, speed changes, camera drift, cup morphing, floating objects, extra fingers, text, music or speech.

모델별 실제 참조명은 업로드 후 확인해 위 문구에 넣는다. 영상 편집 모드와 일반 참조 생성 모드를 혼동하지 않는다.

## 자연스러움 판정

- 동일 시각의 원본/변환을 나란히 보고 손과 컵의 궤적·크기·접촉을 비교한다.
- 시작·중간·끝 정지 표본 외에 전체 재생으로 컵 변형·떨림·배경 깜빡임을 확인한다.
- 손의 접촉이 실제처럼 보이지 않으면 미완성으로 두고 해당 구간을 수정한다.
- 얼굴 없는 예시는 얼굴 또는 입싱크 검증을 대신하지 않는다.
- 참고 광고의 느낌은 조명·구도·재질에 적용하되 원본 광고 이상의 품질이라고 검수 전 보장하지 않는다.
- 최종 썸네일은 실제 검수 영상 프레임과 짧은 질문으로 만든다. 기획 이미지를 성공 결과처럼 게시하지 않는다.
