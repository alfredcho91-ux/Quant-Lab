# Quant Lab Windows 데스크톱 앱

`Quant Lab.exe`를 실행하면 Chrome 탭 대신 독립된 앱 창이 열립니다.
Python·Node.js·개발 서버를 따로 실행할 필요가 없습니다. Microsoft Edge WebView2
Runtime은 필요합니다(현행 Windows에 보통 설치되어 있습니다). 없는 경우 Microsoft의
공식 WebView2 Runtime을 설치하세요: https://developer.microsoft.com/microsoft-edge/webview2/

## 실행

`Quant-Lab-Windows.zip` 전체를 압축 해제한 뒤 `Quant Lab/Quant Lab.exe`를 실행하세요.
실행 파일만 따로 옮기지 마세요. `_internal` 폴더도 필요합니다.
앱 창을 닫으면 그 앱의 로컬 서버도 종료됩니다. 이미 실행 중이면 기존 창을 엽니다.
미저장 편집/저장 중인 작업은 기존 화면의 이동 보호 정책으로 종료를 막습니다.
시세 조회에는 인터넷이 필요합니다. 외부 링크는 기본 브라우저로 열 수 있습니다.

로컬 HTTP 서버는 `127.0.0.1`에만 바인딩하며 기본 포트는 5182입니다.
사용 중이면 다음 빈 포트를 선택합니다. 기존 8000/5173 개발 서버와 독립적입니다.
실제 데이터와 설정은 `%APPDATA%\Quant Lab`에 저장하며 패키지 안에 사용자 DB,
API 키, `.env`, CSV 거래 기록을 포함하지 않습니다. 소스 실행의 `journal` 데이터는
자동으로 이동/복사하지 않습니다. 데스크톱 첫 실행의 별도 데이터 위치에 유의하세요.
기본 시세 캐시도 이 사용자 폴더의 `.cache`에 생성하며 설치 폴더를 수정하지 않습니다.

## 다시 빌드

Windows Python 3.11+, Node.js 24와 기존 백엔드/프런트 의존성을 준비합니다.

```powershell
backend\venv\Scripts\python.exe -m pip install -r packaging\requirements-build.txt
powershell -File packaging\build_windows_app.ps1
```

결과는 `Windows/Quant Lab/Quant Lab.exe`와 `Windows/Quant-Lab-Windows.zip`입니다.
기존 결과물이 있으면 덮어쓰지 않습니다. 새 `-OutputDirectory`를 지정하세요.
공유 배포용 코드 서명/MSIX/스토어 제출은 이 로컬 빌드와 별도이며 이 빌드는 서명되지 않습니다.
웹 서버용 `backend/requirements.txt`에는 데스크톱 빌드 의존성을 추가하지 않습니다.
