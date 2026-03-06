import { select, isCancel } from '@clack/prompts';
import { t } from '../i18n.js';

export type ServiceType = 'plane' | 'linear' | 'github';

export async function promptServiceSelect(): Promise<ServiceType> {
  const m = t();
  const service = await select<ServiceType>({
    message: m.selectService,
    options: [
      { value: 'plane', label: 'Plane', hint: m.planeHint },
      { value: 'linear', label: 'Linear', hint: m.linearHint },
      { value: 'github', label: 'GitHub', hint: m.githubHint },
    ],
  });

  if (isCancel(service)) {
    process.exit(0);
  }

  return service as ServiceType;
}
