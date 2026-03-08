"""GitHub CLI wrapper: gh CLI를 통한 GitHub 이슈/PR 관리."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys

import click

# 레포지토리 형식 검증 패턴 (owner/repo)
# 첫 글자는 반드시 영숫자여야 함 (GitHub 실제 제약 반영, '..'/'.-' 등 방지)
_REPO_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*/[a-zA-Z0-9][a-zA-Z0-9._-]*$")

def _validate_repo(repo: str | None) -> None:
    """레포지토리 형식을 검증한다. 유효하지 않으면 ClickException을 발생시킨다."""
    if repo and not _REPO_RE.match(repo):
        raise click.ClickException(
            "레포지토리 형식이 잘못되었습니다. 'owner/repo' 형식으로 입력하세요."
        )



# gh CLI 명령 실행 타임아웃 (초)
_GH_TIMEOUT = 30

# gh CLI 설치 안내 URL
_GH_INSTALL_URL = "https://cli.github.com/"


def _check_gh_available() -> None:
    """gh CLI가 설치되어 있는지 확인한다. 없으면 ClickException."""
    if shutil.which("gh") is None:
        raise click.ClickException(
            f"gh CLI를 찾을 수 없습니다.\n"
            f"설치: {_GH_INSTALL_URL}"
        )


def _run_gh(*args: str) -> str:
    """gh CLI를 실행하고 stdout을 반환한다.

    Args:
        *args: gh 명령 인자 (리스트로 전달, 셸 인젝션 방지)

    Returns:
        명령 stdout 문자열

    Raises:
        click.ClickException: gh 실행 실패 시
    """
    _check_gh_available()

    cmd = ["gh", *args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_GH_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise click.ClickException(
            f"gh 명령이 {_GH_TIMEOUT}초 내에 완료되지 않았습니다."
        )
    except OSError as e:
        raise click.ClickException(f"gh 실행 실패: {e}")

    if result.returncode != 0:
        stderr = result.stderr.strip()
        # 인증 문제 감지
        if "auth" in stderr.lower() or "login" in stderr.lower():
            raise click.ClickException(
                f"GitHub 인증이 필요합니다.\n"
                f"실행: gh auth login\n\n"
                f"원본 에러: {stderr}"
            )
        raise click.ClickException(f"gh 명령 실패: {stderr or '알 수 없는 오류'}")

    return result.stdout


# ── Click 커맨드 그룹 ───────────────────────────────────────────────────────


@click.group("github")
def github() -> None:
    """GitHub 프로젝트 관리 (Issues, Projects, Milestones, Labels).

    \b
    omk github issue list --repo owner/repo
    omk github pr list --repo owner/repo

    'gh'는 'github'의 단축 alias입니다.
    """


# ── Issue 서브그룹 ──────────────────────────────────────────────────────────


@github.group("issue")
def issue() -> None:
    """GitHub 이슈 관리."""


@issue.command("list")
@click.option("--repo", "-R", default=None, help="대상 레포지토리 (owner/repo)")
@click.option(
    "--state", "-s",
    default="open",
    type=click.Choice(["open", "closed", "all"], case_sensitive=False),
    help="이슈 상태 (open, closed, all)",
)
@click.option("--limit", "-L", default=30, type=int, help="최대 표시 개수")
def issue_list(repo: str | None, state: str, limit: int) -> None:
    """이슈 목록을 조회한다."""
    _validate_repo(repo)
    # 인자 범위 방어
    limit = max(1, min(limit, 1000))
    args = ["issue", "list", "--state", state, "--limit", str(limit)]
    if repo:
        args.extend(["--repo", repo])
    output = _run_gh(*args)
    click.echo(output)


@issue.command("view")
@click.argument("number", type=int)
@click.option("--repo", "-R", default=None, help="대상 레포지토리 (owner/repo)")
def issue_view(number: int, repo: str | None) -> None:
    """이슈 상세 정보를 조회한다."""
    _validate_repo(repo)
    if number <= 0:
        raise click.ClickException("이슈 번호는 양의 정수여야 합니다.")
    args = ["issue", "view", str(number)]
    if repo:
        args.extend(["--repo", repo])
    output = _run_gh(*args)
    click.echo(output)


@issue.command("create")
@click.option("--title", "-t", required=True, help="이슈 제목")
@click.option("--body", "-b", default="", help="이슈 본문")
@click.option("--repo", "-R", default=None, help="대상 레포지토리 (owner/repo)")
def issue_create(title: str, body: str, repo: str | None) -> None:
    """새 이슈를 생성한다."""
    _validate_repo(repo)
    if not title.strip():
        raise click.ClickException("이슈 제목은 필수입니다.")
    args = ["issue", "create", "--title", title]
    if body:
        args.extend(["--body", body])
    if repo:
        args.extend(["--repo", repo])
    output = _run_gh(*args)
    click.echo(output)


# ── PR 서브그룹 ─────────────────────────────────────────────────────────────


@github.group("pr")
def pr() -> None:
    """GitHub Pull Request 관리."""


@pr.command("list")
@click.option("--repo", "-R", default=None, help="대상 레포지토리 (owner/repo)")
@click.option(
    "--state", "-s",
    default="open",
    type=click.Choice(["open", "closed", "merged", "all"], case_sensitive=False),
    help="PR 상태 (open, closed, merged, all)",
)
@click.option("--limit", "-L", default=30, type=int, help="최대 표시 개수")
def pr_list(repo: str | None, state: str, limit: int) -> None:
    """Pull Request 목록을 조회한다."""
    _validate_repo(repo)
    # 인자 범위 방어
    limit = max(1, min(limit, 1000))
    args = ["pr", "list", "--state", state, "--limit", str(limit)]
    if repo:
        args.extend(["--repo", repo])
    output = _run_gh(*args)
    click.echo(output)


@pr.command("view")
@click.argument("number", type=int)
@click.option("--repo", "-R", default=None, help="대상 레포지토리 (owner/repo)")
def pr_view(number: int, repo: str | None) -> None:
    """Pull Request 상세 정보를 조회한다."""
    _validate_repo(repo)
    if number <= 0:
        raise click.ClickException("PR 번호는 양의 정수여야 합니다.")
    args = ["pr", "view", str(number)]
    if repo:
        args.extend(["--repo", repo])
    output = _run_gh(*args)
    click.echo(output)
