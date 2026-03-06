import { select, isCancel } from '@clack/prompts';

export type ServiceType = 'plane' | 'linear' | 'github';

export async function promptServiceSelect(): Promise<ServiceType> {
  const service = await select<ServiceType>({
    message: '사용할 프로젝트 관리 서비스를 선택하세요',
    options: [
      { value: 'plane', label: 'Plane', hint: '오픈소스 프로젝트 관리' },
      { value: 'linear', label: 'Linear', hint: 'SaaS 프로젝트 관리' },
      { value: 'github', label: 'GitHub', hint: 'GitHub Issues / Projects' },
    ],
  });

  if (isCancel(service)) {
    process.exit(0);
  }

  return service as ServiceType;
}
