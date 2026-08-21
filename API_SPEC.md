# Quant-Lab API Specification

현재 API의 기준 구현은 `backend/main.py`와 각 `backend/modules/*/router.py`, `schemas.py`입니다. 실행 중인 상세 스키마와 예시는 `http://localhost:8000/docs`에서 OpenAPI로 확인합니다.

## 공통 규칙

- 기본 성공 형식: `{ "success": true, ... }`
- 오류는 FastAPI HTTP 상태 코드와 표준 오류 payload를 사용합니다.
- `coin`은 `BTC`, `ETH`, `SOL` 같은 base symbol을 사용합니다. 내부 데이터 요청은 `USDT` 페어로 정규화합니다.
- `use_csv=false`면 Binance Spot API를 사용합니다. 지원되는 화면은 로컬 `binance_klines/` CSV를 선택할 수 있습니다.
- 개발 환경은 Basic Auth를 생략하고, production은 HTTP Basic Auth를 요구합니다.

## 시장 데이터

| Method | Endpoint | 주요 입력 | 설명 |
| --- | --- | --- | --- |
| GET | `/api/market/prices` | - | BTC/ETH/SOL 현재 가격 |
| GET | `/api/market/fear-greed` | - | 공포·탐욕 지수 |
| GET | `/api/timeframes/{coin}` | path `coin` | Binance/CSV에서 가능한 시간대 |
| GET | `/api/ohlcv/{coin}/{interval}` | query `use_csv`, `limit` (1-10000), `end_time` (선택, ms) | 정규화 OHLCV. `end_time` 지정 시 해당 시점 기준 Binance Spot 과거 캔들 |

## 지표와 추세

| Method | Endpoint | 주요 입력 | 설명 |
| --- | --- | --- | --- |
| POST | `/api/trend-indicators` | `coin`, `interval`, `use_csv` | 직전 확정봉 기준 추세·모멘텀 지표와 최근 시계열 |
| GET | `/api/indicators/projection` | query `coin`, `interval` | 현재 RSI, RSI 30/70 역산 가격, 기간/롤링 VWAP |
| GET | `/api/indicators/vpvr/{coin}/{interval}` | query `candles`, `bin_count`, `price_range` | Binance kline 기반 VPVR |
| GET | `/api/indicators/vpvr-source/{coin}/{interval}` | query `candles` | VPVR 검증용 정규화 Binance kline |
| GET | `/api/indicators/trade-report/{coin}/{interval}` | query `limit` (기본 300), `end_time`, `as_of`, `profile_candles` (기본 300), `bin_count` | 과거 거래 캔들·모멘텀 시계열과 `as_of` 직전 확정봉 기준 VPVR/VWAP |
| GET | `/api/support-resistance/{coin}/{interval}` | query `lookback`, `tolerance_pct`, `min_touches`, `show_pivots`, `htf_option` | 지지·저항 레벨 |

`/api/indicators/vpvr`의 기본값은 `bin_count=24`, `price_range=10000`, `candles`는 시간대별 기본 기간입니다. 응답의 `allocation_method`는 항상 `candle_range_proportional`이며, quote volume을 고가-저가에 비례 배분했음을 뜻합니다.

거래 리포트 API는 표시 구간 뒤에 붙는 종료 후 캔들을 지표 기준값에 포함하지 않습니다. `vpvr`, 기간 VWAP, 앵커 VWAP, 200봉 VWAP, `latest`는 모두 `as_of`보다 먼저 종료된 확정봉만 사용하며, RSI/MACD/Stoch RSI/3 Slow Stochastic 시계열은 화면 캔들 구간과 함께 반환합니다.

## 전략과 백테스트

| Method | Endpoint | 주요 입력 | 설명 |
| --- | --- | --- | --- |
| POST | `/api/backtest` | 백테스트 파라미터 | 기본 전략 백테스트 |
| POST | `/api/bb-mid` | `coin`, `intervals`, `start_side`, `max_bars`, `regime`, `use_csv` | BB Mid 통계 |
| POST | `/api/hybrid-analysis` | `coin`, `interval`, `strategies` | 하이브리드 전략 통계 |
| POST | `/api/hybrid-backtest` | `coin`, `interval`, `strategy`, `tp`, `sl`, `max_hold` | 하이브리드 백테스트 |
| POST | `/api/hybrid-live` | `coin`, `interval`, `strategies` | 하이브리드 최신 확정봉 상태 |
| GET | `/api/strategies` | - | 전략 목록 |
| GET | `/api/strategy-info/{strategy_id}` | query `lang`, RSI/SMA 파라미터 | 전략 설명과 계산 정보 |

## 연속봉, AI, 기록

| Method | Endpoint | 주요 입력 | 설명 |
| --- | --- | --- | --- |
| POST | `/api/streak-analysis` | 연속봉/복합 패턴 파라미터 | C1/C2 확률 분석 |
| GET | `/api/streak-cache-stats` | - | 연속봉 캐시 통계 |
| POST | `/api/streak-cache-clear` | - | 연속봉 캐시 초기화 |
| POST | `/api/ai/research` | `prompt`, `provider`, `model`, `temperature`, `history` | AI 리서치 워크플로 |
| POST | `/api/ai/analyst` | `prompt`, `coin`, `interval`, `model` | AI 분석가 응답 |
| GET | `/api/journal` | - | 매매일지 목록 |
| GET | `/api/journal/current-market` | query `coin` | 선택 코인의 현재 완료봉 기준 1H/2H/4H/1D 지표 스냅샷과 Weekly/Daily/4H 추세·Regime. 과거 진입 유사도 비교용이며 시간 단위 캐시 사용 |
| GET | `/api/journal/excursions` | query `start_time`, `end_time` | 종료 거래별 15분봉 MFE/MAE 및 종료 품질 분류 |
| GET | `/api/journal/quality-analysis` | query `start_time`, `end_time` | 진입 시점 Weekly/Daily/4H Regime, 분포 기반 진입·청산 품질, 전체 및 LONG/SHORT별 4H 추가 홀딩·보조지표 가상 청산 비교 |
| GET | `/api/journal/stop-loss-analysis` | query `start_time`, `end_time` | Deepcoin 확정 SL 체결과 종료 포지션을 연결하고 손절 후 최대 3개 완료 4H 봉을 분석. 반대 방향 1% 이상은 Good Stop, 여기에 반대 방향 2R 이상과 4H 추세 전환이 동반되면 Good Stop + Reversal로 분류 |
| GET | `/api/journal/sl-tp-analysis` | 기간, `sl_min/max/step`, `tp_min/max/step` | 종료 거래의 5분봉 경로에서 SL/TP 최초 도달을 재생하고 최대 800개 조합의 기대값·PF·복리 수익·Drawdown, 70/30 검증 추천 범위를 반환 |
| DELETE | `/api/journal/{entry_id}` | path `entry_id` | 매매일지 삭제 |
| GET | `/api/deepcoin/status` | - | 서버의 Deepcoin 읽기 전용 자격 증명 설정 여부 |
| GET | `/api/deepcoin/trade-markers` | query `symbol`, `direction`, `entry_time`, `exit_time`, `entry_price` | 종료 거래 구간의 실제 발동 TP 주문을 `TP1`, `TP2`로 반환 |
| POST | `/api/deepcoin/sync` | `inst_type` (`SWAP`/`SPOT`), `lookback_days` (1-90) | Deepcoin 체결을 중복 없이 저널에 동기화하고 종료 포지션의 레버리지·투자금과 지표 스냅샷 저장 |
| GET | `/api/presets` | - | 프리셋 목록 |
| POST | `/api/presets` | 이름, 코인, 시간대, 전략, 파라미터 | 프리셋 저장 |
| DELETE | `/api/presets/{name}` | path `name` | 프리셋 삭제 |

## 호환성과 주의

- `/ai-backtest-builder`는 프런트엔드만의 레거시 경로이며 AI Lab Builder 탭으로 이동합니다.
- 문서에 없는 `/api/qx/*`, `/api/scanner*`, 고급 백테스트 전용 API는 현재 활성 계약이 아닙니다.
- 외부 공개 시 AI의 Python 실행 도구는 별도 컨테이너 또는 비활성화 정책이 필요합니다.
- Deepcoin 동기화는 읽기 전용 fills와 positions-history를 사용합니다. 종료 포지션의 `lever`와 총손익·가격 변동을 이용해 거래별 투입 증거금을 저장하며, 투자금 대비 순수익률은 수수료·펀딩을 반영한 순손익으로 계산합니다. 거래 복기에서는 읽기 전용 trigger-orders-history를 추가로 조회하며, 주문 생성·수정·취소 API는 호출하지 않습니다. 체결당 지표는 Binance Spot OHLCV의 체결 직전 확정봉 기준이므로 Deepcoin SWAP 가격과 차이가 날 수 있습니다.
