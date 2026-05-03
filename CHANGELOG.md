# Changelog

## 2.0.0
- Added merge-engine detection and selection for standard, Microsoft Excel, and LibreOffice flows.
- Added a working LibreOffice/PyUNO merge engine, JPype/Apache POI runtime scaffolding, and direct-update preparation flows.
- Reworked settings storage to remove `secret.key` and migrate passwords to base64 encoding.
- Updated packaging/docs for cross-platform v2 distribution planning.
- Verified the Apache POI fallback on `Python 3.13 + JPype1 1.6.0 + OpenJDK 17/21` and pinned CI/dependencies away from the crashing `JPype1 1.7.0` combination.
- Added a manual `build-test.yml` workflow that produces all 8 test artifacts without publishing a release.
