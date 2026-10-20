# Code versions: storage design and browser checks

Each coding problem keeps its existing `deepcode-code:<slug>` localStorage key as the current, automatically saved working draft. Opening a problem reads that draft, so the latest edit is displayed by default. On the first load after this upgrade, all existing problem drafts in this browser are copied into version history as **Existing draft**, including problems that are not opened. Exact matches already in history are reused; the working-draft keys remain unchanged.

Running all tests automatically saves the submitted code as a snapshot only after the full suite passes. Failed/error runs, individual tests, and custom-only tests do not create submission snapshots. No name entry or manual save step is needed. Typing and unsuccessful attempts still update the working draft. Consecutive successful submissions of identical code reuse the newest snapshot; a successful submission of changed code (including a previously used approach) creates a new latest version. Existing snapshots and protective backups before reset/restore remain unchanged.

A completion marker (`deepcode-code-versions-migrated:v1`) prevents later typing, reloads, or intentional deletions from creating or restoring snapshots. If migration is interrupted or storage is full, it can safely retry on reload without duplicating completed copies. A visible banner reports incomplete migration.

Snapshots live separately at `deepcode-code-versions:<slug>`:

```json
{
  "schemaVersion": 1,
  "versions": [
    {
      "id": "UUID",
      "name": "Submitted code",
      "code": "exact submitted source text",
      "createdAt": "ISO-8601 timestamp"
    }
  ]
}
```

Versions are ordered newest first and never overwritten or automatically evicted. Legacy named versions remain readable. History previews do not touch the editor. Restoring copies a saved version into the current draft; restoring and resetting first preserve the current code if identical code is not already in history. Backups must succeed before the draft is replaced. Failed autosaves remain in memory through rerenders and navigation, with a visible warning and browser leave protection.

**Delete version** removes only the selected snapshot ID, leaving the working draft and other problems unchanged. **Undo delete** recovers the most recent deletion while History remains open. Deletes and undo operations re-read storage and only update the UI after a successful write. Deleting the last version leaves an empty schema envelope, so intentionally restored code remains protected from starter refresh.

Malformed/unsupported history or unavailable/full storage aborts version mutations. Runs still execute when version storage is unavailable; if a passing submission cannot be saved, a visible error reports the save failure while preserving its test result and completion status. Clearing browser site data removes drafts and versions; another browser/device/origin does not share them. This is not server-side synchronization. Playground sessions and System Design answers retain their existing behavior.

## Browser checks

The checks and screenshots below record the earlier save-on-submission behavior. The current pass-only policy is covered by the automated checks described above and by the code-version tests.

Tested in the Codex in-app browser against the feature worktree on `http://127.0.0.1:8851`, using isolated browser storage and test-only server state. No changes were made to the normal service on port 8848.

1. Typed an initial test attempt: the four existing history entries remained unchanged.
2. Ran all tests without entering a name: **Submitted code** appeared automatically, even though the attempt failed its tests.
3. Ran identical code again: the history count and newest snapshot timestamp stayed unchanged.
4. Edited and submitted a second attempt: a second automatic snapshot appeared at the top.
5. Selected the older automatic snapshot and clicked **Delete version**: exactly that entry disappeared; the newer snapshot and older legacy versions remained.
6. Clicked **Undo delete**: the removed snapshot returned in chronological order.
7. Loaded an old unsubmitted Top-p draft: **Existing draft** appeared automatically; a reload kept exactly one entry.
8. Prior checks verified reload into the latest draft, read-only preview, restore with automatic backup, reload of restored code, reset backup, and per-problem isolation.

The displayed code is synthetic browser-test content, not a verified solution to the K-means exercise.

### Automatic submission snapshots

![Code is saved on submission without a name field](history.png)

### Delete a selected version

![The selected version is removed with an undo action](delete-version.png)

### Restore preserves the previous draft

The earlier restore check (before the automatic-save UI update) verified preservation of unversioned edits:

![Automatic backup includes the unversioned experiment](restore-backup.png)

## Automated checks

- Focused code-version tests cover snapshots, submission timing and deduplication, typing without snapshots, deletion by ID, undo, storage failures, current-draft recovery, custom runs, and legacy compatibility.
- Full-suite results are recorded in the PR Test Plan. The focused version/migration suite passes all 23 tests.
- `node --check frontend/app.js` and `node --check frontend/code-versions.mjs`: passed.

### Existing drafts are preserved on upgrade

![An existing unsubmitted draft becomes the first saved version](existing-draft.png)
