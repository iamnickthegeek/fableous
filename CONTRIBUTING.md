# Contributing to Fable Orchestrator

## What You Need

- Hermes Agent installed
- The skill loaded: `skill_view(name='fableous')`
- Familiarity with the skill structure (SKILL.md, references/, templates/)
- A `fable-config.yaml` in the skill directory (required — no default routing table exists)

## How to Contribute

### 1. Report an Issue

Open a GitHub issue:
- What happened
- What you expected
- The exact task that triggered it
- Your Hermes version and provider setup

### 2. Suggest a Change

- Open an issue first. Describe the change and why it improves the skill.
- If approved, submit a PR.

### 3. Update the Skill

The skill is the SKILL.md file. Changes to the skill must follow the Hermes skill format:

- YAML frontmatter with name, description, version, author, license, metadata
- Markdown body with sections matching the skill's structure
- Imperative language for procedures: "You MUST...", "Do NOT..."
- Every new feature must include a verification checklist

### 4. Update Reference Documents

Reference documents in `references/` are supporting docs. They can be updated independently of the skill.

- Keep them factual and specific
- Avoid generic advice
- Include examples
- Cross-reference the SKILL.md where relevant

### 5. Update Prompt Templates

Templates in `templates/` are reusable prompts. When updating:

- Keep them generic enough to work with any task
- Use {{variable}} placeholders for task-specific data
- Include guardrails and model tagging instructions
- Test the template with a real task before submitting

### 6. Add Examples

Examples in `examples/` are concrete execution traces. When adding:

- Show the full 6-stage execution
- Include the exact todo list
- Show the verification checks
- Include expected outputs
- Estimate time

### 7. Update Helper Scripts

Scripts in `scripts/` are small utilities, not an engine. If you change them:

- Keep them self-contained and runnable with `python3 scripts/<name>.py`
- Do not reintroduce a Python engine, daemon, or state database
- Run `python3 scripts/verify_models.py` to confirm it still works
- Run `python3 scripts/auto_detect_providers.py` to confirm output is valid YAML

### 8. Test Before Submitting

Run the skill against a real task before submitting:

1. Ensure `fable-config.yaml` exists in the skill directory with your provider/models
2. Load the skill: `/skill fableous`
3. Give a task: "Write a blog post about X"
4. Verify all 6 stages complete
5. Verify the FINAL.md is correct
6. Check the WORK_LOG.md for completeness
7. Log the result in `examples/test_results.md`
8. Run `python3 scripts/verify_models.py` to confirm provider setup

## Code of Conduct

- Be direct. No filler.
- Focus on what works.
- Prefer simple solutions.
- Document the reasoning.
- Ship working tools.

## License

MIT. See [LICENSE](LICENSE).
