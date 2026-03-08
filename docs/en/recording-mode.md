# Recording Mode

oh-my-kanban automatically posts comments to Plane Work Items when sessions end. The `upload_level` setting controls what gets uploaded.

## Upload Levels

| Level | Description |
|-------|-------------|
| `none` | No comments are uploaded. Only local session files are saved. |
| `metadata` | (Default) Records statistics, modified files, and scope summary. Shares essential info while protecting privacy. |
| `full` | Uploads detailed comments including timeline events. All session activity is recorded. |

## Configuration

### CLI

```bash
omk config set upload_level metadata
omk config set upload_level full
omk config set upload_level none
```

### Config File

`~/.config/oh-my-kanban/config.toml`:

```toml
[default]
upload_level = "metadata"
```

### Environment Variable

```bash
export OMK_UPLOAD_LEVEL=full
```

### Using Presets

```bash
# Minimal (no upload)
omk config preset apply minimal

# Verbose recording
omk config preset apply verbose
```

## Comment Examples by Mode

### metadata Mode

```markdown
## omk Session End

**Goal**: OAuth refactoring

**Statistics**
- Prompts: 12
- Files modified: 5
- Drift warnings: 1

**Modified Files**
- `src/auth/oauth.py`
- `tests/test_oauth.py`
```

### full Mode

Includes everything from metadata mode plus timeline events.

```markdown
**Timeline**
- `2026-01-01T10:00:00` [scope_init] Session started
- `2026-01-01T10:05:00` [prompt] Implementing OAuth token refresh
- `2026-01-01T10:15:00` [drift_detected] Drift detected
- `2026-01-01T10:30:00` [prompt] Session ended normally
```

## Notes

- In `none` mode, session state is still saved locally. Only Plane API calls are skipped.
- Invalid `upload_level` values automatically fall back to `none` (safe default — no upload).
- Changes to `upload_level` typically take effect at session end, since `session_end` reloads config before uploading. Avoid changing `upload_level` mid-session if you need predictable upload behavior.
