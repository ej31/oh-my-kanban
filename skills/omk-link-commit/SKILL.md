---
name: omk-link-commit
description: Manually records a specific commit hash as a comment on the current Work Item.
---

# omk link-commit \<commit-hash\> - Manually Link a Commit to the Current WI

Manually records a specific commit hash as a comment on the current Work Item.

## Usage Examples

```bash
omk link-commit a1b2c3d
omk link-commit a1b2c3d7f9e2b4c6d8e0f1a2b3c4d5e6f7a8b9c0
```

## Execution Steps

1. **Check the current WI**
   - If `focused_work_item_id` is missing:
     "No Work Item is linked.
     Please run /oh-my-kanban:focus first."

2. **Retrieve commit information (optional)**
   - Use `git show --oneline -s <commit-hash>` to retrieve the commit message (continue even if it fails).

3. **Add a comment to the WI**

   ```python
   mcp__plane__create_work_item_comment(
       project_id=<current project_id>,
       work_item_id=<focused_work_item_id>,
       comment_html=(
           "<h3>Commit Record</h3>"
           "<p><strong>Commit</strong>: <code>{hash_short}</code><br>"
           "<strong>Message</strong>: {sanitize_comment(commit_msg)}<br>"
           "<em>Manually recorded by omk</em></p>"
       )
   )
   ```

4. **Output the result**:

```text
[omk] Commit {hash_short} has been recorded to {wi_identifier}.
```

## Notes

- Warn if the hash is fewer than 7 characters (but continue processing).
- Even if the git command fails, continue adding the comment.
- Duplicate commit prevention is not implemented (searching Plane's comment list is costly).
