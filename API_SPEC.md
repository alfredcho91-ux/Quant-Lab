# API Spec (Core Endpoints)

상세 예시/파라미터는 `API.md`를 참고하고, 이 문서는 핵심 계약만 요약합니다.

## Envelopes

- 성공 응답: `{ "success": true, "data": ... }`
- 실패 응답: `{ "success": false, "error": "..." }`

## 주요 엔드포인트

| Endpoint | Method | 설명 |
|---|---|---|
| `/api/streak-analysis` | `POST` | 연속 봉 패턴 분석 |
| `/api/bb-mid` | `POST` | BB 중단 터치 확률 통계 |
| `/api/combo-filter` | `POST` | 콤보 필터 백테스트 |
| `/api/trend-indicators` | `POST` | 추세판단 지표 조회 |
| `/api/hybrid-analysis` | `POST` | 하이브리드 전략 통계 |
| `/api/hybrid-backtest` | `POST` | 하이브리드 전략 백테스트 |
| `/api/hybrid-live` | `POST` | 하이브리드 전략 라이브 상태 |
| `/api/qx/profiles` | `GET` | Quant Lab 프로파일 목록 |
| `/api/qx/regime-snapshot` | `POST` | Quant Lab 레짐 스냅샷 |
| `/api/qx/conditional-prob` | `POST` | Quant Lab 조건부 확률 |
| `/api/qx/event-study` | `POST` | Quant Lab 이벤트 스터디 |
| `/api/qx/robustness` | `POST` | Quant Lab 강건성 비교 |

## 품질 게이트 (Quant Lab)

`/api/qx/*` 분석은 입력 데이터 품질 게이트를 통과하지 못하면 실패 응답을 반환합니다.

- 품질 메타 포함: `quality_report`, `quality_gate`, `reproducibility`
