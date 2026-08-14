# ConsultParser2 Release Notes

## 🚀 Version v2.5.0.Build.2 (배포 일시: 2026-08-14 19:25)

### 🐛 긴급 패치: `QComboBox` 누락 NameError 소거 및 정렬 순서 필터 완결

1. **[Fix] `NameError: name 'QComboBox' is not defined` 버그 즉시 수정**
   - `ui/tab_process.py` 상단 PyQt5 import 구문에 `QComboBox` 명시적 수록으로 앱 시작 시 튕김 오류 완벽 해결.

2. **[Feat] 2가지 정렬 순서 (`⚖️ 파일 용량 오름차순` & `⏰ 타임스탬프 오름차순`) 정상 가동 보장**
   - 0B 및 저용량 파일 최우선 순서 배치로 완료율 선제 달성 기능 100% 가동 확인.
