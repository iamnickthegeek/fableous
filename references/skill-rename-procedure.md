# Skill Rename Procedure

This documents the clean rename from `fable-orchestrator` to `fableous` (June 2026). Use as reference for any future skill renames.

## Files Changed (Operational)

### Critical (will break if skipped)
1. **`SKILL.md` YAML frontmatter** — `name: fable-orchestrator` → `name: fableous`
2. **`scripts/route_config.py` line 41** — `BACKUP_DIR` path hardcoded to old name. Change to new directory name.

### Documentation (cosmetic but should update)
3. **`SKILL.md` body** — all internal path references (install URL, `~/.hermes/skills/fable-orchestrator/...`)
4. **`README.md`** — install URL, repo URL, skill load commands, architecture tree
5. **`INSTALL.md`** — install URL
6. **`CONTRIBUTING.md`** — skill load commands
7. **`references/github-publication.md`** — repo URL, install URL, git remote
8. **`references/config-cycling.md`** — backup file path
9. **`references/model-verification.md`** — script paths
10. **`IMPLEMENTATION_PLAN_V7.md`** — all path references
11. **`IMPLEMENTATION_PLAN_7-1.md`** — all path references

### Does NOT need changing
- **`archive/`** — frozen legacy, 32 references to old name preserved, no operational impact
- **`.git/`** — only remote URL needed updating (`git remote set-url`)
- **Script logic** — only `route_config.py` had a hardcoded path; `fable_routing.py` uses relative imports

## Procedure

```bash
# 1. Update all references in active files (not archive/)
#    Use replace_all for each file

# 2. Rename directory
mv ~/.hermes/skills/fable-orchestrator ~/.hermes/skills/fableous

# 3. Update git remote
cd ~/.hermes/skills/fableous
git remote set-url origin git@github.com:iamnickthegeek/fableous.git

# 4. Verify
grep -r "fable-orchestrator" ~/.hermes/skills/fableous/ --include="*.md" --include="*.py" -l | grep -v "archive/"
# Should return nothing

# 5. Commit and push
```

## Verification Checklist
- [ ] Old directory gone
- [ ] New SKILL.md `name:` field matches new name
- [ ] `route_config.py` BACKUP_DIR matches new path
- [ ] Zero active-file references to old name (archive/ excluded)
- [ ] `route_config.py status` still functional
- [ ] Git remote updated
- [ ] Pushed successfully
