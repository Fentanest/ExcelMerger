# ExcelMerger

크로스 플랫폼 Excel 시트 병합 도구. PySide6 데스크톱 UI에서 여러 워크북·시트를 시트별/수직/수평으로 합치고, 사용 가능한 오피스 런타임에 따라 4개 병합 엔진 중 최적 엔진을 자동 선택합니다.

## 프로젝트 구조

```
.
├── main.py                       # 엔트리: from excelmerger import main
├── version.py                    # __version__ (CI가 sed로 읽음)
├── ExcelMerger.spec              # PyInstaller 스펙 (main.py로부터 의존성 추적)
├── requirements.txt              # 런타임 의존성 (PySide6, JPype1, msoffcrypto-tool, pywin32)
├── requirements-dev.txt          # 테스트 픽스처용 (openpyxl)
├── ui.sh                         # excelmerger/ui/forms/*.ui → *_ui.py 재생성
├── config.ini                    # 사용자 설정 (런타임 생성, 비추적)
├── README.md, CHANGELOG.md, CLAUDE.md, LICENSE
├── lib/
│   ├── poi/*.jar                 # Apache POI 9개 (CI에서 다운로드되거나 로컬 보관)
│   ├── jre/                      # JRE 번들 빌드 시에만 (lib/jre 존재 → 자동 감지)
│   ├── logo.png, logo.ico
├── excelmerger/                  # 애플리케이션 패키지
│   ├── __init__.py               # main, __version__ 재export
│   ├── app.py                    # MainWindow + main() 진입점
│   ├── settings.py               # config.ini 직렬화 + secret.key 마이그레이션
│   ├── runtime_paths.py          # PyInstaller 번들/개발 모드 공통 경로 헬퍼
│   ├── updater.py                # GitHub Releases 자동 업데이트
│   ├── file_handler.py           # 입력 파일 열기/암호 해제/시트 열거
│   ├── engines/
│   │   ├── detector.py           # Excel/LibreOffice/JPype 가용성 감지
│   │   ├── utils.py              # 시트명 규칙, 매크로 소스 감지
│   │   ├── standard.py           # openpyxl 기반 폴백 엔진
│   │   ├── libreoffice.py        # PyUNO 기반 LibreOffice 엔진
│   │   ├── poi.py                # JPype + Apache POI 엔진 (기본 권장)
│   │   └── win32.py              # Windows COM Excel 엔진
│   └── ui/
│       ├── dialogs.py            # 비밀번호/암호화/옵션 다이얼로그
│       ├── *_ui.py               # pyside6-uic 자동 생성 (편집 금지)
│       └── forms/*.ui            # Qt Designer 원본
└── tests/                        # unittest (단위 + POI 통합)
```

## 엔진 아키텍처

`excelmerger/app.py::MainWindow.resolved_engine()`이 다음 순서로 실행 엔진을 결정:

```
사용자 라디오 선택(merge_engine 옵션)
├── "excel"    → Excel 감지됨 + win32com 사용 가능 → engines/win32.py
├── "libre"    → LibreOffice 감지됨 + PyUNO 사용 가능 → engines/libreoffice.py
├── "standard" → openpyxl 사용 가능 → engines/standard.py
│              └ 없으면 jpype로 자동 강등
└── 모든 자동 폴백 실패 → RuntimeError
```

각 엔진은 동일한 3개 메서드를 노출 (이름은 다름): `merge_as_sheets_*`, `merge_horizontally_*`, `merge_vertically_*`. `app.py::_execute_merge`가 (`engine_key`, `merge_type`) 매트릭스로 디스패치.

### 책임 분리 원칙
- `standard` 엔진은 **openpyxl만** 다룸. POI로의 폴백 라우팅은 `app.py::resolved_engine()`이 단일 지점에서 결정하며, 엔진 내부에서 다른 엔진을 호출하지 않음 (이전의 `_use_poi_first` 우회 헬퍼는 제거됨).
- `detector.py`만 외부 런타임을 탐색하며, 결과는 `{key, label, available, detail, path}` 딕셔너리로 통일.
- `file_handler.convert_to_xlsx`는 win32 → POI → openpyxl 순으로 시도; 변환 자체는 항상 임시 .xlsx로 산출.

### 핵심 기술 요점
- **VBA 보존**: `engines/utils.py::has_macro_source`로 입력에 .xlsm이 있는지 판정 → Win32 엔진은 `FileFormat=52`로 저장, UI 파일 다이얼로그 필터도 동적으로 .xlsm 추가 (`app.py::_save_file_filter`).
- **POI 변환·복사**: `engines/poi.py::convert_to_xlsx`가 .xls/.xlsb/.xlsm/.csv를 읽어 새 XSSFWorkbook으로 재저장. `_copy_sheet`는 셀값/수식/스타일/병합셀/열너비를 `style_cache`/`font_cache`/`data_format_cache`로 중복 생성 없이 복사하며, 같은 캐시는 `convert_to_xlsx`/`merge_*`에서 공유 가능.
- **JVM 부트스트랩**: `engines/poi.py::_ensure_jvm`이 `runtime_paths.bundled_java_home()`로 `lib/jre`를 우선 탐지 후 시스템 JRE로 폴백. JAR classpath는 `lib/poi/`의 9개 (`poi-5.3.0`, `poi-ooxml-5.3.0`, `poi-ooxml-lite-5.3.0`, `commons-collections4-4.4`, `commons-io-2.16.1`, `commons-compress-1.26.2`, `commons-codec-1.17.1`, `xmlbeans-5.2.1`, `log4j-api-2.24.1`).
- **LibreOffice 연결**: `engines/libreoffice.py::_ensure_connection`이 `localhost:2002` UNO 소켓에 먼저 접속, 실패하면 `soffice --headless --accept=socket,host=localhost,port=2002;urp;`로 새 인스턴스 기동. PyUNO 모듈은 `_import_uno()`로 지연 로드. 시트 복사는 `XSheets.importSheet`.
- **암호화**: `settings.py`는 base64로 비밀번호 인코딩만 수행. 기존 `secret.key`(Fernet) 파일이 있으면 첫 로드 시 복호화→base64 재저장→키 파일 삭제로 마이그레이션. 출력 파일 자체 암호화는 `msoffcrypto-tool`로 처리.
- **자동 업데이트**: `updater.py::check_for_update`가 `https://api.github.com/repos/Fentanest/ExcelMerger/releases/latest` 호출. `_runtime_asset_fragment`가 `bundled_java_home()` 존재 여부로 `-jre` 자산을 자동 선택. 다운로드 후 플랫폼별 스크립트(Windows .cmd / Linux .sh / macOS hdiutil)로 실행 파일 교체.

## 빌드 / 패키징

- PyInstaller가 `main.py`로부터 정적 import 추적으로 `excelmerger.*`를 모두 수집.
- `ExcelMerger.spec`은 `EXCELMERGER_INCLUDE_JRE=1` 환경변수로 `lib/jre`를 datas에 조건부 포함.
- CI(`.github/workflows/build.yml`)는 4 플랫폼 × `include_jre: [false, true]` = 8 산출물을 생성하여 GitHub Release에 업로드.
- 검증 베이스라인: Python 3.13 + JPype1 1.6.0 + OpenJDK 17/21. JPype 1.7.0은 JVM 충돌 이슈로 회피.

## 개발 워크플로

```bash
python -m venv venv
./venv/bin/pip install -r requirements-dev.txt
./venv/bin/python main.py                       # GUI 실행
./venv/bin/python -m unittest discover -s tests # 단위 테스트
./ui.sh                                         # .ui 수정 후 *_ui.py 재생성
```
