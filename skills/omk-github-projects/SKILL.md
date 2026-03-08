---
name: omk-github-projects
description: Manages GitHub Projects-based WIs with the `gh` CLI.
---

# omk github-projects - Manage GitHub WIs with `gh`

GitHub-based WIs are not managed by separate wrappers like `omk gh`.
Always use the `gh` CLI and GitHub Projects directly.

## Execution Conditions

When the user requests "/oh-my-kanban:github-projects", "/omk:gh", or
"Manage GitHub WI", "Change project status with gh", "Operate tasks with GitHub Projects", etc.

## Basic Principles

- Distinguish between Repository Issues and Project Items.
- Title/Body/Comments/Closing are handled by `gh issue`.
- Board Status, Iteration, and Custom Fields are handled by `gh project`.
- `gh project item-edit` can only update **one field** at a time.
- Always verify permissions and target Project before working on GitHub Projects.

## Procedure

### 1. Authentication and Permissions Check

First, check the current authentication status:

```bash
gh auth status
```

If there's an issue, restore it with the following steps:

```bash
gh auth login
gh auth refresh -s project
```

Additional check:

```bash
gh repo view OWNER/REPO
```

- `gh project` commands require at least `project` scope.
- If the repo is visible but the project is not, organization Project permissions might be insufficient.
- In this case, guide the user to check org/project access permissions.

### 2. Confirm Target Repository and GitHub Project

First, decide whether to work based on the current repository.
If no repository is specified, prioritize the current git remote and `gh repo view` results.

Check Project candidates:

```bash
gh project list --owner OWNER --limit 100 --format json
```

Detailed check of the selected Project:

```bash
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project field-list PROJECT_NUMBER --owner OWNER --limit 100 --format json
```

If internal IDs required for write operations are missing, supplement with GraphQL:

Organization Project:

```bash
gh api graphql -f query='
query($owner: String!, $number: Int!) {
  organization(login: $owner) {
    projectV2(number: $number) {
      id
      title
      fields(first: 100) {
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

User Project:

```bash
gh api graphql -f query='
query($owner: String!, $number: Int!) {
  user(login: $owner) {
    projectV2(number: $number) {
      id
      title
      fields(first: 100) {
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

Values to confirm here:

- `PROJECT_NUMBER`: Project number entered by humans.
- `project id`: Internal node ID needed for `item-edit`.
- `field id`: Field IDs for Status, Iteration, Due Date, etc.
- `single select option id`: Option IDs for single-select fields like Status.

### 3. Match WI Data Model

In GitHub, do not confuse the following identifiers:

- Issue number: `123`
- Issue URL: `https://github.com/OWNER/REPO/issues/123`
- Project number: `7`
- Project item id: Internal item ID used within a Project.
- Project field id / option id: Internal IDs for status changes.

Practical principle:

- "Work content management" is based on issues.
- "Board position and status management" is based on project items.

### 4. Find Existing WI

Find candidates from the issue list:

```bash
gh issue list -R OWNER/REPO --state all \
  --limit 100 \
  --json number,title,state,assignees,labels,projectItems,url
```

If search is needed:

```bash
gh issue list -R OWNER/REPO --state all --search "keyword sort:updated-desc"
```

Single WI details:

```bash
gh issue view ISSUE_NUMBER -R OWNER/REPO --comments --json title,body,state,projectItems,url
```

If an issue already exists but is not in the Project, add it:

```bash
gh project item-add PROJECT_NUMBER --owner OWNER --url ISSUE_URL
```

### 5. Create New WI

For general development WIs, first create an issue:

```bash
gh issue create -R OWNER/REPO \
  --title "Title" \
  --body "Description" \
  --label "backend" \
  --assignee "@me"
```

If the Project title is clearly fixed to one, it can be linked directly upon creation:

```bash
gh issue create -R OWNER/REPO \
  --title "Title" \
  --body "Description" \
  --project "Project Title"
```

If the Project link is unclear or if there are multiple Projects with the same title under the owner, add it explicitly as below:

```bash
gh project item-add PROJECT_NUMBER --owner OWNER --url ISSUE_URL
```

If a draft card is needed instead of a repository issue, create it as a draft item:

```bash
gh project item-create PROJECT_NUMBER --owner OWNER \
  --title "Draft task" \
  --body "Memo or TODO"
```

### 6. Update Status and Custom Fields

First, secure the Project item and field identifiers.

Find project item:

```bash
gh issue view ISSUE_NUMBER -R OWNER/REPO --json projectItems
```

Or:

```bash
gh project item-list PROJECT_NUMBER --owner OWNER --limit 200 --format json
```

If the internal item ID is ambiguous, directly map issue number and item ID with GraphQL:

Organization Project:

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

User Project:

```bash
gh api graphql -f query='
query($owner: String!, $number: Int!) {
  user(login: $owner) {
    projectV2(number: $number) {
      id
      items(first: 200) {
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

Change single-select fields like Status:

```bash
gh project item-edit \
  --id ITEM_ID \
  --project-id PROJECT_ID \
  --field-id STATUS_FIELD_ID \
  --single-select-option-id STATUS_OPTION_ID
```

Change Iteration:

```bash
gh project item-edit \
  --id ITEM_ID \
  --project-id PROJECT_ID \
  --field-id ITERATION_FIELD_ID \
  --iteration-id ITERATION_ID
```

Change Text / Date / Number fields:

```bash
gh project item-edit --id ITEM_ID --project-id PROJECT_ID --field-id FIELD_ID --text "value"
gh project item-edit --id ITEM_ID --project-id PROJECT_ID --field-id FIELD_ID --date 2026-03-08
gh project item-edit --id ITEM_ID --project-id PROJECT_ID --field-id FIELD_ID --number 3
```

When clearing field values:

```bash
gh project item-edit --id ITEM_ID --project-id PROJECT_ID --field-id FIELD_ID --clear
```

Note:

- `gh project item-edit` does not modify the issue itself.
- If multiple fields need to be changed, execute the command multiple times.
- The **option id** is needed for `Status` options, not the option name.

### 7. Progress Log and Handoff

Log work progress in issue comments:

```bash
gh issue comment ISSUE_NUMBER -R OWNER/REPO --body "Progress / Decisions / Next Action"
```

Check recent comments:

```bash
gh issue view ISSUE_NUMBER -R OWNER/REPO --comments
```

Adjust labels, assignees, milestones:

```bash
gh issue edit ISSUE_NUMBER -R OWNER/REPO --add-label "blocked"
gh issue edit ISSUE_NUMBER -R OWNER/REPO --add-assignee " @me"
gh issue edit ISSUE_NUMBER -R OWNER/REPO --milestone "Sprint 12"
```

### 8. Complete, Reopen, and Clean Up

Complete:

```bash
gh issue close ISSUE_NUMBER -R OWNER/REPO --reason completed --comment "Completion summary"
```

Reopen:

```bash
gh issue reopen ISSUE_NUMBER -R OWNER/REPO --comment "Reason for reopening"
```

If an item needs to be archived from the board:

```bash
gh project item-archive PROJECT_NUMBER --owner OWNER --id ITEM_ID
```

Usually, the following sequence is safer:

1. Change Project Status to a Done-related status.
2. Add a completion comment to the issue.
3. Close the issue.
4. Archive the item only if required by team rules.

### 9. Final Verification

After working, check both:

```bash
gh issue view ISSUE_NUMBER -R OWNER/REPO --json title,state,assignees,labels,projectItems,url
gh project item-list PROJECT_NUMBER --owner OWNER --limit 200 --format json
```

Verification points:

- Is the correct issue linked to the Project?
- Are Status/Iteration/custom fields reflected as intended?
- Are comments/completion status not missing?

## Recommended Operating Patterns

- New development work: `gh issue create` -> `gh project item-add` -> `gh project item-edit`
- Progress log: `gh issue comment`
- Status transition: `gh project item-edit`
- Completion: `gh issue close`
- Reopen: `gh issue reopen` + readjust Status if necessary

## Precautions

- GitHub Projects often involve internal ID-based manipulation, so do not confuse `PROJECT_NUMBER` and `PROJECT_ID`.
- Status cannot be changed with only the repository issue number. The Project item ID is required.
- The `--project "Title"` method can cause confusion if there are multiple Projects with the same title under the owner.
- If securing internal IDs is ambiguous, use `gh api graphql` as a supplementary tool.
- Choose `organization(login: ...)` or `user(login: ...)` for GraphQL fallbacks based on the owner type.
- `gh project list`, `gh project field-list`, and `gh project item-list` have small default limits, so explicitly set `--limit` on larger boards.
- When dealing with org Projects, check repo permissions and project permissions separately.
- Even if the user requests `omk gh`, guide and process the actual execution with the `gh` CLI.
