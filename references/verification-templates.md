# Verification Templates

Per-domain failable checks for the Fable Orchestrator.

## Software Engineering

### Pre-write
- Read the relevant section of the codebase before writing a line
- Identify all call sites of the function you're modifying
- Check for existing tests that will break

### Verification check
```bash
# Must run and pass
pytest -q
# Or: npm test
# Or: cargo test
```

### What failure looks like
- Test exits non-zero
- Compilation error
- Type error (TypeScript, Rust, etc.)
- Lint error (eslint, clippy, etc.)

### What to do on failure
- Fix the code
- Re-run the check
- If the fix is large, return to the implementation stage

## Research / Knowledge Work

### Pre-write
- Gather sources before synthesizing
- For each claim: what's the evidence? what would falsify it?
- Distinguish confirmed facts from inferences

### Verification check
- Every load-bearing claim must have a source citation
- The source must have been actually read (not assumed from training data)
- If the source is a URL, it must have been fetched via `web_extract` or `web_search`

### What failure looks like
- Claim cites "PostgreSQL documentation" but the docs don't mention it
- Statistic has no source
- Source cited but was not actually read

### What to do on failure
- Re-run the research stage for the specific claim
- Mark the claim as unverified if no source exists
- Remove the claim or downgrade it to "reported but not verified"

## Data Analysis

### Pre-write
- Understand the data shape before writing analysis
- State your hypothesis before computing
- Check for nulls, duplicates, outliers first

### Verification check
```python
# Run in execute_code
import pandas as pd

df = pd.read_csv('data.csv')
assert df.isnull().sum().sum() == 0, "Nulls found"
assert df.duplicated().sum() == 0, "Duplicates found"
assert (df['value'] < 0).sum() == 0, "Negative values found"
```

### What failure looks like
- Assertion fails
- Data shape is not what was assumed
- Nulls or outliers present

### What to do on failure
- Clean the data
- Adjust the analysis
- Re-run the check

## Writing / Content Creation

### Pre-write
- Define audience and constraints
- Set tone and style guidelines
- Create a brief/spec

### Verification check
- Output matches the brief/spec
- Word count or length constraints met
- Plagiarism check if needed (via web search for unique phrases)
- Fact check: load-bearing claims trace to sources

### What failure looks like
- Output doesn't match the brief
- Tone is wrong for the audience
- Claims are unsupported

### What to do on failure
- Rewrite the specific section
- Re-run the check
- Flag the gap to the user if it can't be fixed

## Long-Running / Multi-Session

### Pre-write
- Define done criteria upfront
- Create a work log
- Set session boundaries

### Verification check
- Done criteria are written and testable
- Work log is up to date
- All prior stages' checks still pass

### What failure looks like
- Done criteria are vague ("looks good")
- Work log is missing
- A prior stage's check would fail after a later fix

### What to do on failure
- Write clear done criteria
- Update the work log
- Re-run prior checks

## Generic Verification

When a stage has no obvious domain-specific check, use one of these:

### File existence check
```bash
ls -la output.md
# Must exist and have non-zero size
```

### Content shape check
```bash
# Must contain expected section
grep -q "## Conclusion" output.md
```

### Diff check
```bash
# Compare against expected output
diff expected.md output.md
```

### The minimum viable check
If a stage genuinely has no failable check, say so explicitly:

> "Stage N has no failable check. Output is unverified."

This makes the gap visible downstream. It is better than a fake check
that always passes.
