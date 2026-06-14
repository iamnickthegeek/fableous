# Contributing to Fable Orchestrator

Thank you for your interest in contributing! This project is designed to be accessible to non-coders and developers alike.

## Ways to Contribute

### For Non-Coders

- **Test it**: Run tasks and report what works and what doesn't
- **Share examples**: Add your task descriptions to `examples/`
- **Improve documentation**: If something in INSTALL.md or README.md is confusing, suggest changes
- **Report bugs**: Open an issue with your task description and the error message

### For Developers

- **Add features**: See the roadmap below
- **Write tests**: Add tests to `tests/`
- **Fix bugs**: Check open issues and submit PRs
- **Improve code**: Refactoring, performance improvements, better error handling

## Development Setup

```bash
# Clone the repo
git clone https://github.com/iamnickthegeek/fable-orchestrator.git
cd fable-orchestrator

# Install in development mode
pip install -e .

# Run tests
pytest tests/
```

## Code Style

- Python 3.10+ with type hints
- Docstrings for all public functions
- Keep functions focused and small
- Add tests for new features

## Roadmap

### v5.1 (Next)
- [ ] Vision integration: analyze images in the automated loop
- [ ] Dynamic re-planning: adjust the DAG mid-flight when obstacles are encountered
- [ ] Better verification: domain-specific checks (e.g., run `pytest` for software, check citations for research)

### v5.2
- [ ] Distributed agent pool: support for hundreds of agents via Redis/RabbitMQ
- [ ] Web dashboard: visualize running tasks, stage status, and outputs
- [ ] Plugin system: custom stages and verification checks

### v6.0
- [ ] Integration with Hermes native tools: use `delegate_task` when available, fallback to subprocess
- [ ] Auto-discovery: automatically detect the task type and choose the right stage sequence
- [ ] Self-improvement: learn from past tasks to improve planning and model selection

## Submitting Changes

1. Fork the repo
2. Create a branch: `git checkout -b my-feature`
3. Make your changes
4. Run tests: `pytest tests/`
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin my-feature`
7. Open a Pull Request

## Questions?

Open an issue or ask in the Hermes Agent community.
