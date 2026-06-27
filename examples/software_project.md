# Example: Software Project

## Task

"Build a FastAPI authentication service with JWT tokens, rate limiting, and user registration."

## Execution

### Step 1: Create the stage map

```
todo(todos=[
  {id: "stage-1", content: "Stage 1: Research — FastAPI auth patterns, JWT libraries, rate limiting strategies", status: "pending"},
  {id: "stage-2", content: "Stage 2: Plan — architecture, endpoints, database schema", status: "pending"},
  {id: "stage-3", content: "Stage 3: Implement — write code, tests, docs", status: "pending"},
  {id: "stage-4", content: "Stage 4: Verify — run tests, check coverage, lint", status: "pending"},
  {id: "stage-5", content: "Stage 5: Critique — security review, performance check", status: "pending"},
  {id: "stage-6", content: "Stage 6: Consolidate — canonical README + code", status: "pending"},
])
```

### Step 2: Execute Stage 1 (Research)

Delegate to `deepseek-v0.4.0-flash` via Opencode Go.

Prompt:
```
[FABLE STAGE: Research]

Task: Build a FastAPI auth service with JWT, rate limiting, and registration.

GUARDRAILS:
- If you cite benchmarks, label the exact source and date.
- Do not present vendor claims as verified facts.
- Save your complete output to: ./stage1_research.md
- At the top of your output, write exactly: [MODEL: deepseek-v0.4.0-flash, PROVIDER: opencode-go]

INSTRUCTIONS:
- Research FastAPI auth patterns (OAuth2, JWT, session-based).
- Research rate limiting strategies (Redis, in-memory, middleware).
- Research password hashing (bcrypt, Argon2).
- Verify library documentation URLs are live.
- Save to ./stage1_research.md.
```

### Step 3: Execute Stage 2 (Plan)

Delegate to `glm-5.1` via Opencode Go.

Prompt:
```
[FABLE STAGE: Plan]

Task: Build a FastAPI auth service with JWT, rate limiting, and registration.

Context:
- Research summary: [from stage1_research.md]

GUARDRAILS:
- Segment audience into 3 tiers (solo dev, small team, enterprise).
- Map recommendations to tiers.
- Include "Methodology & Caveats".
- Save your complete output to: ./stage2_plan.md
- At the top of your output, write exactly: [MODEL: glm-5.1, PROVIDER: opencode-go]

INSTRUCTIONS:
- Define architecture: directory structure, modules, dependencies.
- List all endpoints: /register, /login, /refresh, /protected.
- Define database schema: users table, token blacklist.
- Define rate limiting rules: requests per minute per IP/user.
- Include security considerations: CORS, HTTPS, input validation.
- Save to ./stage2_plan.md.
```

### Step 4: Execute Stage 3 (Implement)

Delegate to `kimi-k2.7-code` via Opencode Go.

Depends on Stage 1 and Stage 2.

Prompt:
```
[FABLE STAGE: Implement]

Task: Build a FastAPI auth service with JWT, rate limiting, and registration.

Context:
- Research: [from stage1_research.md]
- Plan: [from stage2_plan.md]

GUARDRAILS:
- Every claim must trace to a source.
- Write tests before or alongside implementation.
- Save your complete output to: ./stage3_implement.md
- At the top of your output, write exactly: [MODEL: kimi-k2.7-code, PROVIDER: opencode-go]

INSTRUCTIONS:
- Create the FastAPI app with all endpoints.
- Implement JWT token generation and validation.
- Implement rate limiting middleware.
- Write tests with pytest (coverage > 80%).
- Save code to ./app/ directory.
- Save tests to ./tests/ directory.
- Save to ./stage3_implement.md.
```

### Step 5: Execute Stage 4 (Verify)

**Verification checks (mandatory):**

1. Tests pass:
```
terminal(command="pytest -q --cov=app --cov-report=term-missing", workdir=".")
# Must return exit_code 0
# Coverage must be >= 80%
```

2. Type check:
```
terminal(command="mypy app/", workdir=".")
# Must return exit_code 0
```

3. Lint:
```
terminal(command="flake8 app/ tests/", workdir=".")
# Must return exit_code 0
```

4. Security check:
```
terminal(command="bandit -r app/", workdir=".")
# Must return no HIGH or MEDIUM severity issues
```

If ANY check fails, the stage is NOT complete. Fix and re-run.

Delegate to `deepseek-v0.4.0-pro` via Opencode Go.

**Critical:** Must be a different model family than Implement (DeepSeek vs Kimi).

After completion:
- Run verification checks
- Verify model tag
- Update todo
- Update WORK_LOG.md

### Step 6: Execute Stage 5 (Critique)

Delegate to `glm-5.1` via Opencode Go.

**Critical:** Must be a different model family than Implement (GLM vs Kimi).

Prompt:
```
[FABLE STAGE: Critique]

Task: Build a FastAPI auth service with JWT, rate limiting, and registration.

Context:
- Implementation: [from stage3_implement.md]
- Verification: [from stage4_verify.md]

GUARDRAILS:
- Check for confirmation bias.
- Verify security considerations.
- Assess performance.
- Identify 3+ concrete weaknesses.
- Save your complete output to: ./stage5_critique.md
- At the top of your output, write exactly: [MODEL: glm-5.1, PROVIDER: opencode-go]

INSTRUCTIONS:
- Review the implementation for security flaws.
- Check for SQL injection, XSS, CSRF.
- Assess rate limiting robustness.
- Check JWT secret handling.
- Identify 3+ concrete weaknesses.
- Save to ./stage5_critique.md.
```

### Step 7: Execute Stage 6 (Consolidate)

Delegate to `deepseek-v0.4.0-pro` via Opencode Go.

Read all prior stage outputs. Apply corrections. Produce FINAL README and code.

After completion:
- Verify model tag
- Verify FINAL.md exists
- Verify all verification corrections applied
- Verify all critique fixes addressed or flagged
- Update todo
- Update WORK_LOG.md
- Mark task complete

## Expected Output

```
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── auth.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── rate_limit.py
├── tests/
│   ├── test_auth.py
│   ├── test_rate_limit.py
│   └── conftest.py
├── stage1_research.md
├── stage2_plan.md
├── stage3_implement.md
├── stage4_verify.md
├── stage5_critique.md
├── FINAL.md
└── WORK_LOG.md
```

## Time Estimate

- Stages 1-2: 15 minutes (can run in parallel)
- Stage 3: 30-45 minutes
- Stage 4: 15 minutes (includes test execution)
- Stage 5: 15 minutes
- Stage 6: 15 minutes
- Total: 90-120 minutes

## Verification Gates

- [ ] pytest passes with >= 80% coverage
- [ ] mypy passes with no errors
- [ ] flake8 passes with no errors
- [ ] bandit passes with no HIGH/MEDIUM issues
- [ ] All model verifications pass
- [ ] Cross-family verification: Verify ≠ Implement, Critique ≠ Implement
