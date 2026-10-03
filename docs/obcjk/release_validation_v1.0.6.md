# v1.0.6 검증 기록

날짜: 2026-10-03

- 사용자 게임 비교 테스트에서 기존본의 지형 누락과 수정본의 정상 지형 표시를 확인했다.
- 설치기 생성 ESM은 테스트 수정본과 SHA-256이 같다: `b9b8e5d14d8a4412f58f50b91c4e993b10f6f2a34cbb966891dec1d5b220ed26`.
- 전체 레코드 1,167,838개 유지. 레코드 추가·누락 및 보호된 필드 변경 없음. OFST 85개 제거.
- 공식 TES4Edit 재로드에서 CELL/LAND/REFR FormID 집합이 영문 원본과 일치하고, 추가 메뉴 GMST 821개를 확인했다.
- frozen 설치기를 원본 Data에 실행해 동일한 수정 ESM 생성을 확인했다. 공식 DLC 9개와 메뉴·글꼴 설정은 기존 출력과 같다.
- 회귀 테스트 31개 통과.
- 최신 원격 소스의 영상 분리 정책을 유지한다. 설치기 기본값과 BAT 실행 인자는 영상 생성 off이다.
- 1.0.6은 최신 소스에서 EXE를 다시 빌드하고 버전이 갱신된 README·CHANGELOG와 함께 패키징한다. 언오피셜 패치 ZIP은 변경하지 않는다.

근거 파일: `_build/obcjk/terrain-fix-test/final-verification.json`, `native-final-readback.json`, `_build/obcjk/terrain-release-replacement-20261003/frozen-installer-verification.json`, `_build/obcjk/release-v1.0.6/frozen-installer-verification.json`.
