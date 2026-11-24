# rse-task-packs

Turns accepted work into portable, resumable task packs for another agent or a later session, with a structural validator.

> Requires [reliable-software-engineering](https://github.com/reliable-engineering-skills/reliable-software-engineering) installed alongside. Links such as `../reliable-software-engineering/references/...` resolve on disk after installation, not on the GitHub web view.

Part of the **RSE skill suite**: five complementary agent skills for Claude Code and Codex. One core skill
holds the shared rules; each companion adds one workflow and points back to the core, so every rule has
exactly one owner.

| Skill | Role | What it does |
| --- | --- | --- |
| [reliable-software-engineering](https://github.com/reliable-engineering-skills/reliable-software-engineering) | Core (required) | Proportionate, evidence-based engineering decisions: scope, smallest sufficient change, contracts, payments and data history, authorization, caching, operations and honest verification. |
| **rse-task-packs** (this repo) | Companion | Turns accepted work into portable, resumable task packs for another agent or a later session, with a structural validator. |
| [rse-refactoring](https://github.com/reliable-engineering-skills/rse-refactoring) | Companion | Behavior-preserving refactoring and codebase rescue, one responsibility at a time, with a before/after check recorder. |
| [rse-security-review](https://github.com/reliable-engineering-skills/rse-security-review) | Companion | Focused security review: trace untrusted input to sensitive sinks and report evidence-graded findings without touching production. |
| [rse-debugging](https://github.com/reliable-engineering-skills/rse-debugging) | Companion | Fixes reported bugs from evidence: reproduces with a failing check, fixes the cause, and leaves a regression test, even when the cause looks obvious. |

## Install the suite

The companions link into the core skill's files, so install all five side by side.

Claude Code (PowerShell):

```powershell
foreach ($r in "reliable-software-engineering", "rse-task-packs", "rse-refactoring", "rse-security-review", "rse-debugging") { git clone "https://github.com/reliable-engineering-skills/$r" "$env:USERPROFILE\.claude\skills\$r" }
```

Claude Code (bash/zsh):

```bash
for r in reliable-software-engineering rse-task-packs rse-refactoring rse-security-review rse-debugging; do git clone "https://github.com/reliable-engineering-skills/$r" ~/.claude/skills/$r; done
```

Codex: clone the same five repositories into `~/.codex/skills/`. Update later with `git pull` in each folder.

## Contents

- `SKILL.md`: scoping, task shape, execution profile, completion and resumption.
- `assets/task-pack/`: the pack skeleton (INDEX, SPEC, CONTRACTS, DECISIONS, manifest, task template).
- `scripts/validate_task_pack.py`: structural validator (Python 3.9+, standard library only).

```powershell
py -3 -B scripts/validate_task_pack.py <pack>               # structure
py -3 -B scripts/validate_task_pack.py <pack> --task T001   # declared eligibility (exit 2 = cannot start)
py -3 -B scripts/validate_task_pack.py <pack> --spec-hash   # value for completion evidence
```

The validator checks structure, never approval authenticity or code correctness.

## License

MIT. Version 3.1.1; see the [core changelog](https://github.com/reliable-engineering-skills/reliable-software-engineering/blob/main/CHANGELOG.md).
