---
name: omk-analyze-lv1
description: "빠른 프로젝트 개요 분석 - 파일 구조, 언어/프레임워크, 진입점 파악"
---

# omk-analyze-lv1: 빠른 프로젝트 개요

프로젝트의 전체 윤곽을 5분 안에 파악합니다.

## 목적

- 파일/디렉토리 트리 구조 파악
- 사용 언어 및 프레임워크 감지
- 진입점(main, CLI entrypoint 등) 파악
- 프로젝트 메타데이터 확인 (package.json, pyproject.toml 등)

## 추천 모델

**Haiku** - 빠른 탐색에 최적화

## 언제 사용하나요?

- 새 프로젝트에 처음 접근할 때
- 5분 안에 전체 윤곽을 파악하고 싶을 때
- 코드를 수정하기 전 기본 구조를 이해하고 싶을 때

## 수행 지침

1. **프로젝트 루트 탐색**
   ```bash
   ls -la
   find . -maxdepth 2 -type f -name "*.json" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" | head -20
   ```

2. **설정 파일 읽기** - 다음 파일이 있으면 읽어서 프로젝트 메타데이터를 파악합니다
   - `package.json` (Node.js)
   - `pyproject.toml` / `setup.py` (Python)
   - `Cargo.toml` (Rust)
   - `go.mod` (Go)
   - `pom.xml` / `build.gradle` (Java)

3. **디렉토리 구조 파악**
   ```bash
   find . -type d -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/venv/*' | head -30
   ```

4. **진입점 탐색** - main 함수, CLI entrypoint, 서버 시작 파일 등

5. **출력 형식**
   ```
   === 프로젝트 개요 ===
   이름: {프로젝트 이름}
   언어: {주 언어}
   프레임워크: {감지된 프레임워크}
   진입점: {메인 파일 경로}
   디렉토리 수: {N}개
   파일 수: {N}개 (추정)
   ```
