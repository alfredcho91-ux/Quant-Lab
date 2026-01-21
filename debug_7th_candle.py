"""
7번째 봉 확률 계산 비교 및 디버깅
"""
import pandas as pd
import numpy as np

def create_test_data():
    """테스트용 데이터 생성"""
    # 시나리오: 7연속 음봉 후 양봉
    data = {
        'open_time': [1000 + i * 86400000 for i in range(10)],
        'open': [100.0] * 10,
        'close': [99.0, 99.0, 99.0, 99.0, 99.0, 99.0, 99.0, 101.0, 99.0, 101.0],  # R R R R R R R G R G
        'high': [100.5] * 10,
        'low': [98.5] * 10,
        'volume': [1000.0] * 10,
    }
    df = pd.DataFrame(data)
    df['is_red'] = df['close'] < df['open']
    df['is_green'] = df['close'] > df['open']
    return df


def method_provided_code(df):
    """제공된 코드 방식"""
    print("\n=== 제공된 코드 방식 ===")
    
    # 6연속 음봉 식별
    df['prev_red_6_sum'] = df['is_red'].shift(1).rolling(window=6).sum()
    df['is_after_6_red'] = df['prev_red_6_sum'] == 6
    
    print("인덱스별 prev_red_6_sum:")
    for idx in range(len(df)):
        print(f"  인덱스 {idx}: prev_red_6_sum={df.loc[idx, 'prev_red_6_sum']:.0f}, "
              f"is_after_6_red={df.loc[idx, 'is_after_6_red']}, "
              f"봉={df.loc[idx, 'is_red']}")
    
    target_days = df[df['is_after_6_red']].copy()
    print(f"\n타겟 인덱스: {target_days.index.tolist()}")
    
    if len(target_days) > 0:
        total = len(target_days)
        red_7th = target_days['is_red'].sum()
        prob = (red_7th / total * 100) if total > 0 else 0
        print(f"총 케이스: {total}")
        print(f"7번째 봉이 음봉인 케이스: {red_7th}")
        print(f"7번째 봉이 음봉일 확률: {prob:.2f}%")
        
        # 각 타겟의 이전 6일 확인
        print("\n각 타겟의 이전 6일 상세:")
        for idx in target_days.index:
            prev_6 = df.loc[max(0, idx-6):idx-1] if idx > 0 else pd.DataFrame()
            print(f"  인덱스 {idx} (타겟):")
            if len(prev_6) > 0:
                print(f"    이전 6일: {prev_6['is_red'].tolist()}")
                print(f"    음봉 합계: {prev_6['is_red'].sum()}")
            print(f"    현재 봉 (7번째): {'R' if df.loc[idx, 'is_red'] else 'G'}")
    
    return target_days


def method_current_project(df):
    """현재 프로젝트 방식"""
    print("\n=== 현재 프로젝트 방식 ===")
    
    n = 6
    df['target_bit'] = df['is_red']
    
    # 패턴 매칭
    condition = pd.Series([True] * len(df), index=df.index)
    for i in range(1, n + 1):
        condition &= (df['target_bit'].shift(i) == True)
        print(f"shift({i}) 후 조건 만족 개수: {condition.sum()}")
    
    target_cases = df[condition].copy()
    print(f"\n타겟 인덱스: {target_cases.index.tolist()}")
    
    if len(target_cases) > 0:
        # C1 분석 (다음 봉)
        df['next_is_red'] = df['is_red'].shift(-1)
        c1_red_mask = df.loc[target_cases.index, 'next_is_red'] == True
        
        total = len(target_cases)
        red_c1 = int(c1_red_mask.sum())
        prob = (red_c1 / total * 100) if total > 0 else 0
        
        print(f"총 케이스: {total}")
        print(f"C1이 음봉인 케이스: {red_c1}")
        print(f"C1이 음봉일 확률: {prob:.2f}%")
        
        # 각 타겟의 이전 6일 확인
        print("\n각 타겟의 이전 6일 상세:")
        for idx in target_cases.index:
            prev_6 = df.loc[max(0, idx-6):idx-1] if idx > 0 else pd.DataFrame()
            print(f"  인덱스 {idx} (타겟):")
            if len(prev_6) > 0:
                print(f"    이전 6일: {prev_6['is_red'].tolist()}")
                print(f"    음봉 합계: {prev_6['is_red'].sum()}")
            print(f"    현재 봉: {'R' if df.loc[idx, 'is_red'] else 'G'}")
            if idx + 1 < len(df):
                print(f"    다음 봉 (C1): {'R' if df.loc[idx + 1, 'is_red'] else 'G'}")
    
    return target_cases


def compare_results(df, provided_target, current_target):
    """결과 비교"""
    print("\n=== 결과 비교 ===")
    
    print(f"제공된 코드 타겟 개수: {len(provided_target)}")
    print(f"현재 프로젝트 타겟 개수: {len(current_target)}")
    
    provided_indices = set(provided_target.index)
    current_indices = set(current_target.index)
    
    print(f"\n제공된 코드 타겟 인덱스: {sorted(provided_indices)}")
    print(f"현재 프로젝트 타겟 인덱스: {sorted(current_indices)}")
    
    if provided_indices == current_indices:
        print("✅ 타겟 인덱스가 동일합니다!")
        
        # 7번째 봉 확률 비교
        provided_7th_red = provided_target['is_red'].sum()
        provided_total = len(provided_target)
        provided_prob = (provided_7th_red / provided_total * 100) if provided_total > 0 else 0
        
        current_c1_red = df.loc[current_target.index, 'is_red'].shift(-1).sum()
        current_total = len(current_target)
        current_prob = (current_c1_red / current_total * 100) if current_total > 0 else 0
        
        print(f"\n제공된 코드 - 7번째 봉이 음봉일 확률: {provided_prob:.2f}%")
        print(f"현재 프로젝트 - C1이 음봉일 확률: {current_prob:.2f}%")
        
        if abs(provided_prob - current_prob) < 0.01:
            print("✅ 확률이 동일합니다!")
        else:
            print(f"❌ 확률이 다릅니다! 차이: {abs(provided_prob - current_prob):.2f}%")
            
            # 상세 비교
            print("\n상세 비교:")
            for idx in provided_indices:
                provided_7th = df.loc[idx, 'is_red']
                if idx + 1 < len(df):
                    current_c1 = df.loc[idx + 1, 'is_red']
                    print(f"  인덱스 {idx}: 제공된 코드 7번째={provided_7th}, "
                          f"현재 프로젝트 C1={current_c1}, "
                          f"일치={provided_7th == current_c1}")
    else:
        print("❌ 타겟 인덱스가 다릅니다!")
        print(f"제공된 코드에만 있는 인덱스: {sorted(provided_indices - current_indices)}")
        print(f"현재 프로젝트에만 있는 인덱스: {sorted(current_indices - provided_indices)}")


if __name__ == "__main__":
    df = create_test_data()
    
    print("=== 테스트 데이터 ===")
    print(df[['open_time', 'open', 'close', 'is_red']].to_string())
    
    provided_target = method_provided_code(df.copy())
    current_target = method_current_project(df.copy())
    
    compare_results(df, provided_target, current_target)
