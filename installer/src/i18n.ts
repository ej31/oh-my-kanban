// 다국어 지원 모듈
export type Lang = 'en' | 'ko';

export const messages = {
  en: {
    intro: 'oh-my-kanban Setup Wizard',
    setupWizard: 'Setup Wizard',

    // navigation
    returnToFirstStep: '↩ Return to First step (Language selection)',

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
    planeValidating: 'Verifying credentials...',
    planeConnectFailed: 'Cannot connect to Plane server — check your URL',
    planeAuthFailed: 'Invalid API key',
    planeWorkspaceNotFound: 'Workspace not found — check your slug',
    planeFetchingWorkspaces: 'Fetching workspaces...',
    planeSelectWorkspace: 'Select your workspace',
    planeNoWorkspacesFound: 'No workspaces found — enter slug manually',

    // linear
    linearApiKey: 'Linear API key',
    linearApiKeyRequired: 'Please enter an API key',
    linearTeamId: 'Linear Team ID',
    linearTeamIdPlaceholder: 'team_xxxxxxxx',
    linearTeamIdRequired: 'Please enter a Team ID',
    linearValidating: 'Verifying credentials...',
    linearAuthFailed: 'Invalid API key',
    linearTeamNotFound: 'Team not found — check your Team ID',
    linearConnectFailed: 'Cannot connect to Linear',
    linearFetchingTeams: 'Fetching your teams...',
    linearSelectTeam: 'Select your Linear team',
    linearNoTeamsFound: 'No teams found — enter Team ID manually',
    linearTeamIdHint: 'Team ID can be found at linear.app → Settings → Members → Teams → select team → copy ID from URL',
    linearCreateNewTeam: '+ Create a new team',
    linearNewTeamName: 'New team name',
    linearTeamNameRequired: 'Please enter a team name',
    linearCreatingTeam: 'Creating team...',
    linearTeamCreateFailed: 'Failed to create team — check your permissions',

    // github - gh CLI setup
    ghNotInstalled: 'gh CLI not found',
    ghNotAuthenticated: 'gh CLI not authenticated',
    ghReadyTitle: 'gh CLI is ready',
    ghScopesRequired: 'Additional permissions required',
    ghInstallMacOS: 'Install via Homebrew:\n  brew install gh',
    ghInstallWindows: 'Install via winget:\n  winget install --id GitHub.cli\n\nOr via Scoop:\n  scoop install gh',
    ghInstallLinux: 'Install via apt (Debian/Ubuntu):\n  sudo apt install gh\n\nOr via dnf (Fedora/RHEL):\n  sudo dnf install gh',
    ghInstallUnsupported: 'Please install GitHub CLI manually:\n  https://cli.github.com',
    ghAuthInstruction: 'Authenticate with GitHub:\n  gh auth login',
    ghRerun: 'Then re-run the setup wizard:\n  npx oh-my-kanban',
    ghReadyNote: 'gh CLI is installed and authenticated — you are all set!\n\noh-my-kanban uses the official GitHub CLI (gh) to manage\nyour GitHub issues and projects. No extra setup needed.\n\nTry it now:\n  gh issue list\n  gh issue create',
    ghScopeMissing: 'Required permissions are missing — GitHub features will NOT work without them',
    ghAddScopes: 'Add all required permissions with this command:',
    ghApiTestFailed: 'GitHub API test failed — re-run the setup wizard after re-authenticating:\n  gh auth login',

    // index
    pythonNotFound: 'Python not found. Please install Python 3.10+ from https://www.python.org/downloads/',
    pipNotFound: 'pip not found. Please check that Python and pip are installed correctly.',
    configSaveFailed: 'Failed to save config file: ',
    unexpectedError: 'Unexpected error: ',
    outroPlane: 'Setup complete!\n  List issues:   omk pl work-item list\n  Create issue:  omk pl work-item create\n  List projects: omk pl project list',
    outroLinear: 'Setup complete!\n  List issues:   omk ln issue list\n  Create issue:  omk ln issue create',
    outro: 'Setup complete! Run `omk` to get started.',

    // claude code scope
    claudeScopeTitle: 'Claude Code Integration',
    claudeScopeNote: 'oh-my-kanban can install hooks and MCP server config into Claude Code.\n\nProject scope is recommended because KANBAN settings differ per project\n— each project has its own workspace, API key, and team.',
    claudeScopeSelect: 'Where should Claude Code settings (hooks, MCP) be installed?',
    claudeScopeUser: 'Install for you (user scope)',
    claudeScopeUserHint: '~/.claude/settings.json — all projects globally',
    claudeScopeProject: 'Install for all collaborators on this repository (project scope)',
    claudeScopeProjectHint: './.claude/settings.json — committed to git, shared',
    claudeScopeLocal: 'Install for you, in this repo only (local scope)',
    claudeScopeLocalHint: './.claude/settings.local.json — gitignored, personal',
    claudeHooksInstalling: 'Installing hooks...',
    claudeHooksInstalled: 'Hooks installed',
    claudeHooksFailed: 'Hook installation failed — run manually: omk hooks install',
    claudeMcpTitle: 'MCP Server Setup',
    claudeMcpNote: 'Register oh-my-kanban as an MCP server in Claude Code.\nAdd to {path}:\n\n  {\n    "mcpServers": {\n      "oh-my-kanban": {\n        "command": "omk",\n        "args": ["mcp", "serve"]\n      }\n    }\n  }',

    // plane project
    planeFetchingProjects: 'Fetching projects...',
    planeSelectProject: 'Select a project',
    planeCreateProject: '+ Create a new project',
    planeSkipProject: 'Skip (set later with: omk config set project_id <id>)',
    planeProjectName: 'New project name',
    planeProjectNameRequired: 'Please enter a project name',
    planeProjectNameTooLong: 'Project name must be 255 characters or fewer',
    planeProjectCreating: 'Creating project...',
    planeProjectCreated: 'Project created',
    planeProjectCreateFailed: 'Failed to create project — check your permissions',
    planeNoProjectsFound: 'No projects found — create one to get started',
  },
  ko: {
    intro: 'oh-my-kanban 설정 위저드',
    setupWizard: '설정 위저드',

    // navigation
    returnToFirstStep: '↩ 처음으로 돌아가기 (Return to First step)',

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
    planeValidating: '자격 증명 확인 중...',
    planeConnectFailed: 'Plane 서버에 연결할 수 없습니다 — URL을 확인해주세요',
    planeAuthFailed: 'API 키가 올바르지 않습니다',
    planeWorkspaceNotFound: 'Workspace를 찾을 수 없습니다 — slug를 확인해주세요',
    planeFetchingWorkspaces: '워크스페이스 목록 조회 중...',
    planeSelectWorkspace: '사용할 워크스페이스를 선택하세요',
    planeNoWorkspacesFound: '워크스페이스를 찾을 수 없어 직접 입력합니다',

    // linear
    linearApiKey: 'Linear API 키를 입력하세요',
    linearApiKeyRequired: 'API 키를 입력해주세요',
    linearTeamId: 'Linear Team ID를 입력하세요',
    linearTeamIdPlaceholder: 'team_xxxxxxxx',
    linearTeamIdRequired: 'Team ID를 입력해주세요',
    linearValidating: '자격 증명 확인 중...',
    linearAuthFailed: 'API 키가 올바르지 않습니다',
    linearTeamNotFound: '팀을 찾을 수 없습니다 — Team ID를 확인해주세요',
    linearConnectFailed: 'Linear에 연결할 수 없습니다',
    linearFetchingTeams: '팀 목록을 가져오는 중...',
    linearSelectTeam: '사용할 Linear 팀을 선택하세요',
    linearNoTeamsFound: '팀을 찾을 수 없습니다 — Team ID를 직접 입력해주세요',
    linearTeamIdHint: 'Team ID 찾는 방법: linear.app → Settings → Members → Teams → 팀 선택 → URL에서 ID 복사',
    linearCreateNewTeam: '+ 새 팀 만들기',
    linearNewTeamName: '새 팀 이름을 입력하세요',
    linearTeamNameRequired: '팀 이름을 입력해주세요',
    linearCreatingTeam: '팀을 생성하는 중...',
    linearTeamCreateFailed: '팀 생성에 실패했습니다 — 권한을 확인해주세요',

    // github - gh CLI setup
    ghNotInstalled: 'gh CLI를 찾을 수 없습니다',
    ghNotAuthenticated: 'gh CLI 인증이 필요합니다',
    ghReadyTitle: 'gh CLI 준비 완료',
    ghScopesRequired: '추가 권한이 필요합니다',
    ghInstallMacOS: 'Homebrew로 설치하세요:\n  brew install gh',
    ghInstallWindows: 'winget으로 설치하세요:\n  winget install --id GitHub.cli\n\nScoop으로 설치하세요:\n  scoop install gh',
    ghInstallLinux: 'apt로 설치하세요 (Debian/Ubuntu):\n  sudo apt install gh\n\ndnf로 설치하세요 (Fedora/RHEL):\n  sudo dnf install gh',
    ghInstallUnsupported: 'GitHub CLI를 수동으로 설치하세요:\n  https://cli.github.com',
    ghAuthInstruction: 'GitHub 인증을 진행하세요:\n  gh auth login',
    ghRerun: '완료 후 다시 실행하세요:\n  npx oh-my-kanban',
    ghReadyNote: 'gh CLI가 설치되어 있고 인증도 완료되었습니다!\n\noh-my-kanban은 GitHub 공식 CLI(gh)를 활용하여\nGitHub 이슈와 프로젝트를 관리합니다.\n추가 설정 없이 바로 사용할 수 있습니다.\n\n바로 시작하기:\n  gh issue list\n  gh issue create',
    ghScopeMissing: '필수 권한이 없으면 GitHub 기능을 전혀 사용할 수 없습니다',
    ghAddScopes: '아래 명령어로 필수 권한을 모두 추가하세요:',
    ghApiTestFailed: 'GitHub API 테스트 실패 — 재인증 후 다시 실행하세요:\n  gh auth login',

    // index
    pythonNotFound: 'Python을 찾을 수 없습니다. https://www.python.org/downloads/ 에서 Python 3.10 이상을 설치하세요.',
    pipNotFound: 'pip을 찾을 수 없습니다. Python과 pip이 올바르게 설치되어 있는지 확인하세요.',
    configSaveFailed: '설정 파일 저장 실패: ',
    unexpectedError: '예상치 못한 오류가 발생했습니다: ',
    outroPlane: '설정이 완료되었습니다!\n  이슈 목록:    omk pl work-item list\n  이슈 생성:    omk pl work-item create\n  프로젝트 목록: omk pl project list',
    outroLinear: '설정이 완료되었습니다!\n  이슈 목록: omk ln issue list\n  이슈 생성: omk ln issue create',
    outro: '설정이 완료되었습니다! `omk` 명령어로 시작하세요.',

    // claude code scope
    claudeScopeTitle: 'Claude Code 연동 설정',
    claudeScopeNote: 'oh-my-kanban이 Claude Code 훅과 MCP 서버 설정을 자동으로 등록할 수 있습니다.\n\nKANBAN은 프로젝트 단위로 설정이 모두 다르므로\n가급적 Project scope을 추천합니다.',
    claudeScopeSelect: 'Claude Code 설정(훅, MCP)을 어디에 설치하시겠습니까?',
    claudeScopeUser: '나에게만 설치 (user scope)',
    claudeScopeUserHint: '~/.claude/settings.json — 모든 프로젝트에 전역 적용',
    claudeScopeProject: '이 저장소의 모든 협업자에게 설치 (project scope)',
    claudeScopeProjectHint: './.claude/settings.json — git에 커밋되어 공유됨',
    claudeScopeLocal: '나에게만, 이 저장소에서만 설치 (local scope)',
    claudeScopeLocalHint: './.claude/settings.local.json — git 무시, 개인 전용',
    claudeHooksInstalling: '훅 설치 중...',
    claudeHooksInstalled: '훅 설치 완료',
    claudeHooksFailed: '훅 설치 실패 — 수동 실행: omk hooks install',
    claudeMcpTitle: 'MCP 서버 설정',
    claudeMcpNote: 'oh-my-kanban을 Claude Code MCP 서버로 등록하세요.\n{path} 에 아래 내용을 추가하세요:\n\n  {\n    "mcpServers": {\n      "oh-my-kanban": {\n        "command": "omk",\n        "args": ["mcp", "serve"]\n      }\n    }\n  }',

    // plane project
    planeFetchingProjects: '프로젝트 목록 조회 중...',
    planeSelectProject: '사용할 프로젝트를 선택하세요',
    planeCreateProject: '+ 새 프로젝트 만들기',
    planeSkipProject: '건너뛰기 (나중에: omk config set project_id <id>)',
    planeProjectName: '새 프로젝트 이름을 입력하세요',
    planeProjectNameRequired: '프로젝트 이름을 입력해주세요',
    planeProjectNameTooLong: '프로젝트 이름은 255자 이하여야 합니다',
    planeProjectCreating: '프로젝트 생성 중...',
    planeProjectCreated: '프로젝트 생성 완료',
    planeProjectCreateFailed: '프로젝트 생성 실패 — 권한을 확인해주세요',
    planeNoProjectsFound: '프로젝트가 없습니다 — 새로 만드세요',
  },
};

export type Messages = typeof messages['en'];

let currentLang: Lang = 'en';

export function setLang(lang: Lang): void {
  currentLang = lang;
}

export function t(): Messages {
  return messages[currentLang];
}
