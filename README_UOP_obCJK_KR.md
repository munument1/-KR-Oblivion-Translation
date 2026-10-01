# Unofficial Oblivion Patches 한국어 UTF-8 오버레이

obCJK용 한국어 번역입니다. 대상 원본 버전은 **UOP 3.5.9a / USIP 1.6.2 / UODP v27**이며, 서로 다른 버전의 원본 ESP를 이 파일로 덮지 마세요.

## MO2 설치

1. xOBSE와 obCJK, 해당 버전의 영문 Unofficial Oblivion Patch / Unofficial Shivering Isles Patch / Unofficial Oblivion DLC Patches를 먼저 설치합니다.
2. 본편·공식 DLC용 `Oblivion_KR_obCJK` 번역 모드를 활성화합니다. 글꼴 설치와 프로필 INI 설정은 본편 **v1.0.5 설치기** 안내를 따릅니다.
3. 이 ZIP을 MO2에서 별도 모드로 설치합니다. 최상위에는 기본 패치 ESP 11개가 있습니다. 왼쪽 목록에서 영문 언오피셜 패치 및 본편 번역 모드보다 아래에 두어 같은 이름의 ESP를 덮도록 합니다.
4. `Optional`의 `Oblivion Citadel Door Fix.esp`와 `DLCThievesDen - Unofficial Patch - SSSB.esp`는 해당 영문 선택 패치를 사용하던 경우에만 모드 최상위로 옮깁니다.
5. 설치된 DLC에 해당하는 ESP만 활성화하며, 플러그인 이름과 기존 로드 순서를 유지합니다. 이전 방식의 `Unofficial ...-KR` 모드와 `_UTF8_Test`/`_Locations_Test` 시험판은 끕니다.
6. MO2에서 Oblivion을 실행합니다. xOBSE·obCJK 본체와 MO2의 강제 로드 설정은 본편 설치 안내를 따릅니다.

이 ZIP에는 xOBSE/obCJK DLL, 본편 ESM, 원본 패치의 메시·텍스처·음성 파일 및 Windows 글꼴이 들어 있지 않습니다. 해당 파일은 각각의 원본 모드에서 읽습니다. 번역 대상이 없는 `UOP Vampire Aging & Face Fix.esp`는 원본 파일을 그대로 사용합니다.

## 변경과 검증

기존 검증된 한국어 패치 번역을 UTF-8로 변환하고 검증된 CELL/WRLD 한글 위치명을 적용했습니다. 종족 이름은 원본과 같이 영어로 유지합니다. 원문 대조가 확정되지 않은 문자열은 영어로 남을 수 있으며 완역을 주장하지 않습니다.

각 출력은 원본 대비 레코드·그룹 식별자, FormID, 필드 순서와 컴파일된 스크립트가 보존되는지 검사했습니다. `validation.json`에 UTF-8 변환 및 위치명 검증 수치, 원본·출력 SHA-256을 기록했고, `SHA256SUMS.txt`는 ZIP 안 ESP 파일을 확인하는 데 사용합니다.

MO2 시험 구성에서 한글 위치명이 들어간 저장 파일 생성과 한국어 메뉴 표시를 확인했습니다. 모든 언오피셜 패치의 퀘스트·대화·장시간 플레이를 개별 검증한 것은 아닙니다. 기존 한글 바이트 방식 폰트 및 번역 모드와 섞어 사용하지 마세요.

원본 패치 제작자: Unofficial Patch Project Team / Arthmoor 및 해당 패치 크레딧에 포함된 기여자들. 이 파일은 한국어 번역 ESP 오버레이이며 원본 패치의 기능·자산 제작 크레딧은 원 저자에게 있습니다.
