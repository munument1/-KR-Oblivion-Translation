# obCJK 전환 조사 — 2026-10-01

대상은 Oblivion Original의 본PC Windows 환경이다. Steam Deck 작업과 검증은 제외한다.

## 결론

- **obCJK backend의 우선 인코딩은 UTF-8**으로 권고한다. 실제 바이트 처리와 전역 설정은 [소스 분석](obcjk_source_analysis.md)에 근거한다.
- 확인한 obCJK 20260807 배포 설명과 공식 GitHub main에서는 **Bink 동영상 외부 자막 기능을 확인하지 못했다**. 게임 내 대사 자막의 폰트 지원과 동영상 자막은 구분해야 한다. 기존 인트로/아웃트로 SRT와 자막 삽입 BIK는 유지한다.
- 현재 legacy 데이터를 UTF-8로 단순 재인코딩하면 안 된다. 조사한 23개 CSV, 84,349행 중 **39,239행은 Unicode 한국어 칸이 비어 있으면서 legacy hex에 번역이 들어 있다**. 복원 및 왕복 검증이 선행되어야 한다.
- 이전 종료는 아직 원인이 확정되지 않았다. Windows Application 오류 기록 20건과 별도의 obCJK 훅 성공 로그를 확보했다. 전체 변환에 앞서 별도 프로필의 원본 게임 + xOBSE + obCJK부터 재현해야 한다.

## 작업 기준과 보존

작업 브랜치: `obcjk-unicode`.

작업 시작 당시 로컬 main은 v1.0.3 커밋 `f73c270`이었다. 원격 main 및 v1.0.4 태그를 fetch하고 **작업 브랜치만** v1.0.4 `be9140e7cee72034be033fd66ac67518e23ac010`으로 fast-forward했다. 로컬 main과 기존 태그, 원격 릴리즈에는 쓰지 않았다.

사용자가 알려준 MO2의 Default 프로필을 읽기 전용으로 조사했다. 설치된 1.0.4 적용 여부는 사용자 보고를 따른다. 기존 mod 메타데이터나 이전 audit만으로 설치된 각 GMST의 최종 바이트를 인증한 것은 아니다.

기존 공식 KR, UOP/USIP/UODP KR, obCJK, Default 프로필 및 실행 환경 파일 총 99개(761,006,408 bytes)를 SHA-256 목록으로 기록했다. 이 목록은 백업 사본이 아니라 변경 감지 기준이다. 이번 조사에서 게임·MO2 모드·프로필·INI는 수정하지 않았다.

조사 종료 시 위 99개를 다시 해시 비교했고 변경 0개였다. 검증 결과는 `_build/obcjk/research/preservation_check.json`에 있다. 비교 범위는 캡처 목록이며 전체 게임 폴더를 비교한 것은 아니다.

머신별 절대경로와 원본 로그는 이미 Git에서 제외되는 `_build/obcjk/research/` 아래에만 보관한다.

## 요청한 첫 단계 산출물

| 항목 | 결과 |
|---|---|
| obCJK 소스/동작 분석 | [obcjk_source_analysis.md](obcjk_source_analysis.md) |
| 기존 인코딩 구조 및 CSV 실태 | [legacy_encoding_analysis.md](legacy_encoding_analysis.md), [csv_inventory.json](csv_inventory.json) |
| 방식 차이와 변경 목록 | [migration_plan.md](migration_plan.md) |
| 즉시 종료 후보 및 현재 확인 결과 | [startup_diagnosis.md](startup_diagnosis.md) |
| 권고 인코딩과 근거 | [소스 분석의 인코딩 결정](obcjk_source_analysis.md#인코딩-결정) |
| 최소 ESP/빌드 계획 | [migration_plan.md](migration_plan.md), [obcjk_smoke_test.md](obcjk_smoke_test.md) |

현재 단계는 조사와 계획 작성이다. 기존 빌더 코드, 번역 CSV, 설치기, ESP/ESM은 변경하거나 실행하지 않았다. 게임 실행·한글 표시·저장 재로드는 이번 조사에서 검증하지 않았다.
