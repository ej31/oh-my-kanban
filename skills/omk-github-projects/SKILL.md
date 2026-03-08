---
name: omk-github-projects
description: GitHub Projects 기반 WI를 `gh` CLI로 관리한다.
---

# omk github-projects — GitHub WI를 `gh`로 관리

GitHub 기반 WI는 `omk gh` 같은 별도 래퍼로 관리하지 않는다.
반드시 `gh` CLI와 GitHub Projects를 직접 사용한다.

## 실행 조건

사용자가 "/oh-my-kanban:github-projects", "/omk:gh" 또는
"GitHub WI 관리해줘", "gh로 프로젝트 상태 바꿔줘", "GitHub Projects로 태스크 운영해줘" 등을 요청한 경우.

## 기본 원칙

- 저장소 이슈(Issue)와 프로젝트 아이템(Project Item)은 구분한다
- 제목/본문/댓글/닫기는 `gh issue`
- 보드 상태(Status), Iteration, 커스텀 필드는 `gh project`
- `gh project item-edit`는 한 번에 **한 필드만** 갱신할 수 있다
- GitHub Projects 작업 전에는 항상 권한과 대상 Project를 먼저 확인한다

## 절차

### 1. 인증과 권한 확인

먼저 현재 인증 상태를 확인한다:

```bash
gh auth status
```

문제가 있으면 아래 순서로 복구한다:

```bash
gh auth login
gh auth refresh -s project
```

추가 점검:

```bash
gh repo view OWNER/REPO
```

- `gh project` 계열은 최소 `project` scope가 필요하다
- repo는 보이는데 project가 안 보이면 조직 Project 권한이 부족할 수 있다
- 이 경우 사용자에게 org/project 접근 권한 확인을 안내한다

### 2. 대상 저장소와 GitHub Project 확정

현재 저장소 기준으로 작업할지 먼저 정한다.
저장소가 명시되지 않았으면 현재 git remote와 `gh repo view` 결과를 우선 사용한다.

Project 후보 확인:

```bash
gh project list --owner OWNER --format json
```

선택한 Project 상세 확인:

```bash
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project field-list PROJECT_NUMBER --owner OWNER --format json
```

쓰기 작업에 필요한 내부 ID가 부족하면 GraphQL로 보강한다:

```bash
gh api graphql -f query='
query($owner: String!, $number: Int!) {
  organization(login: $owner) {
    projectV2(number: $number) {
      id
      title
      fields(first: 50) {
        nodes {
          ... on ProjectV2Field { id name dataType }
          ... on ProjectV2SingleSelectField { id name options { id name } }
          ... on ProjectV2IterationField {
            id
            name
            configuration { iterations { id title startDate } }
          }
        }
      }
    }
  }
}' -f owner=OWNER -F number=PROJECT_NUMBER
```

여기서 확인해야 하는 값:

- `PROJECT_NUMBER`: 사람이 입력하는 프로젝트 번호
- `project id`: `item-edit`에 필요한 내부 node ID
- `field id`: Status, Iteration, Due Date 등 필드 ID
- `single select option id`: Status 같은 단일 선택 필드의 옵션 ID

### 3. WI 데이터 모델 맞추기

GitHub에서는 아래 식별자를 혼동하면 안 된다:

- Issue 번호: `123`
- Issue URL: `https://github.com/OWNER/REPO/issues/123`
- Project number: `7`
- Project item id: Project 안에서 쓰는 내부 item ID
- Project field id / option id: 상태 변경용 내부 ID

실무 원칙:

- "작업 내용 관리"는 issue를 기준으로 본다
- "보드 위치와 상태 관리"는 project item을 기준으로 본다

### 4. 기존 WI 찾기

이슈 목록에서 후보를 찾는다:

```bash
gh issue list -R OWNER/REPO --state all \
  --json number,title,state,assignees,labels,projectItems,url
```

검색이 필요하면:

```bash
gh issue list -R OWNER/REPO --state all --search "keyword sort:updated-desc"
```

단일 WI 상세:

```bash
gh issue view ISSUE_NUMBER -R OWNER/REPO --comments --json title,body,state,projectItems,url
```

이미 issue는 있는데 Project에 없으면 추가한다:

```bash
gh project item-add PROJECT_NUMBER --owner OWNER --url ISSUE_URL
```

### 5. 새 WI 생성

일반적인 개발 WI는 먼저 issue를 만든다:

```bash
gh issue create -R OWNER/REPO \
  --title "제목" \
  --body "설명" \
  --label "backend" \
  --assignee "@me"
```

Project 제목이 명확하게 하나로 고정돼 있다면 생성 시 바로 연결할 수 있다:

```bash
gh issue create -R OWNER/REPO \
  --title "제목" \
  --body "설명" \
  --project "Project Title"
```

Project 연결이 불명확하거나 owner에 같은 제목 Project가 여러 개면 아래처럼 명시적으로 추가한다:

```bash
gh project item-add PROJECT_NUMBER --owner OWNER --url ISSUE_URL
```

저장소 issue가 아니라 초안 카드가 필요하면 draft item으로 생성한다:

```bash
gh project item-create PROJECT_NUMBER --owner OWNER \
  --title "Draft task" \
  --body "메모 또는 TODO"
```

### 6. 상태와 커스텀 필드 갱신

먼저 Project item과 field 식별자를 확보한다.

프로젝트 아이템 찾기:

```bash
gh issue view ISSUE_NUMBER -R OWNER/REPO --json projectItems
```

또는

```bash
gh project item-list PROJECT_NUMBER --owner OWNER --format json
```

내부 item ID가 애매하면 GraphQL로 issue 번호와 item ID를 직접 매핑한다:

```bash
gh api graphql -f query='
query($owner: String!, $number: Int!) {
  organization(login: $owner) {
    projectV2(number: $number) {
      id
      items(first: 100) {
        nodes {
          id
          content {
            ... on Issue { number title url }
            ... on PullRequest { number title url }
            ... on DraftIssue { title body }
          }
        }
      }
    }
  }
}' -f owner=OWNER -F number=PROJECT_NUMBER
```

Status 같은 단일 선택 필드 변경:

```bash
gh project item-edit \
  --id ITEM_ID \
  --project-id PROJECT_ID \
  --field-id STATUS_FIELD_ID \
  --single-select-option-id STATUS_OPTION_ID
```

Iteration 변경:

```bash
gh project item-edit \
  --id ITEM_ID \
  --project-id PROJECT_ID \
  --field-id ITERATION_FIELD_ID \
  --iteration-id ITERATION_ID
```

Text / Date / Number 필드 변경:

```bash
gh project item-edit --id ITEM_ID --project-id PROJECT_ID --field-id FIELD_ID --text "value"
gh project item-edit --id ITEM_ID --project-id PROJECT_ID --field-id FIELD_ID --date 2026-03-08
gh project item-edit --id ITEM_ID --project-id PROJECT_ID --field-id FIELD_ID --number 3
```

필드 값을 지울 때:

```bash
gh project item-edit --id ITEM_ID --project-id PROJECT_ID --field-id FIELD_ID --clear
```

주의:

- `gh project item-edit`는 issue 자체를 수정하지 않는다
- 필드 여러 개를 바꿔야 하면 명령을 여러 번 실행한다
- `Status` 옵션 이름이 아니라 **option id**가 필요하다

### 7. 진행 기록과 핸드오프

작업 기록은 issue 댓글에 남긴다:

```bash
gh issue comment ISSUE_NUMBER -R OWNER/REPO --body "진행 상황 / 결정 사항 / 다음 액션"
```

최근 댓글 확인:

```bash
gh issue view ISSUE_NUMBER -R OWNER/REPO --comments
```

라벨, 담당자, 마일스톤 조정:

```bash
gh issue edit ISSUE_NUMBER -R OWNER/REPO --add-label "blocked"
gh issue edit ISSUE_NUMBER -R OWNER/REPO --add-assignee "@me"
gh issue edit ISSUE_NUMBER -R OWNER/REPO --milestone "Sprint 12"
```

### 8. 완료, 재개, 정리

완료 처리:

```bash
gh issue close ISSUE_NUMBER -R OWNER/REPO --reason completed --comment "완료 요약"
```

재개:

```bash
gh issue reopen ISSUE_NUMBER -R OWNER/REPO --comment "재개 사유"
```

보드에서 아이템을 archive 해야 하면:

```bash
gh project item-archive PROJECT_NUMBER --owner OWNER --id ITEM_ID
```

보통은 아래 순서가 안전하다:

1. Project Status를 Done 계열로 변경
2. issue에 완료 댓글 추가
3. issue close
4. 팀 규칙상 필요할 때만 item archive

### 9. 최종 검증

작업 후에는 아래 둘 다 확인한다:

```bash
gh issue view ISSUE_NUMBER -R OWNER/REPO --json title,state,assignees,labels,projectItems,url
gh project item-list PROJECT_NUMBER --owner OWNER --format json
```

검증 포인트:

- 올바른 issue가 Project에 연결되었는가
- Status/Iteration/custom field가 의도대로 반영되었는가
- 댓글/완료 상태가 누락되지 않았는가

## 권장 운영 패턴

- 신규 개발 작업: `gh issue create` -> `gh project item-add` -> `gh project item-edit`
- 진행 기록: `gh issue comment`
- 상태 전환: `gh project item-edit`
- 완료 처리: `gh issue close`
- 재개: `gh issue reopen` + 필요 시 Status 재조정

## 주의사항

- GitHub Projects는 내부 ID 기반 조작이 많아서 `PROJECT_NUMBER`와 `PROJECT_ID`를 혼동하지 않는다
- 저장소 issue 번호만으로는 Status 변경이 안 된다. Project item ID가 필요하다
- `--project "제목"` 방식은 동명이인 Project가 있으면 혼동될 수 있다
- 내부 ID 확보가 애매하면 `gh api graphql`을 보조 수단으로 사용한다
- org Project를 다룰 때는 repo 권한과 project 권한을 별도로 확인한다
- 사용자가 `omk gh`를 요청해도 실제 실행은 `gh` CLI로 안내하고 처리한다
