# 📡 API 명세 (API Specification)

> **참고**: 이 문서는 [README.md](./README.md)에서 분리된 상세 API 명세입니다.

---

# 📡 주요 API 엔드포인트

## API 데이터 계약 (Data Contract)

> **중요**: 프론트엔드-백엔드 연동 시 타입 불일치를 방지하기 위한 명세입니다.

### 표준 에러 응답 (Error Response Schema)

모든 API 엔드포인트는 에러 발생 시 다음 형식을 따릅니다:

```typescript
// 기본 에러 응답
{
  success: false;
  error: string;              // 에러 메시지 (필수)
  error_code?: string;        // 에러 코드 (선택, 향후 확장용)
  traceback?: string;         // 스택 트레이스 (선택, 개발 환경에서만 제공)
  details?: any;              // 추가 상세 정보 (선택)
}

// 예시 1: 일반 에러
{
  "success": false,
  "error": "Failed to load data from Binance API"
}

// 예시 2: 검증 에러
{
  "success": false,
  "error": "Invalid parameter: n_streak must be >= 1",
  "error_code": "VALIDATION_ERROR"
}

// 예시 3: 디버그용 (개발 환경)
{
  "success": false,
  "error": "Index out of range",
  "traceback": "Traceback (most recent call last):\n  File..."
}
```

**HTTP 상태 코드:**
- `200 OK`: 성공 또는 에러 모두 200 반환 (현재 구현)
- `400 Bad Request`: 잘못된 요청 파라미터 (향후 개선)
- `500 Internal Server Error`: 서버 내부 오류 (향후 개선)

> **참고**: 현재는 모든 응답이 HTTP 200으로 반환되며, `success` 필드로 성공/실패를 구분합니다. 향후 RESTful 표준에 맞춰 HTTP 상태 코드를 명확히 구분할 예정입니다.

### POST `/api/streak-analysis` - 연속 봉패턴 분석

**입력 (Request):**
```typescript
{
  coin: string;              // 예: "BTC", "ETH", "SOL", "XRP"
  interval: string;          // 예: "1d", "3d", "4h", "1h"
  n_streak: number;          // 연속 봉 개수 (1 이상 정수)
  direction: 'green' | 'red'; // 'green'=양봉, 'red'=음봉
  use_complex_pattern?: boolean;        // 기본값: false
  complex_pattern?: number[] | null;    // 예: [1,1,1,1,1,-1,-1] (5양-2음)
  rsi_threshold?: number;    // 기본값: 60.0
  max_retracement?: number;  // 기본값: 50.0
  use_csv?: boolean;         // 기본값: false
  timezone_offset?: number;  // 기본값: -5 (EST)
}
```

**출력 (Response):**
```typescript
{
  success: boolean;
  mode?: 'simple' | 'complex';
  total_cases: number;
  continuation_rate: number | null;
  reversal_rate: number | null;
  continuation_ci?: {
    ci_lower: number;
    ci_upper: number;
  } | null;
  c1_prediction?: {
    rate: number;
    ci_lower: number;
    ci_upper: number;
    p_value: number;
    is_significant: boolean;
  };
  c2_after_c1_green_rate: number | null;
  c2_after_c1_red_rate: number | null;
  comparative_report?: {
    pattern_total: number;
    success_count: number;
    failure_count: number;
    success_rate: number | null;
    success: { prev_rsi: number | null; prev_body_pct: number | null; ... };
    failure: { prev_rsi: number | null; prev_body_pct: number | null; ... };
  } | null;
  ny_trading_guide?: {
    low_window: string | null;
    avg_volatility: number | null;
    hourly_low_probability: Record<string, number>;
    hourly_high_probability: Record<string, number>;
  };
  complex_pattern_analysis?: {
    pattern: number[];
    total_matches: number;
    avg_score: number;
    rsi_by_interval?: Record<string, { rate: number; sample_size: number; ... }>;
    // ... 기타 필드
  } | null;
  coin: string;
  interval: string;
  n_streak: number;
  direction: string;
}
```

**에러 응답 (Error Response):**
```typescript
{
  success: false;
  error: string;              // 예: "Failed to load data", "Invalid pattern"
  traceback?: string;         // 개발 환경에서만 제공 (선택)
}
```

### POST `/api/weekly-pattern` - 주간 패턴 분석

**입력 (Request):**
```typescript
{
  coin: string;              // 예: "BTC", "ETH", "SOL", "XRP"
  interval: string;          // "1d"만 지원 (주간 분석)
  direction?: 'down' | 'up'; // 선택적: "down" (하락) 또는 "up" (상승), 없으면 임계값으로 자동 판단
  deep_drop_threshold: number; // 깊은 하락 임계값 (기본값: -0.05 = -5%)
  deep_rise_threshold: number; // 깊은 상승 임계값 (기본값: 0.05 = +5%)
  rsi_threshold: number;     // 과매도/과매수 임계값 (기본값: 40)
  use_csv?: boolean;         // 기본값: false
}
```

**주요 특징:**
- **자동 방향 판단**: `direction`이 없으면 `deep_drop_threshold`가 음수면 하락, `deep_rise_threshold`가 양수면 상승으로 자동 판단
- **하락 케이스**: 주 초반(월-화) 하락 후 주 후반(수-일) 반등 확률 분석
- **상승 케이스**: 주 초반(월-화) 상승 후 주 후반(수-일) 지속 확률 분석

**출력 (Response):**
```typescript
{
  success: boolean;
  coin: string;
  total_weeks: number;
  warnings?: string[];       // 데이터 품질 경고
  filters: {
    deep_drop_threshold: number;
    deep_rise_threshold?: number;  // 상승 케이스일 때만 포함
    rsi_threshold: number;
    rsi_period?: number;     // 기본값: 14
    atr_period?: number;     // 기본값: 14
    vol_period?: number;     // 기본값: 20
  };
  results: {
    baseline?: WeeklyPatternStats;    // 주 초반 하락/상승 케이스 (기준선)
    deep_drop?: WeeklyPatternStats;    // 깊은 하락 필터 (하락 케이스)
    deep_rise?: WeeklyPatternStats;    // 깊은 상승 필터 (상승 케이스)
    oversold?: WeeklyPatternStats;    // 과매도 필터 (하락 케이스)
    overbought?: WeeklyPatternStats;   // 과매수 필터 (상승 케이스)
    contra?: WeeklyPatternStats;       // 반전 케이스 (숏 전략)
  };
}

interface WeeklyPatternStats {
  title: string;
  description: string;
  sample_count: number;
  sample_size_warning?: string | null;  // N < 30일 때 경고
  period?: {
    start: string | null;
    end: string | null;
  };
  // Returns
  win_rate: number | null;  // 하락 케이스: 반등 확률, 상승 케이스: 지속 확률
  expected_return: number | null;
  median_return: number | null;
  volatility: number | null;
  confidence_interval?: {
    ci_lower: number | null;
    ci_upper: number | null;
    ci_width: number | null;
  };
  // Statistical Significance
  t_test?: {
    t_statistic: number | null;
    p_value: number | null;
    is_significant: boolean;
  };
  // Risk Metrics
  profit_factor: number | null;
  sharpe_ratio: number | null;
  max_drawdown?: {
    max_drawdown: number | null;
    max_drawdown_pct: number | null;
  };
  max_consecutive_loss: number;
  // Additional
  positive_sum: number | null;
  negative_sum: number | null;
}
```

**에러 응답 (Error Response):**
```typescript
{
  success: false;
  error: string;              // 예: "No weekly patterns found", "Data validation failed"
  error_type?: string;        // 예: "DataValidationError", "InsufficientDataError"
  warnings?: string[];        // 데이터 품질 경고
  traceback?: string;         // 개발 환경에서만 제공 (선택)
}
```

**주요 기능:**
- 주 초반(월-화) 하락 후 주 후반(수-일) 반등 패턴 검증
- 통계적 유의성 검증 (t-test, 신뢰구간)
- 리스크 지표 제공 (Sharpe Ratio, MDD, 연속 손실)
- 데이터 품질 검증 및 경고
- Look-ahead Bias 방지

### POST `/api/ma-cross` - MA 크로스 통계

**입력:**
```typescript
{
  coin: string;
  interval: string;          // "15m", "30m", "1h", "2h", "4h", "1d", "3d", "1w"
  cross_type: 'golden' | 'dead';
  pairs: number[][];         // 예: [[5, 20], [20, 60]]
  horizons: number[];        // 예: [1, 2, 3, 4, 5]
  up_thresholds: number[];   // 백분율, 예: [0.5, 1.0, 2.0]
  down_thresholds: number[]; // 백분율, 예: [0.5, 1.0, 2.0]
  use_csv?: boolean;
}
```

**출력:**
```typescript
{
  success: boolean;
  data: Array<{
    pair: string;           // "5/20"
    horizon: number;
    type: 'up' | 'down';
    threshold_value: number;
    threshold_label: string;
    probability: number;    // 0-100
    signals: number;
  }>;
  cross_type: string;
  available_pairs: string[];
  horizons: number[];
}
```

**에러 응답 (Error Response):**
```typescript
{
  success: false;
  error: string;              // 예: "Invalid MA pair", "Data load failed"
}
```

### POST `/api/bb-mid` - 볼밴 중단 회귀 통계

**입력:**
```typescript
{
  coin: string;
  intervals: string[];      // 예: ["1h", "4h", "1d", "3d", "1w"]
  start_side: 'lower' | 'upper';
  max_bars: number;         // 기본값: 7
  rsi_min: number;          // 기본값: 40
  rsi_max: number;          // 기본값: 60
  regime?: 'above_sma200' | 'below_sma200' | null;
  use_csv?: boolean;
}
```

**출력:**
```typescript
{
  success: boolean;
  data: Array<{
    interval: string;
    events: number;
    success: number;
    success_rate: number | null;
  }>;
  excursions: Record<string, {
    avg_mfe: number;
    avg_mae: number;
    avg_end: number;
  }>;
  quartile_stats: Record<string, {
    Q1: number;
    Q2: number;
    Q3: number;
    Q4: number;
    Total: number;
  }>;
  start_side: string;
}
```

**에러 응답 (Error Response):**
```typescript
{
  success: false;
  error: string;              // 예: "No matching events found", "RSI filter error"
}
```

## 전체 API 엔드포인트 목록

| Method | Endpoint | 설명 | 입력/출력 타입 |
|--------|----------|------|----------------|
| GET | `/api/market/prices` | 시장 가격 조회 | JSON |
| GET | `/api/market/fear-greed` | Fear & Greed Index | JSON |
| GET | `/api/market/timeframes/{coin}` | 사용 가능한 타임프레임 | JSON |
| GET | `/api/market/ohlcv/{coin}/{interval}` | OHLCV 데이터 | JSON |
| GET | `/api/strategies` | 전략 목록 | JSON |
| GET | `/api/strategy-info/{id}` | 전략 설명 | JSON |
| POST | `/api/backtest` | 백테스트 실행 | BacktestParams → BacktestResult |
| POST | `/api/backtest-advanced` | 고급 백테스트 | AdvancedBacktestParams → AdvancedBacktestResult |
| POST | `/api/streak-analysis` | 연속 봉패턴 분석 | StreakAnalysisParams → StreakAnalysisResult |
| POST | `/api/weekly-pattern` | 주간 패턴 분석 | WeeklyPatternParams → WeeklyPatternResult |
| POST | `/api/ma-cross` | MA 크로스 통계 | MaCrossParams → MaCrossResult |
| POST | `/api/bb-mid` | 볼밴 중단 회귀 통계 | BBMidParams → BBMidResult |
| GET | `/api/support-resistance/{coin}/{interval}` | 지지/저항 레벨 | JSON |
| POST | `/api/scanner` | 전략 스캐너 | ScannerParams → ScannerResult |
| POST | `/api/pattern-scanner` | 패턴 스캐너 | PatternScanParams → PatternScanResult |
| GET | `/api/presets` | 프리셋 목록 | JSON |
| POST | `/api/presets` | 프리셋 저장 | PresetSaveRequest → JSON |

> **참고**: 상세한 타입 정의는 `backend/models/request.py` (Pydantic) 및 `frontend/src/types/index.ts` (TypeScript) 참조
