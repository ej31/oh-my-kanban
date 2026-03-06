// 다국어 지원 모듈
export type Lang = 'en' | 'ko';

export const messages = {
  en: {
    intro: 'oh-my-kanban Setup Wizard',
    setupWizard: 'Setup Wizard',

    // service-select
    selectService: 'Select a project management service',
    planeHint: 'Open-source project management',
    linearHint: 'SaaS project management',
    githubHint: 'GitHub Issues / Projects',

    // plane
    isSelfHosted: 'Are you self-hosting Plane?',
    planeServerUrl: 'Plane server URL',
    planeUrlRequired: 'Please enter a URL',
    planeUrlInvalid: 'Invalid URL format',
    planeApiKey: 'Plane API key',
    planeApiKeyRequired: 'Please enter an API key',
    planeWorkspace: 'Workspace URL or slug',
    planeWorkspacePlaceholder: 'https://app.plane.so/my-workspace/... or my-workspace',
    planeWorkspaceRequired: 'Please enter workspace info',

    // linear
    linearApiKey: 'Linear API key',
    linearApiKeyRequired: 'Please enter an API key',
    linearTeamId: 'Linear Team ID',
    linearTeamIdPlaceholder: 'team_xxxxxxxx',
    linearTeamIdRequired: 'Please enter a Team ID',

    // github - gh CLI setup
    ghNotInstalled: 'gh CLI not found',
    ghNotAuthenticated: 'gh CLI not authenticated',
    ghReadyTitle: 'gh CLI is ready',
    ghInstallMacOS: 'Install via Homebrew:\n  brew install gh',
    ghInstallWindows: 'Install via winget:\n  winget install --id GitHub.cli\n\nOr via Scoop:\n  scoop install gh',
    ghInstallLinux: 'Install via apt (Debian/Ubuntu):\n  sudo apt install gh\n\nOr via dnf (Fedora/RHEL):\n  sudo dnf install gh',
    ghAuthInstruction: 'Authenticate with GitHub:\n  gh auth login',
    ghRerun: 'Then re-run the setup wizard:\n  npx oh-my-kanban',
    ghReadyNote: 'gh CLI is installed and authenticated.\nGitHub support in oh-my-kanban is coming soon.',

    // index
    pythonNotFound: 'Python not found. Please install Python 3.10+ from https://www.python.org/downloads/',
    pipNotFound: 'pip not found. Please check that Python and pip are installed correctly.',
    configSaveFailed: 'Failed to save config file: ',
    unexpectedError: 'Unexpected error: ',
    outro: 'Setup complete! Run `omk` to get started.',
  },
  ko: {
    intro: 'oh-my-kanban 설정 위저드',
    setupWizard: '설정 위저드',

    // service-select
    selectService: '사용할 프로젝트 관리 서비스를 선택하세요',
    planeHint: '오픈소스 프로젝트 관리',
    linearHint: 'SaaS 프로젝트 관리',
    githubHint: 'GitHub Issues / Projects',

    // plane
    isSelfHosted: 'Plane을 직접 호스팅(self-hosted)하고 있나요?',
    planeServerUrl: 'Plane 서버 URL을 입력하세요',
    planeUrlRequired: 'URL을 입력해주세요',
    planeUrlInvalid: '올바른 URL 형식이 아닙니다',
    planeApiKey: 'Plane API 키를 입력하세요',
    planeApiKeyRequired: 'API 키를 입력해주세요',
    planeWorkspace: 'Workspace URL 또는 slug를 입력하세요',
    planeWorkspacePlaceholder: 'https://app.plane.so/my-workspace/projects/... 또는 my-workspace',
    planeWorkspaceRequired: 'Workspace 정보를 입력해주세요',

    // linear
    linearApiKey: 'Linear API 키를 입력하세요',
    linearApiKeyRequired: 'API 키를 입력해주세요',
    linearTeamId: 'Linear Team ID를 입력하세요',
    linearTeamIdPlaceholder: 'team_xxxxxxxx',
    linearTeamIdRequired: 'Team ID를 입력해주세요',

    // github - gh CLI setup (note box는 정렬 문제로 영문 유지)
    ghNotInstalled: 'gh CLI not found',
    ghNotAuthenticated: 'gh CLI not authenticated',
    ghReadyTitle: 'gh CLI is ready',
    ghInstallMacOS: 'Install via Homebrew:\n  brew install gh',
    ghInstallWindows: 'Install via winget:\n  winget install --id GitHub.cli\n\nOr via Scoop:\n  scoop install gh',
    ghInstallLinux: 'Install via apt (Debian/Ubuntu):\n  sudo apt install gh\n\nOr via dnf (Fedora/RHEL):\n  sudo dnf install gh',
    ghAuthInstruction: 'Authenticate with GitHub:\n  gh auth login',
    ghRerun: 'Then re-run the setup wizard:\n  npx oh-my-kanban',
    ghReadyNote: 'gh CLI is installed and authenticated.\nGitHub support in oh-my-kanban is coming soon.',

    // index
    pythonNotFound: 'Python을 찾을 수 없습니다. https://www.python.org/downloads/ 에서 Python 3.10 이상을 설치하세요.',
    pipNotFound: 'pip을 찾을 수 없습니다. Python과 pip이 올바르게 설치되어 있는지 확인하세요.',
    configSaveFailed: '설정 파일 저장 실패: ',
    unexpectedError: '예상치 못한 오류가 발생했습니다: ',
    outro: '설정이 완료되었습니다! `omk` 명령어로 시작하세요.',
  },
} as const;

export type Messages = typeof messages['en'];

let currentLang: Lang = 'en';

export function setLang(lang: Lang): void {
  currentLang = lang;
}

export function t(): Messages {
  return messages[currentLang];
}
