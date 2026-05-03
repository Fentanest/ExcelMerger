# Excel Merger 2.0

| Windows | Ubuntu |
| --- | --- |
| ![poster](./lib/windows.png) | ![poster](./lib/ubuntu.png) |

여러 개의 엑셀 파일에서 원하는 시트만 골라 하나의 결과물로 합치는 PySide6 기반 데스크톱 앱입니다. v2 리워크에서는 엔진 선택 구조, 설정 마이그레이션, LibreOffice/JPype 연동, 직접 업데이트 흐름을 추가해 크로스플랫폼 배포 구조를 정리했습니다.

## 주요 기능

- 드래그 앤 드롭 또는 다중 선택으로 `.xlsx`, `.xls`, `.xlsm`, `.xlsb`, `.csv` 파일 추가
- 시트 병합, 가로 병합, 세로 병합 지원
- 암호화된 입력 파일 열기 및 결과 파일 암호화 지원
- 병합 엔진 선택:
  - `표준 병합`
  - `Microsoft Excel 이용` (Windows에서 Excel 감지 시)
  - `LibreOffice 이용` (LibreOffice 감지 시)
- Microsoft Excel 엔진에서 `.xlsm` 소스 감지 시 출력 확장자를 `.xlsm`으로 자동 보정
- JPype/Apache POI 런타임이 준비되어 있으면 고품질 fallback 엔진으로 사용
- 시작 시 GitHub Releases 최신 버전 확인 및 패키징된 앱에서 직접 업데이트 시도
- 검증된 POI 런타임 조합: `Python 3.13 + JPype1 1.6.0 + Java 17/21`

## 엔진 동작 방식

- 사용자가 `Microsoft Excel 이용`을 선택했고 Excel이 감지되면 Win32 엔진을 사용합니다.
- 사용자가 `LibreOffice 이용`을 선택했고 PyUNO 런타임까지 준비되어 있으면 LibreOffice 엔진을 사용합니다.
- 선택한 고품질 엔진을 사용할 수 없으면 `JPype(Apache POI)`로 폴백합니다.
- JPype도 사용할 수 없으면 `표준 병합` 엔진으로 폴백합니다.

## 설정 저장 방식

- `secret.key` 파일을 더 이상 사용하지 않습니다.
- 비밀번호는 `config.ini`에 base64 인코딩으로 저장됩니다.
- 기존 `secret.key`와 Fernet 기반 설정이 있으면 읽어서 새 형식으로 재저장한 뒤 `secret.key`를 제거합니다.

## Apache POI 준비

JPype 엔진을 사용하려면 `lib/poi/` 아래에 다음 JAR 파일을 배치하세요.

- `poi-5.3.0.jar`
- `poi-ooxml-5.3.0.jar`
- `poi-ooxml-lite-5.3.0.jar`
- `commons-collections4-4.4.jar`
- `commons-io-2.16.1.jar`
- `commons-compress-1.26.2.jar`
- `commons-codec-1.17.1.jar`
- `xmlbeans-5.2.1.jar`
- `log4j-api-2.24.1.jar`

개발/CI 기준 런타임은 `Python 3.13`과 `JPype1 1.6.0`입니다. `JPype1 1.7.0`은 이 프로젝트의 `WorkbookFactory` 경로에서 Python 3.13/3.14 조합으로 JVM 크래시가 재현되어 현재는 사용하지 않습니다.

선택적으로 번들 JRE를 포함하려면 `lib/jre/` 아래에 런타임을 배치하고, 빌드 시 `EXCELMERGER_INCLUDE_JRE=1`을 사용하세요. 개발 환경에서는 Android Studio JBR 대신 일반 OpenJDK 17/21 또는 번들 JRE 사용을 권장합니다.

## 개발 메모

- 앱 진입점은 `main.py`이며 실제 리워크된 메인 윈도우는 `app_main.py`에 있습니다.
- PyInstaller 스펙은 `ExcelMerger.spec`입니다.
- 수동 8종 테스트 빌드는 `.github/workflows/build-test.yml`의 `workflow_dispatch`로 실행할 수 있습니다.
- 변경 내역은 `CHANGELOG.md`를 참고하세요.
