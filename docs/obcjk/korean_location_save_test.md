# 한글 위치명 저장 검증 — 2026-10-01

사용자 요청: obCJK의 Unicode 저장 지원으로 위치명도 한국어로 바꿀 수 있는지 확인하고 실제 저장/재로드를 시험한다. 이 실험에 한해 한글 위치명을 사용하며, 전체 legacy 빌드의 CELL/WRLD 영어 유지 정책은 아직 변경하지 않는다.

후속 변경: 사용자가 기본 번역 Unicode 표시를 먼저 확인하도록 순서를 바꾸었다. 승인 후 `obcjk-save-test`를 세이브 없이 복제했고 임시 MO2 권한은 원래 metadata-editable로 복원했다. [메뉴 실행 검증](utf8_ui_test_results.md)을 완료했으며, 아래 저장 시험 계획과 미실행 결과는 그대로 남아 있다. 이전 CEILING001 차단은 해결된 과거 기록이다. 현재 본문 ESP 제작 제한은 xEdit MCP의 Oblivion 모드 미지원이다.

## 소스 확인 결과

한글 위치명이 포함된 저장 파일명을 지원하도록 설계되어 있다.

- [CreateFileW shim](https://github.com/AophMiSaki/obCJK/blob/4cbdacc0c4970cbfb46650c92ba2b0dcb7bff6a6/obse_plugin_example/include/obCJK_CreateFileWShim.h): 게임의 CreateFileA 호출을 가로채 active codepage에서 UTF-16 경로로 변환해 CreateFileW를 사용한다. UTF8 모드라면 위치명도 유효한 UTF-8이어야 한다. 변환 실패 시 기존 ANSI 경로로 fallback한다.
- [저장 목록 shim](https://github.com/AophMiSaki/obCJK/blob/4cbdacc0c4970cbfb46650c92ba2b0dcb7bff6a6/obse_plugin_example/include/obCJK_SaveListFindShim.h): FindFirstFileW/FindNextFileW로 파일명을 읽고 active codepage로 되돌린다. 파일 생성과 목록/재로드를 별도로 보정한다.
- [길이 절단 훅](https://github.com/AophMiSaki/obCJK/blob/4cbdacc0c4970cbfb46650c92ba2b0dcb7bff6a6/obse_plugin_example/include/obCJK_SaveNameTruncateHook.h): .ess 경로가 255 bytes를 넘으면 UTF-8 문자 경계에서 잘라 확장자를 유지한다. 무제한 경로 지원은 아니다.

즉, 위치명 때문에 기존 저장이 실패했던 ANSI 파일 I/O 경로를 고치는 코드는 있다. 그러나 커스텀 legacy 바이트를 자동으로 Unicode로 만드는 코드는 아니며, 소스만으로 설치된 DLL/게임 실행의 성공을 확정할 수 없다.

## 구체적인 실험 구성

- 프로필: `obcjk-save-test`, Default에서 세이브 제외 복제.
- profile-local INI와 독립 save folder 사용. 기존 세이브 사본도 첫 실험에는 가져오지 않음.
- 원본 영문 게임 + xOBSE 22.13 + 복제한 obCJK 테스트 전용 overlay.
- 기존 공식 KR/UOP KR/USIP KR/UODP KR은 이 프로필에서 비활성화. 원본 Default 구성은 보존.
- 원본 기본 fnt/tex와 설치 확인된 Malgun Gothic 사용. 테스트 복제 INI에서 `ActiveCodePage=UTF8`, `SaveDiagEnable=1`.
- 먼저 새 게임/영문 위치에서 저장이 되는지 기준 실행. 메인 메뉴 전 종료가 재현되면 원인 조사로 전환.

첫 실험은 전체 master 재빌드 대신 **테스트 세션에서 현재 CELL의 표시 이름만 변경**하는 방법을 우선 검토한다. 현재 CELL은 xOBSE `player.GetParentCell`의 실제 결과로 식별하며 FormID를 추측하지 않는다. SetCellFullName 또는 SetName 사용은 해당 명령의 문서와 엔진 콘솔 실행 결과로 확인한다. Unicode 입력은 ASCII 콘솔 입력과 구분하여 engine batch 파일/실제 command parser에 전달되는 UTF-8 bytes를 확인해야 한다.

이 방식은 저장 파일 I/O의 예비 실험이다. 최종 CELL/FULL 또는 WRLD/FULL 번역 plugin의 영구 적용 검증을 대신하지 않는다. 실제 plugin 테스트는 xEdit MCP에서 별도 작은 override를 제작한 뒤 반복한다. ESP/ESM을 자체 parser로 쓰거나 수정하지 않는다.

## 합격 조건

| 시험 | 필수 확인 |
|---|---|
| 영문 기준 위치 | 수동 저장이 실제 .ess/.obse 파일을 생성하고 재로드 성공 |
| 짧은 한글 위치명 `한글 저장 시험방` | 새 슬롯 저장의 실제 파일명에 한글 위치명 포함, SaveDiag write ok |
| 받침/ASCII/괄호/하이픈 `값·꽃·읽음 시험방 (ABC 123)-A` | 실제 파일명 및 저장 목록에 손상 없이 표시 |
| 같은 테스트 슬롯 덮어쓰기 | .ess/.obse 갱신 및 backup 동작, 사용자 기존 슬롯은 사용하지 않음 |
| 게임 완전 종료 후 재실행 | 한글 파일이 목록에 보이고 로드 성공, 플레이어 상태/위치 확인 |
| 긴 위치명 | 255-byte 경계 절단 시 UTF-8 문자/확장자 보존, 재로드 가능 |

긴 이름의 절단 정책은 경로 충돌 가능성을 별도로 확인한다. 동일 prefix의 다른 이름이 같은 파일명으로 잘리는 경우를 정상으로 받아들이지 않는다. CELL 성공만으로 WRLD/모든 DLC/모든 기존 세이브까지 성공했다고 확대하지 않는다.

## 현재 실행 상태와 도구 제한

소스 확인 완료. 게임 실행과 한글 위치명 저장 실험은 **아직 미실행**.

MO2 MCP의 `mo2_clone_profile` plan 요청은 `CEILING001`으로 차단됐다. 현재 root의 `permission_ceiling=metadata-editable`이고 이 작업에는 `full-control`이 필요하다. 같은 작업을 다른 도구로 우회하지 않았다. 프로필/모드/INI/기존 세이브에는 쓰지 않았다.

실험 시작 전 필요한 권한 변경안을 `_build/obcjk/save-test/mo2-mcp.proposed.json`에 작성한다. 적용 대상은 사용자 지정 MO2의 `.mo2-mcp.json`이며, 테스트 프로필 접근과 기존 Default/모드 경로 보호를 함께 설정한 뒤 재bind 결과로 실제 제한을 확인한다. 권한 변경에는 사용자 승인이 필요하다. 설정 파일이 없었던 현재 상태로 돌아갈 수 있도록 복원 정보를 기록한다.

## 실제 실행 결과

| 항목 | 상태 |
|---|---|
| 영문 기준 저장/재로드 | 미실행 |
| 짧은 한글 위치명 | 미실행 |
| 받침/문장부호/영어 혼합 | 미실행 |
| 새 슬롯/덮어쓰기/backup | 미실행 |
| 재실행 후 저장 목록/로드 | 미실행 |
| 긴 위치명 | 미실행 |
| CELL/FULL plugin 적용 | 미실행 |
| WRLD 위치명 | 미실행 |

현재 결론은 **가능성이 소스로 뒷받침됨, 런타임 검증 전**이다.
