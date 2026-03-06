import { password, text, isCancel, spinner, cancel } from '@clack/prompts';
import pc from 'picocolors';
import {
  validateLinearApiKeyFormat,
  validateLinearTeamIdFormat,
  testLinearConnection,
} from '../validators/linear.js';

export interface LinearConfig {
  apiKey: string;
  teamId: string;
}

export async function promptLinearConfig(): Promise<LinearConfig> {
  // API 키 (마스킹) — 형식 검증 포함
  const apiKey = await password({
    message: 'Linear API 키를 입력하세요',
    validate(value) {
      return validateLinearApiKeyFormat(value);
    },
  });

  if (isCancel(apiKey)) {
    process.exit(0);
  }

  // Team ID — UUID 형식 검증 포함
  const teamId = await text({
    message: 'Linear Team ID를 입력하세요',
    placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    validate(value) {
      return validateLinearTeamIdFormat(value);
    },
  });

  if (isCancel(teamId)) {
    process.exit(0);
  }

  const normalizedApiKey = (apiKey as string).trim();
  const normalizedTeamId = (teamId as string).trim();

  // 실제 API 연결 테스트
  const s = spinner();
  s.start('Linear API 연결을 확인하는 중...');

  const result = await testLinearConnection(normalizedApiKey, normalizedTeamId);

  if (!result.ok) {
    s.stop(pc.red(`연결 실패: ${result.error}`));
    cancel('입력한 값을 확인한 후 다시 시도하세요.');
    process.exit(1);
  }

  s.stop(pc.green('Linear API 연결 성공'));

  return {
    apiKey: normalizedApiKey,
    teamId: normalizedTeamId,
  };
}
