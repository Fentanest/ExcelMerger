# ExcelMerger

크로스 플랫폼 Excel 시트 병합 도구. PySide6 데스크톱 UI에서 여러 워크북·시트를 시트별/수직/수평으로 합치고, 사용 가능한 오피스 런타임에 따라 4개 병합 엔진 중 최적 엔진을 자동 선택합니다.

## 프로젝트 구조

```
.
├── main.py                       # 엔트리: from excelmerger import main
├── version.py                    # __version__ (CI가 sed로 읽음)
├── ExcelMerger.spec              # PyInstaller 스펙 (main.py로부터 의존성 추적)
├── requirements.txt              # 런타임 의존성 (PySide6, JPype1, msoffcrypto-tool, pywin32, openpyxl, xlrd, pyxlsb)
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
│   ├── file_handler.py           # 입력 파일 열기/암호 해제/시트 열거 (GUI/헤드리스 공용)
│   ├── headless.py               # GUI 없이 병합하는 HeadlessSession + CLI
│   ├── engines/
│   │   ├── detector.py           # Excel/LibreOffice/JPype 가용성 감지
│   │   ├── utils.py              # 시트명 규칙, 매크로 소스 감지
│   │   ├── standard.py           # openpyxl 기반 폴백 엔진
│   │   ├── libreoffice.py        # PyUNO 기반 LibreOffice 엔진
│   │   ├── poi.py                # JPype + Apache POI 엔진 (기본 권장)
│   │   └── win32.py              # Windows COM Excel 엔진
│   └── ui/
│       ├── dialogs.py            # PasswordDialog(파일 암호 해제) + OptionsDialog(통합 환경설정)
│       ├── *_ui.py               # pyside6-uic 자동 생성 (편집 금지)
│       └── forms/*.ui            # Qt Designer 원본 (main, options, password)
└── tests/                        # unittest (단위 + POI 통합)
```

## 옵션 다이얼로그 구조

`OptionsDialog`(360×625)가 메뉴의 단일 환경설정 진입점이며, 위→아래로 5개 그룹을 가짐:

1. **시트 이름 규칙** — OriginalBoth / OriginalSheet / OriginalFileName
2. **병합 방식** — 시트별 / 가로 / 세로
3. **데이터 정리** — N줄 이상 빈 행/열 제거
4. **전역 비밀번호 / 출력 암호화** — 입력 파일 일괄 복호화 비밀번호 + 출력 파일 암호화 비밀번호 (2개 체크박스 + 비밀번호 입력)
5. **병합 엔진** — 자동/Excel/LibreOffice/Java/Python (아래 표 참조)

`MainWindow.open_options_dialog()`가 다이얼로그에 `engine_status`, `current_options`, `security`(전역 비밀번호 + 출력 암호화 상태)를 모두 전달하고, `dialog.get_options()` + `dialog.get_security()`로 결과를 회수해 한 번에 반영.

## 엔진 아키텍처

엔진 선택은 **옵션 다이얼로그**(`OptionsDialog`)에서만 변경 가능. 메인 UI에는 셀렉터를 두지 않습니다. 5개 옵션:

| 키        | 라벨                      | 가용성 게이트                                  |
|-----------|---------------------------|-----------------------------------------------|
| auto      | 자동 (사용 가능한 최고 엔진) | 항상 활성                                      |
| excel     | Microsoft Excel            | `detector.detect_excel().available && win32`  |
| libre     | LibreOffice                | `detector.detect_libreoffice().available && merger_libre.is_usable()` |
| jpype     | Java (Apache POI)          | `detector.detect_jpype().available`            |
| standard  | Python (openpyxl)          | `detector.detect_standard().available`        |

`app.py::MainWindow.resolved_engine()` 결정 로직:

```
options.merge_engine == "auto"
└── AUTO_PRIORITY = (excel, libre, jpype, standard) 순회 → 첫 가용 엔진
options.merge_engine == 특정 엔진
├── 해당 엔진 가용 → 그대로 사용
└── 아니면 로그 출력 후 AUTO_PRIORITY로 폴백
```

각 엔진은 동일한 3개 메서드를 노출 (이름은 다름): `merge_as_sheets_*`, `merge_horizontally_*`, `merge_vertically_*`. `app.py::_execute_merge`가 (`engine_key`, `merge_type`) 매트릭스로 디스패치.

### 책임 분리 원칙
- `standard` 엔진은 **openpyxl/xlrd/pyxlsb를 사용한 순수 Python 폴백**. POI로의 위임은 하지 않으며, 폴백 라우팅은 `app.py::resolved_engine()`이 단일 지점에서 결정.
- `detector.py`만 외부 런타임을 탐색하며, 결과는 `{key, label, available, detail, path}` 딕셔너리로 통일.
- `file_handler.convert_to_xlsx`는 win32 → POI → openpyxl/xlrd/pyxlsb 순으로 시도; 변환 자체는 항상 임시 .xlsx로 산출.
- 옵션 다이얼로그가 매번 열릴 때 `detect_merge_engines()`로 가용성을 재평가하여 비활성 라디오를 갱신.

### 핵심 기술 요점
- **VBA 보존**: `engines/utils.py::has_macro_source`로 입력에 .xlsm이 있는지 판정 → Win32 Excel 엔진만 `FileFormat=52`로 저장. LibreOffice/POI/standard 엔진은 매크로를 보존하지 않으며 `.xlsx`로 저장.
- **POI 변환·복사**: `engines/poi.py::convert_to_xlsx`가 .xls/.xlsb/.xlsm/.csv를 읽어 새 XSSFWorkbook으로 재저장. `_copy_sheet`는 셀값/수식/스타일/병합셀/열너비를 `style_cache`/`font_cache`/`data_format_cache`로 중복 생성 없이 복사하며, 같은 캐시는 `convert_to_xlsx`/`merge_*`에서 공유 가능.
- **JVM 부트스트랩**: `engines/poi.py::_ensure_jvm`이 `runtime_paths.bundled_java_home()`로 `lib/jre`를 우선 탐지 후 시스템 JRE로 폴백. JAR classpath는 `lib/poi/`의 9개 (`poi-5.3.0`, `poi-ooxml-5.3.0`, `poi-ooxml-lite-5.3.0`, `commons-collections4-4.4`, `commons-io-2.16.1`, `commons-compress-1.26.2`, `commons-codec-1.17.1`, `xmlbeans-5.2.1`, `log4j-api-2.24.1`).
- **LibreOffice 연결**: `engines/libreoffice.py::_ensure_connection`이 `localhost:2002` UNO 소켓에 먼저 접속, 실패하면 `soffice --headless --accept=socket,host=localhost,port=2002;urp;`로 새 인스턴스 기동. PyUNO 모듈은 `_import_uno()`로 지연 로드. 시트 복사는 `XSheets.importSheet`.
- **암호화**: `settings.py`는 base64로 비밀번호 인코딩만 수행. 기존 `secret.key`(Fernet) 파일이 있으면 첫 로드 시 복호화→base64 재저장→키 파일 삭제로 마이그레이션. 출력 파일 자체 암호화는 `msoffcrypto-tool`로 처리.
- **자동 업데이트**: `updater.py::check_for_update`가 `https://api.github.com/repos/Fentanest/ExcelMerger/releases/latest` 호출. `_runtime_asset_fragment`가 `bundled_java_home()` 존재 여부로 `-jre` 자산을 자동 선택. 다운로드 후 플랫폼별 스크립트(Windows .cmd / Linux .sh / macOS hdiutil)로 실행 파일 교체.

## 빌드 / 패키징

- PyInstaller는 **onedir 모드**로 빌드 (`EXE(exclude_binaries=True) + COLLECT`). 산출물은 `dist/ExcelMerger/` 디렉터리(실행파일 + `_internal/` 라이브러리). onefile은 사용하지 않음.
- `ExcelMerger.spec`은 `EXCELMERGER_INCLUDE_JRE=1` 환경변수로 `lib/jre`를 datas에 조건부 포함.
- CI 산출물 흐름 (`.github/workflows/build.yml`, `build-test.yml`):
  - **build-windows / build-linux**: `dist/ExcelMerger/` 폴더를 그대로 `actions/upload-artifact`로 업로드 (확장자 없는 이름). 사전 zip 단계 없음 → 다운로드 시 GitHub의 자동 zip 래핑 1회만 적용되어 zip-in-zip 미발생.
  - **build-macos-x64 / build-macos-arm64**: `hdiutil`로 DMG 생성 후 단일 파일로 업로드.
  - **release** (build.yml만): 모든 아티팩트 다운로드 후 플랫폼 패턴으로 재포장 — Windows는 `zip -r`, Linux는 `tar -czf`, macOS는 DMG 패스스루. 4 플랫폼 × `include_jre` 매트릭스 = 8 산출물.
- 각 빌드 잡은 PyInstaller 실행 직전에 UPX 5.1.1을 설치 (Windows: GitHub release zip, Linux: amd64_linux tar.xz, macOS: `brew install upx`). `ExcelMerger.spec`의 `upx=True`가 PATH의 upx를 사용해 실행 파일을 압축.
- Windows 잡은 PyInstaller 직후 `dist/ExcelMerger/ExcelMerger.exe`의 핸들이 풀릴 때까지 최대 120초 폴링 (Defender/UPX/PyInstaller 후처리 잠금 회피).
- `updater.py`는 onedir 번들을 인지: `sys._MEIPASS == sys.executable의 부모`인지 확인하여 `target_info.type = "bundle"`로 분기, Windows는 `robocopy /MIR`, Linux는 `rm -rf + cp -R`로 디렉터리 통째 교체.
- 검증 베이스라인: Python 3.14 + JPype1 1.7.1 + OpenJDK 21. Linux에서는 단위 테스트, JPype 병합, PyInstaller 빌드를 확인했다. macOS는 JPype wheel이 없을 수 있어 소스 빌드 경로를 탈 수 있다.

## 개발 워크플로

```bash
python -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python main.py                       # GUI 실행
./venv/bin/python -m unittest discover -s tests # 단위 테스트
./ui.sh                                         # .ui 수정 후 *_ui.py 재생성
```
