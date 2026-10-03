## v1.0.8 — 자막 외곽선 및 최신 obCJK 설정

- obCJK 20261003의 Outline/Shadow 설정 구조를 한국어 프리셋에 반영했습니다.
- NPC 대사 자막과 HUD가 사용하는 **슬롯 2에만 검은색 Outline 2px / 100%**를 적용합니다.
- 메뉴·책·지도 등 다른 슬롯은 외곽선을 적용하지 않습니다.
- NorthernUI의 Shadowed 역할(FontParam36)에도 별도 Shadow 효과를 강제로 적용하지 않습니다.
- 본명조 KR Medium / 본명조 KR / 이롭게바탕체의 기존 크기·굵기·배치는 그대로 유지합니다.
- 최신 INI의 [BIG5] 및 기타 upstream 설정은 보존하고, 한국어 폰트 수정은 [UTF8]에만 적용하도록 설치기를 보강했습니다.
- 번역 데이터, canonical 데이터, 지형 FormID 수정은 v1.0.7과 동일합니다.

### 요구 사항

- MO2
- xOBSE
- **obCJK 20261003 이상**

### 업데이트 방법

새 설치기 ZIP을 새 폴더에 풀고 `install.bat`을 실행하세요. 생성된 `output/Oblivion_KR_Mod`로 MO2의 기존 번역 모드를 교체한 뒤 게임을 다시 시작하세요.

인트로·엔딩 한국어 자막 영상과 언오피셜 패치 KR은 기존 Nexus 별도 파일을 사용합니다.
