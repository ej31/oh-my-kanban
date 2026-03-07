// @clack/prompts의 note()는 String.length 기준으로 박스 너비를 계산한다.
// 한글/CJK 문자는 터미널에서 2컬럼을 차지하지만 length는 1이므로
// 각 줄에 (displayWidth - length) 만큼 공백을 추가해 박스가 맞게 그려지도록 보정한다.
import stringWidth from 'string-width';

/** note() 본문 텍스트의 각 줄을 보정한다. */
export function padForNote(text: string): string {
  return text
    .split('\n')
    .map((line) => {
      const padding = stringWidth(line) - line.length;
      return padding > 0 ? line + ' '.repeat(padding) : line;
    })
    .join('\n');
}

/** note() 타이틀 문자열을 보정한다. */
export function padTitle(title: string): string {
  const padding = stringWidth(title) - title.length;
  return padding > 0 ? title + ' '.repeat(padding) : title;
}
