---
name: omk-link-work-item
description: Manually links the current session to a specific Plane Work Item. Use this when auto-linking has failed or you want to link to an existing Work Item.
---

Please manually link the current oh-my-kanban session to a specific Plane Work Item.

## Phase 2 and later (official command)

```bash
omk hooks link --work-item-id <WORK_ITEM_ID>
```

> **Note**: The above command is activated in Phase 2.

---

## Currently available alternative method

**Step 1: Check the session ID**

```bash
omk hooks status
```

Copy the `session_id` value from the output (e.g., `a1b2c3d4-...`).

**Step 2: Edit the session file directly**

```bash
# Session file path
~/.config/oh-my-kanban/sessions/<SESSION_ID>.json
```

Open the file and add the Work Item ID to the `plane_context.work_item_ids` array:

```json
{
  "plane_context": {
    "project_id": "keep existing value",
    "work_item_ids": ["work-item-id-to-add"],
    "module_id": null
  }
}
```

**Step 3: Verify the change**

```bash
omk hooks status
```

Once the Work Item ID appears in the session status, the link is complete. When the session ends, a work summary will be added as a comment to that Work Item.
