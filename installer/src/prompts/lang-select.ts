import { select, isCancel } from '@clack/prompts';
import { setLang, type Lang } from '../i18n.js';

export async function promptLangSelect(): Promise<void> {
  const lang = await select<Lang>({
    message: 'Language / 언어',
    options: [
      { value: 'en', label: 'English' },
      { value: 'ko', label: '한국어' },
    ],
  });

  if (isCancel(lang)) {
    process.exit(0);
  }

  setLang(lang as Lang);
}
