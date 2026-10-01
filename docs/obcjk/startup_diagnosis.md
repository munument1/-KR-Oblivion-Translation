# 이전 메인 메뉴 전 종료 조사

2026-10-01 사용자 확인: **메인 메뉴가 나오기 전에 종료**. 실패 당시 기존 KR 모드 동시 활성화 여부는 아직 미확인이다. 현재 Default 모드 목록에는 ObCJK와 공식/언오피셜 KR이 모두 활성화되어 있으나 이를 과거 실패 조건이라고 단정하지 않는다.

판정: **NOT DIAGNOSED YET — 접근 위반 증거는 확보했고 원인 확정 및 새 재현 실행은 남아 있다.**

## 확보한 증거

| 증거 | 확인 사실 | 해석 한계 |
|---|---|---|
| Windows Application Event 1000 | 당일 Oblivion.exe 접근 위반 `0xc0000005` 20건 | 호출 stack/minidump 없음 |
| 오류 RVA `0x00175ba9` | 18건 | 소스의 문자열 렌더링 함수 영역과 인접한다는 후보 단서 |
| 오류 RVA `0x000f00d5` | 2건, 마지막 두 시각 13:54:18/13:55:10 | 다른 오류군일 수 있으므로 하나로 합치지 않음 |
| obCJK.log (13:57:29 파일 시각) | Query/Load, UTF8 선택, glyph/wrap/save 훅 ok, renderer/device 및 첫 frame task | 위 오류 이벤트보다 늦은 로그이며 동일 실행으로 결합할 수 없음 |
| obse.log (14:55:59 파일 시각) | xOBSE 22.13, 새 게임/여러 저장과 deinitialize | obCJK 활성화된 동일 실행인지 확인 불가 |
| obse_loader.log | Steam loader 사용, inject 완료 | 별도 시각의 기록으로 한글 렌더링 성공을 의미하지 않음 |
| MO2 Default settings | LocalSettings=false, LocalSaves=true, obse_1_2_416.dll force-load 설정 | profile-local oblivion.ini가 없다는 것만으로 누락 오류라고 볼 수 없음 |
| 실제 Documents 게임 INI | SFontFile 1/2/3이 TheGreatestKorean, 4/5는 원본 Daedric/Handwritten | 현재 설정이며 과거 실패 실행의 INI 내용은 아님 |
| 모드 내 DLL | obCJK, UOP jail/training fix | 전체 게임 실행 시 로드 모듈 목록은 아님 |
| MO2 crashDumps | 조사 시 파일 없음 | Windows WER 등 다른 위치의 dump 가능성은 남음 |

RVA를 이미지 기준 주소 `0x00400000`에 더하면 18건 오류 주소 후보는 `0x00575ba9`다. obCJK 소스에서 Path B를 `sub_575870`이라고 명명하며 `0x00575A48` 등을 후킹한다. **인접 주소만으로 특정 명령·폰트 함수·모드를 원인으로 확정할 수 없다.** 심볼/호출 stack 또는 조건 분리 재현이 필요하다.

원본 로그와 오류 요약은 Git에서 제외되는 `_build/obcjk/research/`에 보존했다. 로그가 이번 시도에서 덮여쓰이지 않도록 게임을 새로 실행하지 않았다.

## 원인 후보의 현재 상태

1. **obCJK DLL 로딩 실패:** 13:57 실행의 Load/훅/frame 기록과 양립하지 않는다. 최초 실패 실행의 로드 상태는 아직 미확인.
2. **xOBSE 훅 초기화 실패/주소 충돌:** 소스는 고정 VA를 사용하고 버전 불일치에서 Query가 계속 true를 반환한다. 하지만 로컬 EXE는 요구되는 1.2.0.416이며 성공 로그에 여러 훅 ok가 있다. 별도 실행/후속 렌더링 실패와 구분해야 한다.
3. **설정 문제:** 상대경로의 INI, 전역 codepage, 기본 BIG5 fallback이 핵심이다. 현재 INI는 UTF8이지만 당시 INI는 보존된 `.bak`들과 비교해야 한다. 로컬 프로필 설정은 game INI 공유 모드다.
4. **폰트/텍스처 문제:** 현재 게임 폰트 설정은 TheGreatestKorean이며 obCJK UTF8 폰트는 Klee/Noto CJK TC/일본어 폰트 이름 등이다. 한글 커스텀 폰트 구조 + 새 atlas 훅을 함께 사용한 조건을 원본 폰트 조건과 분리한다. 특정 폰트 결함으로 확정하지 않는다.
5. **ESP/ESM 인코딩 불일치:** 현재 legacy 바이트 + UTF8 모드 조합은 호환되지 않는다. 이는 깨진 표시의 충분한 후보이나 접근 위반의 입증은 아니다. 영문 원본 + obCJK에서 동일 실패가 나는지를 먼저 본다.
6. **다른 OBSE DLL 충돌:** UOP의 jail/training fix가 추가 변수다. 현재 파일 목록에 없는 NorthernUI/MenuQue를 원인으로 지목하지 않는다. 원본+xOBSE+obCJK 기준을 통과한 후 하나씩 추가한다.

## 다음 재현 절차

Default 프로필을 그대로 두고 별도의 `obcjk-isolation` 프로필을 만든다. 설정과 save 폴더도 분리한다. 사용자의 기존 세이브를 쓰거나 수정하지 않는다.

| 단계 | 활성 구성 | 관찰 | 다음 단계 조건 |
|---|---|---|---|
| A | 원본 영문 + xOBSE, obCJK 없음 | 메인 메뉴 도달, 30초 유지 | 기준 실행 성공 |
| B | A + obCJK만, UTF8, 원본 기본 fnt/tex, 설치 확인 한글 폰트 | 메인 메뉴 전 종료 재현 여부, 신규 로그/오류 시각 | B 성공 또는 B 실패 원인 증거 확보 |
| C | B + 최소 UTF-8 테스트 ESP | 한글 GMST/이름 표시 | B에서 안정성이 확인된 뒤 |
| D | C + 원본 UOP DLL 하나씩 | 주소 충돌/새 종료 여부 | C 성공 |
| E | 검증한 UTF-8 공식/언오피셜 번역 구성 | 메뉴/새 게임/저장 재로드 | 최소 테스트 및 무결성 통과 |

B가 실패하면 첫 메뉴 전 실패를 그대로 수집하며 전체 번역 변환을 진행하지 않는다. B는 성공하고 legacy 폰트/legacy KR을 추가할 때만 실패하면 그 두 변수를 별도 단계로 나눠 재현한다. 이미 잘못된 인코딩 혼합 구성을 최종 실행 환경으로 채택하지 않는다.

각 실행에서 DLL/EXE/INI hash, 활성 mods/plugins, 시작·종료 시각, 새 obCJK/OBSE 로그, Event 1000의 RVA를 하나의 run ID로 묶는다. 로그 파일 시각만으로 과거 실행 조건을 복구할 수는 없다.

## 도구 상태

MO2 MCP를 사용자 지정 root에 bind했다. 현재 MO2는 닫혀 있고 broker/sidecar 연결은 없으며 metadata-editable ceiling이다. xEdit MCP 상태는 not_started다. 이 조사에서는 별도의 도구 설치나 live bridge 배포를 하지 않았다. 플러그인 제작/레코드 검증 단계에서는 사용자 지정 MO2에 연결된 xEdit MCP와 Oblivion 지원 여부를 확인해야 한다.

이 문서는 원인 확정 보고서가 아니다. A/B의 재현 성공·실패 및 동일 실행 로그가 아직 필요하므로 인코딩 변경과 전체 ESP/ESM 빌드는 시작하지 않는다.
