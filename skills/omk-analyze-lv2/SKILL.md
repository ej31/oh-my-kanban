---
name: omk-analyze-lv2
description: "모듈 구조 분석 - 모듈별 책임, 핵심 클래스/함수, 의존성 방향"
---

# omk-analyze-lv2: 모듈 구조 분석

모듈별 책임과 의존성 관계를 분석합니다.

## 목적

- 모듈별 책임 범위 파악
- 핵심 클래스/함수 식별
- 의존성 방향 (어떤 모듈이 어떤 모듈을 import하는지)
- 외부 라이브러리 의존성 목록

## 추천 모델

**Sonnet** - 코드 이해에 최적화

## 언제 사용하나요?

- lv1 분석 완료 후 코드 수정 전 컨텍스트를 확보할 때
- 특정 기능이 어디에 구현되어 있는지 찾을 때
- 모듈 간 의존성을 이해하고 싶을 때

## 수행 지침

1. **모듈 목록 파악**
   - 소스 디렉토리의 패키지/모듈 목록 나열
   - 각 모듈의 `__init__.py` 또는 `index.ts` 읽기

2. **핵심 클래스/함수 식별**
   ```bash
   # Python 예시
   grep -rn "^class \|^def " src/ | head -50
   # TypeScript 예시
   grep -rn "export class\|export function\|export const" src/ | head -50
   ```

3. **의존성 방향 분석**
   ```bash
   # 내부 import 관계 파악
   grep -rn "from \.\|import \." src/ | head -50
   ```

4. **외부 의존성 확인**
   - 의존성 파일(requirements.txt, package.json 등)에서 외부 라이브러리 목록

5. **출력 형식**
   ```
   === 모듈 구조 분석 ===

   [모듈: {이름}]
   책임: {한줄 설명}
   핵심 클래스: {Class1, Class2}
   핵심 함수: {func1, func2}
   의존: {다른 모듈 목록}
   파일 수: {N}개

   [의존성 방향]
   {모듈A} → {모듈B} (이유)
   {모듈B} → {모듈C} (이유)
   ```
