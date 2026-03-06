/**
 * config-writer 단위 테스트
 *
 * escapeTomlValue() 함수의 특수문자 이스케이프 동작을 검증한다.
 * 실제 구현은 src/config-writer.ts에 위치할 예정이다.
 */
import { describe, it, expect } from 'vitest';
import { escapeTomlValue } from '../../src/config-writer.js';

describe('escapeTomlValue', () => {
  it('일반 문자열은 이스케이프 없이 그대로 반환한다', () => {
    expect(escapeTomlValue('hello-world')).toBe('hello-world');
  });

  it('백슬래시를 이중 백슬래시로 이스케이프한다', () => {
    // a\b → a\\b (TOML 기본 문자열 표현)
    expect(escapeTomlValue('a\\b')).toBe('a\\\\b');
  });

  it('큰따옴표를 역슬래시-따옴표로 이스케이프한다', () => {
    // say "hi" → say \"hi\"
    expect(escapeTomlValue('say "hi"')).toBe('say \\"hi\\"');
  });

  it('줄바꿈 문자를 \\n 리터럴로 이스케이프한다', () => {
    // line1\nline2 → line1\\nline2
    expect(escapeTomlValue('line1\nline2')).toBe('line1\\nline2');
  });

  it('백슬래시, 따옴표, 줄바꿈이 복합된 경우 모두 이스케이프한다', () => {
    // path: C:\Users\name\n"quoted"
    // 백슬래시 먼저 이스케이프 후 따옴표, 줄바꿈 순서로 처리됨
    const input = 'C:\\Users\\name\n"quoted"';
    const expected = 'C:\\\\Users\\\\name\\n\\"quoted\\"';
    expect(escapeTomlValue(input)).toBe(expected);
  });

  it('캐리지 리턴을 \\r 리터럴로 이스케이프한다', () => {
    expect(escapeTomlValue('line1\r\nline2')).toBe('line1\\r\\nline2');
  });
});
