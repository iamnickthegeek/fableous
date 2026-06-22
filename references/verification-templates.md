# Verification Templates — v8

Per-domain failable checks for the Fable Orchestrator v8. These checks are MANDATORY. A stage is NOT complete until ALL checks pass.

**How to use:** Run these checks using native Hermes tools (`terminal`, `execute_code`, `web_search`, `read_file`). Do NOT write custom Python scripts.

---

## Software Engineering

### Pre-implementation
- Read the relevant section of the codebase before writing a line.
- Identify all call sites of the function you're modifying.
- Check for existing tests that will break.

### Verification checks
1. **Tests pass**
   ```
   terminal(command="pytest -q", workdir=".")
   # Must return exit_code 0
   ```

2. **Build succeeds**
   ```
   terminal(command="npm run build", workdir=".")
   # Must return exit_code 0
   ```

3. **Type check passes**
   ```
   terminal(command="npx tsc --noEmit", workdir=".")
   # Must return exit_code 0
   ```

4. **Lint clean**
   ```
   terminal(command="npm run lint", workdir=".")
   # Must return exit_code 0
   ```

### What failure looks like
- Test exits non-zero
- Compilation error
- Type error
- Lint error

### What to do on failure
- Fix the code
- Re-run the check
- If the fix is large, return to the implementation stage

---

## Research / Knowledge Work

### Pre-write
- Gather sources before synthesizing.
- For each claim: what's the evidence? What would falsify it?
- Distinguish confirmed facts from inferences.

### Verification checks
1. **Source count**
   ```
   read_file(path="./stage1_research.md")
   # Must contain at least 3 cited sources
   ```

2. **URL verification**
   ```
   terminal(command="curl -s -o /dev/null -w '%{http_code}' URL", timeout=30)
   # Must return "200"
   ```
   Or use `web_search` to verify the URL is live.

3. **Source actually read**
   ```
   read_file(path="./stage1_research.md")
   # Every claim must trace to a source with "Source:" or "http"
   # If the source is a URL, verify it was fetched via web_extract or web_search
   ```

4. **Consistency check**
   ```
   read_file(path="./stage1_research.md")
   # Check that statistics don't contradict each other
   # Check that pricing data is consistent across sources
   ```

5. **Cross-run reconciliation (v8.0)**
   ```
   search_files(pattern="*.md", path=".", target="files")
   # Look for prior run outputs (FINAL.md, stage*.md) in the project directory
   # If found, read them and compare key stats against the current implementation
   # Flag discrepancies: same metric at different values, contradictory trends
   # Log in verification report as "Cross-Run Discrepancies" section
   # This check does NOT fail the stage — it flags discrepancies for the user
   ```

6. **Methodology consistency (v8.0)**
   ```
   read_file(path="./stage3_implementation.md")
   # Pick 3 key stats that appear across multiple sources
   # Verify they use the same measurement methodology:
   #   - Engagement rate: impressions-based vs. follower-based?
   #   - Sample size: comparable?
   #   - Time window: same period?
   # Flag stats where sources may measure different things but present as comparable
   # This check FAILS if 2+ stats have methodology mismatches that aren't acknowledged
   ```

### What failure looks like
- Claim cites "PostgreSQL documentation" but the docs don't mention it
- Statistic has no source
- Source cited but was not actually read
- URL returns 404
- Internal contradictions in the data
- Stats from different sources presented as comparable without acknowledging methodology differences (v8.0)

### What to do on failure
- Re-run the research stage for the specific claim
- Mark the claim as unverified if no source exists
- Remove the claim or downgrade it to "reported but not verified"

---

## Data Analysis

### Pre-write
- Understand the data shape before writing analysis.
- State your hypothesis before computing.
- Check for nulls, duplicates, outliers first.

### Verification checks
1. **Data quality**
   ```
   execute_code(code="""
   import pandas as pd
   df = pd.read_csv('data.csv')
   assert df.isnull().sum().sum() == 0, f'Nulls: {df.isnull().sum().sum()}'
   assert df.duplicated().sum() == 0, f'Duplicates: {df.duplicated().sum()}'
   print('Data quality check passed')
   """)
   ```

2. **Outlier check**
   ```
   execute_code(code="""
   import pandas as pd
   df = pd.read_csv('data.csv')
   q1 = df['value'].quantile(0.25)
   q3 = df['value'].quantile(0.75)
   iqr = q3 - q1
   outliers = df[(df['value'] < q1 - 1.5*iqr) | (df['value'] > q3 + 1.5*iqr)]
   assert len(outliers) < len(df) * 0.05, f'Too many outliers: {len(outliers)}'
   print('Outlier check passed')
   """)
   ```

3. **Hypothesis test**
   ```
   execute_code(code="""
   # Run the hypothesis test the analyst stated
   # Verify the p-value, confidence interval, etc.
   """)
   ```

### What failure looks like
- Assertion fails
- Data shape is not what was assumed
- Nulls or outliers present
- Hypothesis test gives unexpected results

### What to do on failure
- Clean the data
- Adjust the analysis
- Re-run the check

---

## Writing / Content Creation

### Pre-write
- Define audience and constraints.
- Set tone and style guidelines.
- Create a brief/spec.

### Verification checks
1. **Brief compliance**
   ```
   read_file(path="./stage3_implement.md")
   # Must match the brief (word count, sections, tone)
   # Check for required sections
   ```

2. **Fact check**
   ```
   read_file(path="./stage3_implement.md")
   # Every load-bearing claim must trace to a source from stage1_research.md
   # Verify claims with web_search if needed
   ```

3. **Plagiarism check**
   ```
   # Search for unique phrases from the output
   web_search(query="'exact phrase from output'", limit=5)
   # Must not return exact matches from other sources
   ```

4. **Audience check**
   ```
   read_file(path="./stage3_implement.md")
   # Verify tone matches audience tier (technical, executive, general)
   ```

### What failure looks like
- Output doesn't match the brief
- Tone is wrong for the audience
- Claims are unsupported
- Plagiarism detected

### What to do on failure
- Rewrite the specific section
- Re-run the check
- Flag the gap to the user if it can't be fixed

---

## Long-Running / Multi-Session

### Pre-write
- Define done criteria upfront.
- Create a work log.
- Set session boundaries.

### Verification checks
1. **Done criteria**
   ```
   read_file(path="WORK_LOG.md")
   # Must contain clear, testable done criteria
   # "Looks good" is NOT a criterion
   ```

2. **Work log up to date**
   ```
   read_file(path="WORK_LOG.md")
   # Must contain entries for all completed stages
   # Must contain decisions, failures, open items
   ```

3. **Prior checks still pass**
   ```
   # Re-run the verification checks for all completed stages
   # If a later fix invalidated a prior stage, re-run that stage
   ```

### What failure looks like
- Done criteria are vague ("looks good")
- Work log is missing
- A prior stage's check would fail after a later fix

### What to do on failure
- Write clear done criteria
- Update the work log
- Re-run prior checks

---

## Generic Verification

When a stage has no obvious domain-specific check, use one of these:

### File existence check
```
terminal(command="ls -la output.md")
# Must exist and have non-zero size
```

### Content shape check
```
terminal(command="grep -q '## Conclusion' output.md")
# Must return exit_code 0
```

### Diff check
```
terminal(command="diff expected.md output.md")
# Must return exit_code 0 (or acceptable differences)
```

### The minimum viable check

If a stage genuinely has no failable check, say so explicitly:

> "Stage N has no failable check. Output is unverified."

This makes the gap visible downstream. It is better than a fake check that always passes.

---

## Verification Checklist

Before declaring any stage complete, answer these:

- [ ] Did you define the verification checks before delegating the stage?
- [ ] Did you run ALL verification checks?
- [ ] Did ALL checks pass?
- [ ] If a check failed, did you fix the issue or re-run the stage?
- [ ] Did you log the verification results in the work log?

**Do NOT proceed to the next stage until ALL boxes are checked.**
