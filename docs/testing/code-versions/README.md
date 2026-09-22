# Code versions: storage design and browser checks

Each coding problem keeps its existing `deepcode-code:<slug>` localStorage key as the current, automatically saved working draft. Opening a problem reads that draft, so existing saved code needs no migration and the latest edit is displayed by default.

Named snapshots live separately at `deepcode-code-versions:<slug>`:

```json
{
  "schemaVersion": 1,
  "versions": [
    {
      "id": "UUID",
      "name": "Vectorized distances",
      "code": "exact source text",
      "createdAt": "ISO-8601 timestamp"
    }
  ]
}
```

Versions are ordered newest first and never overwritten or automatically evicted. Duplicate names are allowed. History previews do not touch the editor. Restoring copies a saved version into the current draft; restoring and resetting first preserve the current code if identical code is not already in history. Backups must succeed before the draft is replaced. Malformed/unsupported history or exhausted browser storage causes the operation to stop, preserving existing data. Empty drafts and restored old starters survive reopening. Failed autosaves remain in memory across UI rerenders and problem navigation, keep a visible warning, and trigger the normal browser leave warning until persistence succeeds.

This retains the app's browser-local storage model: clearing site data removes drafts and versions, and another browser/device/origin does not share them. This is not server-side synchronization. Playground sessions and System Design answers keep their existing storage/UI.

## Browser checks

Tested in the Codex in-app browser against the feature worktree on `http://127.0.0.1:8851`, using isolated browser storage and test-only server state. No changes were made to the normal service on port 8848.

1. Entered a loop-based distance helper and saved **Loop baseline**.
2. Replaced the editor with a broadcasting helper and saved **Vectorized distances**. Both versions remained, newest first.
3. Reloaded: the broadcasting draft opened automatically.
4. Added an unversioned experiment comment. Previewed the older version, then closed History: the current draft still contained the experiment.
5. Restored **Loop baseline**. The editor showed the older code; History contained **Before restoring Loop baseline** with the entire experiment draft. Reloading retained the restored code.
6. Added another draft comment and reset. The editor returned to the starter; History contained **Before reset**, including the comment.
7. Switched to Top-p sampling: its history was empty. Returning to K-means retained all four versions.
8. No browser warning/error logs were recorded during these checks.

The helper code is synthetic test content, not a submitted solution to the K-means exercise.

### Two saved approaches

![Named versions, newest first, with a read-only preview](history.png)

### Restore preserves the previous draft

![Automatic backup includes the unversioned experiment](restore-backup.png)

## Automated checks

- `uv run --locked python -m unittest discover -s tests -p test_code_versions.py`: 10 passed.
- `uv run --locked python -m unittest discover -s tests -p test_static_ui.py`: 42 passed.
- `uv run --locked python -m unittest discover -s tests`: all 394 tests passed (95.8 s). Run with local socket permission because an architecture test starts a loopback HTTP server.
- `node --check frontend/app.js` and `node --check frontend/code-versions.mjs`: passed.
