"""
제공된 코드 vs 현재 프로젝트 코드 비교 테스트
"""
import pandas as pd
import numpy as np

def analyze_7th_day_probability(file_path):
    """제공된 코드 (원본)"""
    df = pd.read_csv(file_path)
    def convert_time(ts):
        return pd.to_datetime(ts, unit='us') if ts > 1e14 else pd.to_datetime(ts, unit='ms')
    df['open_time_dt'] = df['open_time'].apply(convert_time)
    
    df['is_red'] = df['close'] < df['open']
    
    # 6연속 음봉 식별 (당일 제외 과거 6일 기준)
    df['prev_red_6_sum'] = df['is_red'].shift(1).rolling(window=6).sum()
    df['is_after_6_red'] = df['prev_red_6_sum'] == 6
    
    target_days = df[df['is_after_6_red']].copy()
    
    total_occurrences = len(target_days)
    red_7th_count = target_days['is_red'].sum()
    
    prob_red = (red_7th_count / total_occurrences * 100) if total_occurrences > 0 else 0
    avg_return = (target_days['close'] / target_days['open'] - 1).mean()
    
    print(f"\n=== 제공된 코드 결과 ===")
    print(f"Total 6-Red Streaks (다음 날): {total_occurrences}")
    print(f"7th Day Red Count: {red_7th_count}")
    print(f"Probability of 7th Red: {prob_red:.2f}%")
    print(f"7th Day Avg Return: {avg_return * 100:.4f}%")
    
    return target_days, df


def analyze_current_project_logic(df):
    """현재 프로젝트 코드 로직"""
    n = 6
    direction = "red"
    
    # target_bit 설정 (음봉인 경우)
    df['is_red'] = df['close'] < df['open']
    df['target_bit'] = df['is_red']
    
    # 패턴 매칭 (현재 프로젝트 방식)
    condition = pd.Series([True] * len(df), index=df.index)
    for i in range(1, n + 1):
        condition &= (df['target_bit'].shift(i) == True)
    
    target_cases = df[condition].copy()
    total_cases = len(target_cases)
    
    # C1 분석 (다음 봉)
    df['next_is_red'] = df['is_red'].shift(-1)
    c1_red_mask = df.loc[target_cases.index, 'next_is_red'] == True
    continuation_count = int(c1_red_mask.sum())
    
    continuation_rate = float(continuation_count / total_cases * 100) if total_cases > 0 else 0
    
    print(f"\n=== 현재 프로젝트 코드 결과 ===")
    print(f"Total 6-Red Streaks (완성 시점): {total_cases}")
    print(f"C1 Red Count (continuation): {continuation_count}")
    print(f"Continuation Rate: {continuation_rate:.2f}%")
    
    return target_cases, df


def compare_timing(df, provided_target, current_target):
    """시점 비교"""
    print(f"\n=== 시점 비교 ===")
    
    # 제공된 코드의 타겟 인덱스
    provided_indices = set(provided_target.index)
    current_indices = set(current_target.index)
    
    print(f"제공된 코드 타겟 개수: {len(provided_indices)}")
    print(f"현재 프로젝트 타겟 개수: {len(current_indices)}")
    
    # 겹치는 인덱스
    overlap = provided_indices & current_indices
    print(f"겹치는 인덱스: {len(overlap)}")
    
    # 제공된 코드에만 있는 인덱스 (다음 날)
    only_provided = provided_indices - current_indices
    print(f"제공된 코드에만 있는 인덱스: {len(only_provided)}")
    
    # 현재 프로젝트에만 있는 인덱스
    only_current = current_indices - provided_indices
    print(f"현재 프로젝트에만 있는 인덱스: {len(only_current)}")
    
    # 샘플 출력
    if len(only_provided) > 0:
        print(f"\n제공된 코드에만 있는 샘플 (다음 날):")
        sample = df.loc[list(only_provided)[:3]]
        for idx in sample.index:
            print(f"  인덱스 {idx}: {sample.loc[idx, 'open_time_dt']}")
            # 이전 6일 확인
            prev_6 = df.loc[max(0, idx-6):idx-1] if idx > 0 else pd.DataFrame()
            if len(prev_6) > 0:
                print(f"    이전 6일 음봉: {prev_6['is_red'].sum()}/6")
    
    if len(only_current) > 0:
        print(f"\n현재 프로젝트에만 있는 샘플 (완성 시점):")
        sample = df.loc[list(only_current)[:3]]
        for idx in sample.index:
            print(f"  인덱스 {idx}: {sample.loc[idx, 'open_time_dt']}")
            # 이전 6일 확인
            prev_6 = df.loc[max(0, idx-6):idx-1] if idx > 0 else pd.DataFrame()
            if len(prev_6) > 0:
                print(f"    이전 6일 음봉: {prev_6['is_red'].sum()}/6")


if __name__ == "__main__":
    file_path = 'BTCUSDT-1d-merged.csv'
    
    try:
        # 제공된 코드 실행
        provided_target, df1 = analyze_7th_day_probability(file_path)
        
        # 현재 프로젝트 코드 실행 (같은 데이터프레임 사용)
        current_target, df2 = analyze_current_project_logic(df1.copy())
        
        # 시점 비교
        compare_timing(df1, provided_target, current_target)
        
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
        print("CSV 파일 경로를 확인해주세요.")
    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()
