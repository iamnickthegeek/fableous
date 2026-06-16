# Timeout Recovery Recipe for Fable v6

## When this applies

A `delegate_task` stage call returns `status: timeout` after the maximum duration (typically 600s), but the subagent may have already written its deliverables to disk before the timeout fired. This is common for Verify, Critique, and Fix stages that perform many file operations or API calls.

## Do not immediately retry

Re-running the stage can:
- Waste tokens and time.
- Overwrite valid outputs that were produced before the timeout.
- Mask the fact that the stage actually succeeded.

## Recovery recipe

1. **Locate the expected output file.** Use the stage prompt to know where it should be saved (e.g., `stage4_verification.md`, `stage5_critique.md`, `stage5_fixes.md`).

2. **Check if it exists and is complete.** Use `read_file` or `search_files`.

3. **If the file is complete:**
   - Verify it using the correct model family (especially for Verify/Critique/Consolidate).
   - For cross-family stages, use the terminal method:
     ```bash
     hermes chat -q 'READ_FILE_PROMPT' -m MODEL --provider PROVIDER -Q -t file
     ```
   - Update `WORK_LOG.md` to note the timeout and the recovered output.

4. **If the file is incomplete or missing:**
   - Determine which parts were done. Inspect directories, logs, and partial files.
   - Complete missing parts manually or re-run only the missing work.
   - Only re-run the whole stage as a last resort.

## Concrete example

During Stage 4 verification of the author variant, `delegate_task` timed out after 600s. The verification report had already been written:

```text
/home/case/.hermes/projects/royalty-ronin/stage4_verification_authors.md
```

Recovery:

```bash
hermes chat -q 'Read /home/case/.hermes/projects/royalty-ronin/stage4_verification_authors.md and the generated lead sheets. Confirm the verification checks are sound and the outputs are internally consistent. At the top write: [MODEL: deepseek-v4-pro, PROVIDER: opencode-go]. Report pass/fail.' -m deepseek-v4-pro --provider opencode-go -Q -t file
```

Result: verification passed. The work log was updated to reflect the timeout and the recovered, cross-family-verified output.

## Timeout + model mismatch together

If a timeout also coincides with a model mismatch (metadata reports the wrong model), recover the file first, then re-verify via terminal with the correct model. See `references/model-mismatch-recovery.md`.

## What to log

In `WORK_LOG.md` record:
- The stage that timed out.
- The file path that was recovered.
- Whether the recovered output was re-verified and on which model.
- Any missing pieces completed by the parent.
