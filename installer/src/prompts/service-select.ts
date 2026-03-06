import { select, isCancel } from '@clack/prompts';
import { t } from '../i18n.js';
import { RestartWizard, RESTART_SENTINEL } from '../restart.js';

export type ServiceType = 'plane' | 'linear' | 'github';

export async function promptServiceSelect(): Promise<ServiceType> {
  const m = t();
  const service = await select<string>({
    message: m.selectService,
    options: [
      { value: 'plane', label: 'Plane', hint: m.planeHint },
      { value: 'linear', label: 'Linear', hint: m.linearHint },
      { value: 'github', label: 'GitHub', hint: m.githubHint },
      { value: RESTART_SENTINEL, label: m.returnToFirstStep },
    ],
  });

  if (isCancel(service)) {
    process.exit(0);
  }

  if (service === RESTART_SENTINEL) {
    throw new RestartWizard();
  }

  return service as ServiceType;
}
