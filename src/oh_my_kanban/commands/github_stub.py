"""GitHub 커맨드 그룹 (향후 구현 예정)."""

import click


@click.group("github")
def github() -> None:
    """GitHub 프로젝트 관리 (Issues, Projects, Milestones, Labels).

    \b
    omk github issue list --owner ej31 --repo my-repo
    omk github project list --owner ej31

    'gh'는 'github'의 단축 alias입니다.
    """
    pass
