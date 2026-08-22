# Cloudflare Pages 준비

이 문서는 Quant-Lab의 React/Vite 프론트엔드만 Cloudflare Pages에 연결하기 위한 설정입니다. `journal-free/` 무료 배포용 프로그램은 이번 준비 범위에 포함하지 않습니다.

## Pages 설정

GitHub 저장소를 연결한 뒤 다음 값을 사용합니다.

| 항목 | 값 |
| --- | --- |
| Framework preset | React (Vite) 또는 Vite |
| Root directory | `frontend` |
| Build command | `npm run build` |
| Build output directory | `dist` |
| 배포 브랜치 | `main` |

`frontend/public/_redirects`가 빌드 결과에 복사되므로 `/journal`, `/trade-analysis` 같은 SPA 경로를 새로고침해도 Pages에서 `index.html`로 처리됩니다. GitHub 연동을 사용하므로 별도의 `wrangler.toml`이나 Pages 배포 명령은 필요하지 않습니다.

## Pages 환경변수

아래 값은 프론트엔드에 포함되는 **공개 설정**입니다. API Key, API Secret, 암호화 키, Basic Auth 비밀번호를 넣으면 안 됩니다.

| 변수 | 예시 | 용도 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `https://api.example.com/api` | 별도로 운영하는 FastAPI 백엔드 주소 |
| `VITE_WINDOWS_RELEASE_URL` | `https://github.com/alfredcho91-ux/Quant-Lab/releases/latest` | 사이드바 Windows 다운로드 버튼 주소 |

로컬에서는 `VITE_API_BASE_URL`을 지정하지 않아도 `/api`가 사용되고 Vite 개발 프록시가 `localhost:8000`으로 연결합니다. Pages에서는 정적 파일만 제공되므로 API 기능을 사용하려면 백엔드가 외부에서 HTTPS로 접근 가능해야 합니다.

## 백엔드 배포 시 별도 설정

이 값들은 Cloudflare Pages 환경변수가 아니라 백엔드 호스팅 환경의 Secret으로 설정해야 합니다.

- `APP_ENV=production`
- `CORS_ORIGINS=https://<pages-domain>`
- `DEMO_USERNAME`, `DEMO_PASSWORD` 또는 백엔드의 별도 인증 설정
- `CREDENTIAL_STORAGE`, `CREDENTIAL_MASTER_KEY`
- `DEEPCOIN_API_BASE_URL` 및 거래소 연동 설정

Deepcoin API Key, Secret, Passphrase와 `CREDENTIAL_MASTER_KEY`는 Pages 환경변수나 GitHub 저장소에 넣지 않습니다. 사용자가 앱의 API 연결 창에서 입력한 값은 프론트 빌드에 포함되지 않고 백엔드의 credential 저장 경로로 전달됩니다. 백엔드 인증정보를 프론트에 넣는 방식은 지원하지 않습니다.

## 배포 전 확인

```bash
cd frontend
npm run build
test -f dist/_redirects
```

Cloudflare 계정 연결, 실제 Pages 생성, DNS 설정, 백엔드 호스팅은 이 저장소 준비 단계에서 수행하지 않습니다.
