# 백엔드 작업 가이드

이 문서는 백엔드 코드를 수정하거나 새 API를 추가할 때의 현재 경계를 요약합니다. 전체 구조는 [ARCHITECTURE.md](../ARCHITECTURE.md), 활성 API는 [API_SPEC.md](../API_SPEC.md)를 기준으로 합니다.

## 모듈 구조

```text
backend/
├── main.py                 FastAPI 생성, 인증, CORS, router 등록, dist mount
├── config/settings.py      프로젝트 기준 경로와 환경 변수
├── modules/                HTTP 도메인 경계
│   ├── ai_lab/
│   ├── backtest/
│   ├── indicators/
│   ├── journal/
│   ├── market/
│   ├── preset/
│   ├── stats/
│   ├── strategy_info/
│   ├── streak/
│   └── support_resistance/
├── strategy/               전략 특화 계산
│   ├── bb_mid/
│   ├── hybrid/
│   └── streak/
├── services/               공용 서비스 및 AI client adapter
├── utils/                  데이터, 캐시, 오류, 응답, 검증
└── tests/                  pytest
```

## API를 추가하는 순서

1. 새 도메인 또는 기존 `modules/<domain>/schemas.py`에 요청·응답 Pydantic 모델을 만듭니다.
2. `service.py`에 FastAPI에 의존하지 않는 use-case 함수를 둡니다.
3. `router.py`에서 입력을 검증하고 service만 호출합니다.
4. `backend/main.py`에 router를 등록합니다.
5. API client, frontend type, 화면, [API_SPEC.md](../API_SPEC.md), [PAGE_BACKEND_MAPPING.md](./PAGE_BACKEND_MAPPING.md)를 함께 갱신합니다.
6. `python3 scripts/check_route_imports.py`와 관련 테스트를 실행합니다.

## 데이터와 계산 경계

- 시장 데이터는 `utils/data_service.py`와 `utils/data_loader.py`를 사용합니다. 전략이나 라우터에서 Binance/CSV를 직접 다시 구현하지 않습니다.
- 재사용 가능한 수학 계산은 `core/`에 둡니다. HTTP, 파일 I/O, 네트워크 의존성을 넣지 않습니다.
- 전략별 판단은 `backend/strategy/`에 둡니다.
- `modules/indicators/`는 기술 지표를 HTTP 화면에 맞게 조합하는 도메인 서비스이며, 수식 자체는 `core/` 또는 `reverse_calc.py`에 둡니다.
- 진행 중 봉을 쓰지 않는 추세판단·VWAP·VPVR 경로에서는 반드시 마지막 kline을 제거합니다.

## 응답과 오류

- 성공 응답은 `{ "success": true, ... }` 형태를 유지합니다.
- `@handle_api_errors()`와 `response_builder.py`를 기존 패턴에 맞춰 사용합니다.
- 라우터에서 예외를 임의로 `pass` 처리하지 않습니다.
- 직렬화 가능한 Python primitive만 반환합니다. Pandas/NumPy scalar는 필요한 경우 `safe_float` 같은 기존 유틸로 변환합니다.

## 캐시와 파일 경로

- TTL 캐시는 `DataCache`를 사용합니다. 새 병렬 캐시 구현을 만들지 않습니다.
- 프리셋은 `PRESETS_FILE`을 통해 프로젝트 기준 `data/presets.json`에 저장하고 임시 파일 replace 방식으로 갱신합니다.
- 저널 경로는 `JOURNAL_DIR`, `JOURNAL_DB_PATH`, `JOURNAL_CSV_PATH` 환경 변수로 바꿀 수 있습니다.
- 캐시 TTL은 [CACHE_STRATEGY.md](./CACHE_STRATEGY.md)와 함께 관리합니다.

## 검증

```bash
python3 scripts/check_core_imports.py
python3 scripts/check_route_imports.py
backend/venv/bin/python -m pytest -q backend/tests
```

AI Lab은 개발 모드에서 인증을 우회하며 Python 도구는 완전한 권한 격리가 아닙니다. 외부 공개 전에는 해당 endpoint 비활성화 또는 컨테이너 격리가 필요합니다.
