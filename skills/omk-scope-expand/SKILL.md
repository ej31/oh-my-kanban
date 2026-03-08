---
name: omk-scope-expand
description: Explicitly expands the current session's work scope. Use this to add a new work topic to the current session scope in order to prevent false-positive session drift warnings.
---

Please expand the current session's work scope. Use this when unexpected related work has been added and a drift warning is triggered, or when you want to explicitly declare the scope.

## Phase 2 and later (official command)

```bash
omk hooks expand-scope --topic "<new work topic>"
```

> **Note**: The above command is activated in Phase 2.

---

## Currently available alternative method

**Step 1: Check the session ID**

```bash
omk hooks status
```

Copy the `session_id` value from the output.

**Step 2: Add the topic to `expanded_topics` in the session file**

```bash
# Session file path
~/.config/oh-my-kanban/sessions/<SESSION_ID>.json
```

Open the file and add the new topic to the `scope.expanded_topics` array:

```json
{
  "scope": {
    "expanded_topics": ["existing topic", "new work topic to add"]
  }
}
```

**Step 3: Verify the change**

```bash
omk hooks status
```

Once the added topic appears in `expanded_topics`, you are done.
Work related to that topic will no longer be detected as drift.

**Check the full current session scope**

```bash
omk hooks status
```
