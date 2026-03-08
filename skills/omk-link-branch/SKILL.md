---
name: omk-link-branch
description: Records the current git branch information as a Work Item comment and sets a WI link.
---

# omk link-branch - Record the Current Branch as a WI Link

Records the current git branch information as a Work Item comment and sets a WI link.

## Execution Steps

1. **Retrieve the current branch**

   ```bash
   git branch --show-current
   ```

   If there is no branch (detached HEAD): "No branch is available (detached HEAD)."

2. **Retrieve the remote repository URL (optional)**

   ```bash
   git remote get-url origin
   ```

   Continue even if it fails.

3. **Check the current WI**
   - If `focused_work_item_id` is missing:
     "No Work Item is linked.
     Please run /oh-my-kanban:focus first."

4. **Add a branch link comment to the WI**

   ```python
   # Use branch_name and repo_url after escaping to HTML-safe values
   mcp__plane__create_work_item_comment(
       project_id=<current project_id>,
       work_item_id=<focused_work_item_id>,
       comment_html=(
           "<h3>Branch Linked</h3><p><strong>Branch</strong>: "
           f"<code>{escaped_branch_name}</code><br>"
           + (
               f"<strong>Repository</strong>: {escaped_repo_url}<br>"
               if escaped_repo_url
               else "<strong>Repository</strong>: No remote repository URL<br>"
           )
           + "<em>Automatically recorded by omk</em></p>"
       )
   )
   ```

5. **Add a WI link (optional, when a repository URL is available)**

   ```python
   # Normalize SSH/scp remotes to HTTPS browser URLs and remove trailing .git
   normalized_repo_url = normalize_git_remote_to_https(repo_url)
   encoded_branch_name = quote(branch_name, safe="")
   branch_url = f"{normalized_repo_url}/tree/{encoded_branch_name}"
   mcp__plane__create_work_item_link(
       project_id=<current project_id>,
       work_item_id=<focused_work_item_id>,
       url=branch_url,
       title=f"Branch: {branch_name}"
   )
   ```

6. **Output the result**:

```text
[omk] Branch {branch_name} has been linked to {wi_identifier}.
  The following is displayed only if a link was created.
  Link: {branch_url}
```

## Notes

- If a git command fails, display an error and stop.
- If no remote repository URL is available, skip adding the WI link and also omit the link line from the result message.
- SSH/scp format remotes (`git@...`, `ssh://...`) are normalized to browser-accessible HTTPS URLs.
- Branch names are URL-encoded before being used in links.
- Duplicate recording prevention for the same branch is not implemented.
