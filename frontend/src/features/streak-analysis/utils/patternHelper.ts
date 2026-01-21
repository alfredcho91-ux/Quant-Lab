/**
 * 패턴 생성 및 관련 유틸리티 함수
 */

export type PatternDirection = 'green' | 'red';
export type PatternCondition = {
  count: number;
  direction: PatternDirection;
};

/**
 * 복합 패턴 생성
 * @param condition1 1차 조건
 * @param condition2 2차 조건
 * @returns 패턴 배열 (1: 양봉, -1: 음봉) 또는 null
 */
export function generatePattern(
  useComplexPattern: boolean,
  condition1: PatternCondition,
  condition2?: PatternCondition
): number[] | null {
  if (!useComplexPattern) {
    return null;
  }

  if (!condition2) {
    return null;
  }

  const pattern = [
    ...Array(condition1.count).fill(condition1.direction === 'green' ? 1 : -1),
    ...Array(condition2.count).fill(condition2.direction === 'green' ? 1 : -1),
  ];

  return pattern;
}

/**
 * 패턴 미리보기 텍스트 생성
 * @param useComplexPattern 복합 패턴 사용 여부
 * @param condition1 1차 조건
 * @param condition2 2차 조건
 * @param isKo 한국어 여부
 * @returns 패턴 미리보기 텍스트
 */
export function getPatternPreview(
  useComplexPattern: boolean,
  condition1: PatternCondition,
  condition2?: PatternCondition,
  isKo: boolean = false
): string {
  if (!useComplexPattern) {
    return `${condition1.count}${isKo ? '연속' : ' consecutive'} ${
      condition1.direction === 'green' ? (isKo ? '양봉' : 'Green') : (isKo ? '음봉' : 'Red')
    }`;
  }

  if (!condition2) {
    return '';
  }

  const pattern1 = Array(condition1.count)
    .fill(condition1.direction === 'green' ? '↑' : '↓')
    .join('');
  const pattern2 = Array(condition2.count)
    .fill(condition2.direction === 'green' ? '↑' : '↓')
    .join('');

  return `${pattern1}${pattern2}`;
}
