# 1.0.5 야외 진입 낙하 제보 조사

2026-10-03. 대상: 오리지널 Oblivion. 제보: 지하감옥에서 나온 뒤 땅속으로 떨어짐.

## 판정

실제 게임 재현과 이번 낙하의 원인 확정은 아직 하지 못했다. 공식 TES4Edit 검사에서 추가 메뉴 GMST의 잘못된 파일 슬롯에 따른 FormID 충돌을 확인했다. 이 결함과 별개로 원본 ESM의 OFST 위치표를 보존하면서 파일 내부 위치를 변경하는 빌드 경로도 유력한 지형 로딩 문제 후보다.

## 현재 확인한 증거

- `D:/Oblivion MO2/mods/Oblivion_KR_Mod/Oblivion.esm`과 `_build/obcjk/release-v1.0.5/video-fix/package/output/Oblivion_KR_Mod/Oblivion.esm`의 SHA-256은 모두 `b1fdd5861d98efc56572e9e3c8f938762db3478512bc54ffc18e2eaf56bb97df`다.
- 원본과 설치된 ESM 모두 바이트 38에서 OFST 문자열이 검색된다. 이는 단순 바이트 검색이며 개별 위치표 항목의 구조/유효성 검사는 아니다.
- `build_vanilla_overlay.py:478` 부근 TES4 처리에서는 HEDR의 개수만 바꾸고 나머지 헤더 본문을 그대로 복사한다. 번역과 821 GMST 삽입으로 이후 파일 위치는 바뀐다.
- `build_obcjk_overlay.py:201`과 `build_unofficial_release.py:181`의 재작성도 허용된 문자열 외의 데이터를 그대로 보존한다. 현재 빌더/검사에는 OFST 재계산이나 정규화 처리가 없다.
- 기존 검증은 레코드/그룹 식별자와 허용 문자열 외 바이트 보존을 확인한다. 파일 위치표 유효성 또는 하수도 출구 통과와 야외 지형 충돌 검증은 포함하지 않는다.
- Wrye Bash 개발 문서는 OFST가 절대 파일 위치를 담고 있으며 파일 수정 시 무효가 된다고 설명한다. 제거만으로는 원래 잘못 정렬된 그룹의 문제가 드러날 수 있으므로 무조건 삭제하는 수정은 권하지 않는다.
  https://github.com/wrye-bash/wrye-bash/wiki/%5Bdev%5D-OFST

## 검증 제한과 다음 확인

- xEdit MCP를 Oblivion 모드로 시작했으나 `Unsupported game mode: Oblivion. Supported game modes: Fallout4, Skyrim, SkyrimSE, Starfield`로 실패했다. 레코드 판독 결과를 확보하지 못했다.
- 게임 재현, 제보 세이브, 한패 활성/비활성의 동일 출구 비교 결과는 아직 없다. 따라서 OFST 문제는 유력한 가설이지 이번 낙하의 확정 원인이 아니다.
- 출구 직전 세이브로 완전히 종료/재실행하면서 1.0.5 활성/비활성을 비교하고, 지형 표시와 충돌/낙하를 함께 확인해야 한다.
- 수정은 원본과 현재 배포본을 보존한 별도 시험 출력에서 수행하고 실제 야외 진입으로 검증해야 한다. 이번 조사에서는 게임 파일, 프로필, 배포 자산을 변경하지 않았다.

## 공식 TES4Edit 4.1.5f 직접 검사

사용자가 Nexus의 TES4Edit(11536)로 검사하도록 지정해 공식 제작자 GitHub의 같은 4.1.5f를 받아 실행했다. 앞의 MCP 미지원 제한과 별개로 stock TES4Edit를 사용할 수 있었다. 원본 및 한패 ESM을 작업 폴더에 복사해 `-DontRemoveOffsetData -nofixup -skipbsa -nobuildrefs -DontCache`로 읽었다. 한패는 `-cp:utf8`도 지정했다. `-DontRemoveOffsetData`는 xEdit가 기본적으로 OFST를 메모리에서 제거하는 동작을 막기 위해 필요하다.

- 도구: https://www.nexusmods.com/oblivion/mods/11536
- 공식 다운로드: https://github.com/TES5Edit/TES5Edit/releases/tag/xedit-4.1.5f
- 다운로드 7z SHA-256: `54c014da621f83f06a64fd92ddb8e32ed3082d1c65f543dc1c4e432130dced08`.
- 원본 ESM SHA-256: `a26e21ea8c3041f8737ffb3a266129dedb7f8a88590625ecfecd5eb7f66b4a70`. 기존 빌드 검증 JSON의 original_sha256과 같다.
- stock TES4Edit 읽기 전용 Pascal 스크립트 및 로그/추출/비교 JSON: `_build/obcjk/terrain-incident-20261003/`.
- 헤더 OFST 및 84개 WRLD OFST는 모두 원본/한패의 GetEditValue 추출 결과가 같다. Tamriel OFST는 17,681줄이며 양쪽 텍스트 SHA-256은 `1e679f999b7be92ab6f3dd6aed3e0c5413a4b24e5b42e1587c7329a7763293d2`다.
- 단순 바이트 검색으로 Tamriel EDID 표식은 원본 파일 위치 37,257,453, 한패 파일 위치 37,833,272에서 발견됐다. 표식 위치 이동은 575,819바이트다. 이 검색 자체는 OFST 항목의 정확한 해석/유효성 검사가 아니다.
- 새 게임 하수도 출구: 실내 REFR `0004BED7` → 실외 `CharGenExitRef` REFR `0000A395`. XTEL 위치 `47073.230469 / 82958.085938 / 301.770263`, 회전 `0 / 0 / 45`는 같다.
- 실외 CELL `ICPrisonSewerExit01` `00005E3D`, Tamriel 격자 `(11,20)`의 추출 필드는 모두 같다.
- 초기 집계에서는 xEdit가 색인한 CELL/LAND/REFR 개수가 일부 달랐다. 이를 파일 내 레코드 삭제로 단정하지 않고 별도 FormID 추출로 조사한다. HEDR에는 문서화된 GMST 821개 증가가 있고, 파일 전체 레코드 수와 xEdit 내부 색인 수는 구분한다.

지금까지 결과는 위치표 보존 문제를 뒷받침하지만 실제 게임 낙하의 확정 원인을 입증하지 않는다. 출구 좌표 오역/변경은 비교한 두 ESM에서 관찰되지 않았다.

## 추가 메뉴 GMST FormID 충돌 확인

`menu_gmst_new_821.csv`의 37개 행이 `0100xxxx` FormID를 사용한다. 마스터가 없는 `Oblivion.esm`의 파일 슬롯 01은 유효하지 않다. 공식 4.1.5f의 `TwbMainRecord.DoGetFixedFormID`는 슬롯이 MasterCount보다 크면 자기 파일 슬롯으로 바꾸며, 따라서 `01000809`는 `00000809`로 해석된다. 그 결과 기존 FormID와 충돌하고 xEdit의 중복 FormID 건너뛰기 경로가 적용된다.

- `sAge 01000809` → `00000809`: 기존 CELL `ChorrolFireAndSteel`와 충돌.
- `sCombatName 01000869` → `00000869`: 기존 LAND와 충돌.
- `LowIdAudit.tes4pas`로 한패의 해당 ID를 직접 `RecordByFormID` 조회해 `00000809`가 CELL 대신 GMST `sAge`, `00000869`가 LAND 대신 GMST `sCombatName`으로 반환되는 것을 확인했다. 근거 파일은 `_build/obcjk/terrain-incident-20261003/kr105/low-id-audit.tsv`다.
- 별도 RecordByIndex 추출을 대조했을 때 한패 xEdit 색인에서 빠진 CELL 15개, LAND 1개, REFR 14개 모두 메뉴 GMST의 정규화된 ID와 일치한다. 이 30개의 정확한 대조는 `menu-formid-collisions.json`에 있다.
- INFO 1개, STAT 2개, TREE 1개도 색인 집계에서 감소했지만 초기 ID 추출 범위에 없으므로 이 문서에서 개별 FormID 충돌 확정으로 표현하지 않는다. 37개 모두 충돌했다고 단정하지 않는다.
- `ChorrolFireAndSteel`의 EDID와 CELL 헤더 바이트 표식은 원본/한패 파일 양쪽에 여전히 있다. 파일에서 레코드를 삭제한 문제와 로더 색인 충돌은 구분해야 한다.
- 기존 빌더의 충돌 검사는 raw FormID의 완전 일치만 확인하므로 파일 슬롯을 정규화한 충돌을 놓쳤다.
- 공식 소스: https://github.com/TES5Edit/TES5Edit/blob/xedit-4.1.5f/Core/wbImplementation.pas (DoGetFixedFormID).

수정 방향은 새 메뉴 레코드의 적법하고 충돌 없는 ID 배정 및 정규화된 ID 검사, OFST/그룹 구조의 올바른 재작성이다. 이번 요청에서는 검사만 수행했으며 빌더/게임/배포 파일은 수정하지 않았다. 이 FormID 결함을 이번 하수도 낙하의 단독 원인으로 확정하지 않는다.

## 언오피셜 1.0.5 분리 감사

본편의 문제 GMST는 메뉴 번역을 위해 추가한 레코드다. 언오피셜 번역 배포에는 이 추가 작업이 없다. UOP 원본 자체의 기존 GMST 10개와 본편에 추가한 메뉴 GMST를 구분한다.

UOP/USIP/UODP 1.0.5 ZIP의 ESP 13개는 현재 MO2 한패 설치본과 모두 SHA-256이 일치했고, 비교에 사용한 원본 13개도 배포 검증 JSON의 original_sha256과 일치했다. 양쪽을 별도 디렉터리에 복사하고 같은 영문 공식 마스터를 사용해 TES4Edit 4.1.5f로 읽기 전용 검사했다.

- 13개 모두 원본/한패의 레코드 FormID 및 시그니처 집합, 시그니처별 개수, 마스터 목록이 같다. 추가/누락 레코드가 없다.
- UOP는 양쪽 86,425개 레코드 및 기존 GMST 10개가 같고, GMST ID/EDID도 같다. 나머지 12개 ESP에는 GMST가 없다. 잘못된 파일 슬롯의 GMST가 없다.
- USIP는 양쪽 12,900개 레코드가 같다.
- 13개 모두 헤더/WRLD OFST가 없다. 본편의 보존된 OFST 가설은 이 ESP들에 적용되지 않는다.
- 근거: `_build/obcjk/terrain-incident-20261003/unofficial-package-verification.json`, `unofficial-audit-comparison.json`, 두 디렉터리의 xEdit TSV/TXT 및 실행 로그.
- 번역본 헤더 CNAM(Author) 문자열 표시에서 코드 페이지 변환 경고가 있었다. 위 비교는 문자열 표시의 성공이나 모든 기능 필드의 동등성을 의미하지 않는다.

검사 범위에서 언오피셜 번역본 자체에는 본편과 같은 GMST 충돌/레코드 누락이 관찰되지 않았다. 본편 1.0.5 ESM과 함께 설치하면 본편의 결함은 여전히 별도로 남는다. 실제 하수도 출구 낙하의 재현 및 원인 확정은 아직 하지 않았다.

## 수정 시험본 (2026-10-03)

사용자의 수정 요청에 따라 기존 1.0.5 배포본과 현재 활성 MO2 모드는 보존하고 별도 시험본을 만들었다.

- 메뉴 CSV의 잘못된 `0100xxxx` 37개만 `00F10001`부터 `00F10025`로 재배정했다. 번역 열은 바꾸지 않았다. 빌더는 비정상 파일 슬롯을 거부하고 원본 FormID의 하위 24비트 충돌도 검사한다.
- 영문 원본에서 UTF-8 및 한국어 지명 포함 전체 출력을 다시 만들었다. 기존 1.0.5 frozen-output-final과 37개 GMST 헤더 ID를 매핑한 뒤 전체 레코드를 대조해 다른 내용 차이가 없었다(`v105-content-comparison.json`).
- 공식 TES4Edit로 원본 OFST 제거 경로를 사용하고 native PrepareSave로 구조를 정렬해 별도 저장했다. 해당 파일은 중간 산출물이다.
- 정밀 비교에서 native 저장이 CELL/REFR/ACHR/PGRD 107개의 필드를 자동 보정하고, 원본에 있던 REFR 10개의 raw 슬롯을 정규화하는 것을 발견했다. script 모드의 편집 허용 때문에 `-nofixup`만으로 이를 막을 수 없었다. 첫 중간 출력은 헤더 OFST도 그대로 남아 있었다. 이 중간 파일은 배포 대상이 아니다.
- `finalize_oblivion_master.py`는 기존 reader/writer를 사용해 native 그룹 순서를 유지하면서 입력의 레코드 필드·헤더·기존 raw ID를 복원하고 TES4/WRLD OFST 85개만 제거한다. `verify_canonical_oblivion.py`가 전체 레코드의 ID, 플래그, VCS, 부모 그룹 경로, 문자열 및 비문자열 바이트를 검증한다(OFST와 native HEDR recount만 제외).
- 최종 검증: 레코드 1,167,838개 유지, 추가/누락 0, 보호된 필드 변경 0, OFST 0. 입력 두 파일 SHA 불변. `final-verification.json`의 passed=true.
- 최종 ESM SHA-256: `b9b8e5d14d8a4412f58f50b91c4e993b10f6f2a34cbb966891dec1d5b220ed26`.
- 회귀 테스트 26개 통과. 실제 게임에서 낙하가 해결됐는지는 아직 검증하지 않았다.

재현 단계:

1. 현재 빌더로 영문 게임 Data에서 별도 UTF-8/지명 출력물을 만든다.
2. 그 출력의 `Oblivion.esm`만 격리해서 `scripts/CanonicalizeOblivion.tes4pas`를 공식 4.1.5f로 실행한다. 필요 인수는 스크립트 주석에 있다. 기존 출력물을 덮어쓰지 않고 입력 파일을 저장하지 않는다.
3. `python finalize_oblivion_master.py <rebuilt/Oblivion.esm> <rebuilt/Oblivion.canonical.esm> --output <separate/Oblivion.esm> --report <report.json>`을 실행하고 passed=true를 요구한다.
4. 별도 TES4Edit 프로세스로 최종 파일을 재로드해 레코드 집계·출구 관련 ID·OFST 부재를 확인한다.
5. MO2의 별도 시험 모드로 본편 1.0.5보다 우선하게 적용한 뒤 게임을 완전히 재시작한다. 하수도 출구 직전 세이브로 야외 진입, 지형 표시, 충돌과 보행을 확인한다. 처음 테스트에서는 저장하지 않고 기존 정상 세이브를 보존한다.

기존 설치 EXE/ZIP은 재패키징하지 않았다. 기본 빌더 출력에는 아직 native 구조 최종화가 필요하므로, 위 2~4단계를 생략한 재빌드를 지형 수정 완료본으로 취급하면 안 된다.

시험 모드와 ZIP:

- MO2 별도 모드: `D:\Oblivion MO2\mods\Oblivion_KR_Terrain_Fix_Test_20261003` (Default 프로필 목록에 추가/활성화하지 않음).
- ZIP: `_build/obcjk/terrain-fix-test/Oblivion_KR_Terrain_Fix_Test_20261003.zip`.
- ZIP에서 ESM을 다시 읽은 SHA와 MO2 시험 모드 ESM SHA가 최종 검증 SHA와 같다. ZIP CRC 검사 통과.
- 게임 영문 원본과 현재 `Oblivion_KR_Mod/Oblivion.esm` SHA는 조사 시작 때와 같다(`package-verification.json`).

최종 fresh TES4Edit 재로드도 통과했다(`native-final-readback.json`): 모든 시그니처별 개수는 영문 원본과 같고 GMST만 의도한 821개 증가다. CELL/LAND/REFR 1,092,934개의 로드 FormID 집합이 원본과 같다. `00000809`는 다시 CELL ChorrolFireAndSteel, `00000869`는 LAND로 조회됐다. 헤더/WRLD OFST는 0개다.

## 2026-10-03 공개 1.0.5 설치기 교체

사용자 요청에 따라 버전/태그와 자산 이름을 유지하고 공개 GitHub 설치기 ZIP 및 .sha256을 교체했다. 릴리즈 설명에서는 사용자가 제외를 요청한 낙하 해결 여부 문구를 넣지 않았다.

- 기존 공개 ZIP SHA-256 `7d6cb53e0de82becf30d2e5d95c21a44b9d856c242127a5b33de1f67c0e30d9c` 및 EXE/설명은 `_build/obcjk/terrain-release-replacement-20261003/`에 보존했다.
- `assets/oblivion_native_layout.json.gz`에는 공식 TES4Edit 최종본의 레코드 키와 그룹 헤더/순서만 있다. 게임 레코드 payload는 포함하지 않는다. 원본 SHA, 생성 파일 SHA, 레이아웃 무결성과 출력 SHA를 검사한다.
- `master_layout.py`와 기존 writer로 설치기에서 native 구조를 재현한다. 기본 빌드도 이제 별도 TES4Edit 실행 없이 OFST 제거와 정렬을 완료한다. 앞 절의 수동 최종화 제한은 공개 교체 설치기에는 해당하지 않는다.
- 재빌드한 frozen EXE를 실제 영문 원본에 실행해 ESM SHA `b9b8e5d14d8a4412f58f50b91c4e993b10f6f2a34cbb966891dec1d5b220ed26` 재현 및 전수 보호 필드 검증을 확인했다. 공식 DLC 9개와 메뉴/글꼴 설정은 기존 출력과 같다. 테스트 30개 통과.
- 이번 frozen 실행은 동영상 생성을 `off`로 명시했다. 공개 설치기의 기존 기본값 `auto`와 동영상 생성 코드는 유지했다.
- 교체 ZIP SHA-256 `b1f2e3405fe0f48ba7ae40eff050555c479d3e75e4c953461798fdc375b8d426`, 39,780,518바이트.
- 업로드 후 공개 자산을 다시 다운로드해 SHA/체크섬과 설명 반영을 검증했다. `published-verification.json` 참조.
- 공개 URL: https://github.com/munument1/-KR-Oblivion-Translation/releases/tag/v1.0.5
