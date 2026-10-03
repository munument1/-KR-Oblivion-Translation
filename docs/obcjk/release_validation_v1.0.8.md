# v1.0.8 obCJK 표시 설정 검증

- 기준 obCJK: 20261003
- obCJK DLL SHA-256: `fe5742c19a3950f79936065be1ffa489023020d7aa260dc3d7275d8debb986a4`
- 한국어 프리셋 SHA-256: `ca50c81f40657fcd2b7bcc95683e2f5935c274e124dbb64a3652884271138523`
- ActiveCodePage: `UTF8`
- UILang: `ko`
- AsciiRenderEnable: `0`
- 슬롯 2: `OutlineMode=2`, `OutlineSize=2`, `OutlineAlpha=100`
- 슬롯 1/3/5/7/8/33/34/35/36/37: `OutlineMode=0`
- NorthernUI Shadowed 역할(FontParam36): 추가 Shadow 강제 적용 없음
- 기존 본명조 KR Medium / 본명조 KR / 이롭게바탕체 설정 유지
- 최신 upstream [BIG5] 및 일반 obCJK 설정 구조 보존
- 자동 테스트: 48/48 통과
- 수동 인게임 확인: 슬롯 2만 2px 외곽선을 적용한 구성이 사용자 테스트에서 정상 표시로 확정됨

v1.0.8은 번역 레코드, canonical 데이터, 메뉴 GMST FormID 및 지형 구조를 변경하지 않는다.
