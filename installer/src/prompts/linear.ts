import { password, text, select, isCancel, spinner, note } from '@clack/prompts';
import pc from 'picocolors';
import { t } from '../i18n.js';
import { RestartWizard, RESTART_SENTINEL } from '../restart.js';

export interface LinearConfig {
  apiKey: string;
  teamId: string;
}

const LINEAR_API_URL = 'https://api.linear.app/graphql';
const LINEAR_API_TIMEOUT_MS = 8000;

/**
 * Linear GraphQL API로 새 팀을 생성하고 팀 ID를 반환한다.
 * 실패 시 null을 반환하여 호출자가 팀 선택 화면으로 돌아가도록 한다.
 */
async function createLinearTeam(
  apiKey: string,
  m: ReturnType<typeof t>,
): Promise<string | null> {
  const nameRaw = await text({
    message: m.linearNewTeamName,
    validate(value) {
      if (!value.trim()) return m.linearTeamNameRequired;
    },
  });
  if (isCancel(nameRaw)) {
    process.exit(0);
  }

  const teamName = (nameRaw as string).trim();
  const s = spinner();
  s.start(m.linearCreatingTeam);

  try {
    const res = await fetch(LINEAR_API_URL, {
      method: 'POST',
      headers: {
        Authorization: apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: `
          mutation {
            teamCreate(input: { name: "${teamName}" }) {
              success
              team { id name }
            }
          }
        `,
      }),
      signal: AbortSignal.timeout(LINEAR_API_TIMEOUT_MS),
    });

    if (!res.ok) {
      s.stop(pc.red(`✗ ${m.linearTeamCreateFailed}`));
      return null;
    }

    const json = (await res.json()) as {
      data?: { teamCreate?: { success: boolean; team?: { id: string; name: string } } };
      errors?: { message: string }[];
    };

    const result = json.data?.teamCreate;
    if (result?.success && result.team) {
      s.stop(pc.green(`✓ ${result.team.name}`));
      return result.team.id;
    }

    s.stop(pc.red(`✗ ${m.linearTeamCreateFailed}`));
    return null;
  } catch {
    s.stop(pc.red(`✗ ${m.linearConnectFailed}`));
    return null;
  }
}

export async function promptLinearConfig(): Promise<LinearConfig> {
  const m = t();

  // API 키 입력 + 실제 GraphQL 검증 루프
  let apiKey = '';
  while (true) {
    const apiKeyRaw = await password({
      message: m.linearApiKey,
      validate(value) {
        if (!value.trim()) return m.linearApiKeyRequired;
      },
    });

    if (isCancel(apiKeyRaw)) {
      process.exit(0);
    }

    const s = spinner();
    s.start(m.linearValidating);
    let valid = false;

    try {
      const res = await fetch(LINEAR_API_URL, {
        method: 'POST',
        headers: {
          Authorization: apiKeyRaw as string,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: '{ viewer { id } }' }),
        signal: AbortSignal.timeout(LINEAR_API_TIMEOUT_MS),
      });

      if (res.status === 401) {
        s.stop(pc.red(`✗ ${m.linearAuthFailed}`));
      } else if (!res.ok) {
        s.stop(pc.red(`✗ ${m.linearConnectFailed}`));
      } else {
        const json = (await res.json()) as {
          errors?: { message: string }[];
        };
        if (json.errors?.length) {
          s.stop(pc.red(`✗ ${m.linearAuthFailed}`));
        } else {
          s.stop(pc.green('✓'));
          apiKey = apiKeyRaw as string;
          valid = true;
        }
      }
    } catch {
      s.stop(pc.red(`✗ ${m.linearConnectFailed}`));
    }

    if (valid) break;
  }

  // API 키 검증 성공 후 팀 목록 자동 조회
  const s2 = spinner();
  s2.start(m.linearFetchingTeams);

  let teams: { id: string; name: string }[] = [];
  let teamFetchSucceeded = false;
  try {
    const res = await fetch(LINEAR_API_URL, {
      method: 'POST',
      headers: {
        Authorization: apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: '{ teams { nodes { id name } } }' }),
      signal: AbortSignal.timeout(LINEAR_API_TIMEOUT_MS),
    });
    if (res.ok) {
      const json = (await res.json()) as {
        data?: { teams: { nodes: { id: string; name: string }[] } };
      };
      teams = json.data?.teams?.nodes ?? [];
      teamFetchSucceeded = true;
    }
  } catch {
    // 조회 실패 시 수동 입력으로 폴백
  }
  s2.stop();

  // 팀 선택 또는 수동 입력
  let teamId = '';
  const CREATE_TEAM_SENTINEL = '__create__';

  // 조회 성공(빈 목록 포함) → select 메뉴, 조회 실패 → 수동 입력 폴백
  if (teamFetchSucceeded) {
    // 팀 목록 조회 성공 → select 프롬프트 (새 팀 만들기 + 처음으로 돌아가기 포함)
    while (true) {
      const selected = await select<string>({
        message: m.linearSelectTeam,
        options: [
          ...teams.map((team) => ({ value: team.id, label: team.name })),
          { value: CREATE_TEAM_SENTINEL, label: m.linearCreateNewTeam },
          { value: RESTART_SENTINEL, label: m.returnToFirstStep },
        ],
      });

      if (isCancel(selected)) {
        process.exit(0);
      }

      if (selected === RESTART_SENTINEL) {
        throw new RestartWizard();
      }

      if (selected === CREATE_TEAM_SENTINEL) {
        const newTeamId = await createLinearTeam(apiKey, m);
        if (newTeamId !== null) {
          teamId = newTeamId;
          break;
        }
        // null = 생성 실패 → 팀 선택 화면으로 돌아간다
        continue;
      }

      teamId = selected as string;
      break;
    }
  } else {
    // 팀 목록 조회 실패 → 수동 입력 + Team ID 찾는 방법 안내
    note(m.linearTeamIdHint, m.linearNoTeamsFound);

    while (true) {
      const teamIdRaw = await text({
        message: m.linearTeamId,
        placeholder: m.linearTeamIdPlaceholder,
        validate(value) {
          if (!value.trim()) return m.linearTeamIdRequired;
        },
      });

      if (isCancel(teamIdRaw)) {
        process.exit(0);
      }

      const candidateTeamId = (teamIdRaw as string).trim();
      const s = spinner();
      s.start(m.linearValidating);
      let valid = false;

      try {
        const res = await fetch(LINEAR_API_URL, {
          method: 'POST',
          headers: {
            Authorization: apiKey,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: `{ team(id: "${candidateTeamId}") { id name } }`,
          }),
          signal: AbortSignal.timeout(LINEAR_API_TIMEOUT_MS),
        });

        if (res.status === 401) {
          s.stop(pc.red(`✗ ${m.linearAuthFailed}`));
        } else if (!res.ok) {
          s.stop(pc.red(`✗ ${m.linearConnectFailed}`));
        } else {
          const json = (await res.json()) as {
            data?: { team: { id: string } | null };
            errors?: { message: string }[];
          };
          if (!json.data?.team) {
            s.stop(pc.red(`✗ ${m.linearTeamNotFound}`));
          } else {
            s.stop(pc.green('✓'));
            teamId = candidateTeamId;
            valid = true;
          }
        }
      } catch {
        s.stop(pc.red(`✗ ${m.linearConnectFailed}`));
      }

      if (valid) break;
    }
  }

  return { apiKey, teamId };
}
