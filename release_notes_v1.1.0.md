## v1.1.0 — 대사 재검수 및 위치명 통합

### 본편·공식 DLC

- Oblivion Original의 INFO 대사를 다시 검수해 의미 오류, 화자/대상 혼동, 고유명사·잠금 용어 불일치, 영어 잔존과 한국어 형태 오류를 교정했습니다.
- 후보 직접 검수 6,464건을 완료했고, 별도 KEEP 감사에서도 고유 2,454건을 직접 확인했습니다.
- 최종 canonical INFO에는 FIX 판정 7,874건을 통합했으며 실제 문자열 변경은 7,873건입니다.
- 지도 마커와 현재 위치·발견 위치에 쓰이는 CELL/WRLD/REFR/REGN 한국어 위치명을 보강했습니다.
- 임페리얼 시티 Arena / Elven Gardens / Palace / Prison / Market / Talos Plaza / Temple / Waterfront 지도 마커를 실제 출력 ESM에서 검증했습니다.
- 과거 바이트 방식에서 저장 문제를 피하려고 사용하던 CELL/WRLD 영어 유지 제약을 제거했습니다.
- 릴리즈 빌드는 legacy 한국어 중간 ESM/ESP를 만들지 않고 canonical UTF-8 데이터를 원본 플러그인에 직접 적용합니다.

### 언오피셜 패치 KR

UOP / USIP / UODP 한국어 번역은 **GitHub v1.1.0 설치기 ZIP에 포함하지 않습니다.**
각 영문 패치에 대응하는 KR ZIP을 **Nexus에서 별도 파일로 배포**합니다.
새 OBCJK 빌드에서는 UOP/USIP/UODP가 위치 레코드를 덮어쓰는 경우에도 CELL/WRLD/REFR/REGN 한국어 위치명을 함께 전달합니다.

### 검증

- canonical 총 47,227행 / INFO 25,119행 유지.
- FormID, 레코드 구조, 필드 순서 및 컴파일된 스크립트 보존 검사 통과.
- GMST 37개 예약 FormID 충돌 회귀 검사 통과.
- 프로젝트 자동 테스트 50/50 통과.
- 직접 UTF-8 Python 빌드와 기존 검증 OBCJK 출력 플러그인 10개 SHA-256 10/10 동일.
- 새 PyInstaller EXE 출력과 Python 직접 빌드 플러그인 10개 SHA-256 10/10 동일.
- 통합 언오피셜 빌드는 기존 2단계 위치 빌드와 13/14 ESP가 바이트 동일했고, 나머지 Knights ESP는 기존 방식이 놓친 `The Lost Catacombs → 잃어버린 지하 묘지` CELL 1건을 추가 교정했습니다.

### 요구 사항

- MO2
- xOBSE
- **obCJK 20261003 이상**

새 설치기 ZIP을 새 폴더에 풀고 `install.bat`을 실행한 뒤 생성된 `output/Oblivion_KR_Mod`로 기존 본편 번역 모드를 교체하세요.
언오피셜 패치 KR은 Nexus의 별도 파일을 사용하세요.
