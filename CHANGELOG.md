# Changelog

## 2.0.0
- Added merge-engine detection and selection for standard, Microsoft Excel, and LibreOffice flows.
- Added a working LibreOffice/PyUNO merge engine, JPype/Apache POI runtime scaffolding, and direct-update preparation flows.
- Reworked settings storage to remove `secret.key` and migrate passwords to base64 encoding.
- Added headless merge execution and decoupled package import/file handling so non-GUI environments can still use the merge pipeline.
- Tightened runtime engine detection so unavailable Excel/LibreOffice backends are no longer advertised optimistically.
- Fixed merge failure propagation and source-file identity handling for duplicate filenames from different folders.
- Updated packaging/docs for cross-platform v2 distribution planning.
- Moved CI and packaging baselines to `Python 3.14 + JPype1 1.7.1 + OpenJDK 21`.
- Updated `build.yml`, `build-test.yml`, and the platform-specific build-test workflows to use Python 3.14, run dependency checks, and execute unit tests in non-JRE test lanes.
