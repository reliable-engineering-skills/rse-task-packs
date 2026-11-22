---
name: rse-task-packs
description: "Turn an accepted feature or change into portable, bounded task files (spec, contracts, decisions, manifest, per-task instructions, evidence) that another agent or a later session can execute and resume without chat history. Use when the user asks to break work into tasks, plan multi-session or multi-agent execution, prepare a handoff, or resume a task pack; includes a structural validator. Not for small direct edits. Builds on the reliable-software-engineering skill."
metadata:
  version: "3.0.0"
---

# Portable, bounded implementation task packs

> Companion of the `reliable-software-engineering` skill, which must be installed alongside. Its core rules apply here; links into `../reliable-software-engineering/` point at its references.

Use for requested task decomposition, substantial multi-session work, or preparing tasks for another agent. A small direct edit does not need a pack. Preserve an existing Spec Kit/project workflow rather than creating competing specification truth.

## Establish scope before executable tasks

Inspect the actual repository, relevant project instructions, accepted user request, versions, interfaces, checks, and current revision. A planning request produces draft tasks, not code execution. Record the source of approval: an actual user instruction can already authorize the listed scope. Do not demand another approval for what the user has clearly authorized. A draft product choice or model-generated assumption is not user approval.

Assign stable requirement IDs and observable acceptance. Mark uncertainties explicitly. Ask the user before adding or changing product behavior, public contracts, authorization policies, data retention, paid/external effects, infrastructure, or dependencies beyond accepted scope. Show the concrete decision, effect, alternatives, and recommended choice. Record their answer; do not invent an answer or promote your recommendation to approval. Continue independent approved tasks when possible. Routine internal names, local structure, and necessary checks within accepted scope can be chosen without repeated questions.

## Adapt Spec Kit selectively

GitHub Spec Kit separates specification, technical planning, and traceable tasks organized by independently testable stories. Preserve canonical `spec.md`, `plan.md`, and `tasks.md` when already present. Generate one execution file per bounded task, referencing those canonical artifacts and requirement/story IDs; do not maintain a second conflicting requirements list. Regenerate affected task projections after an approved spec change.

The supplied adapter is original guidance informed by the inspected [Spec Kit templates](../reliable-software-engineering/references/standards-sources.md). Do not require its CLI, slash commands, branches, fixed layers, mandatory foundation phase, auto-commits, blanket parallel agents, or a particular stack. Do not copy sample features into a real plan. Verification remains proportionate to risk even when a source template describes new automated tests as optional.

## Recommended pack

Use the [pack skeleton](assets/task-pack/INDEX.md) and adapt actual paths. The manifest is a task index; the spec owns requirement meaning. These Markdown files are instructions an agent can carry out, not automatically executable shell programs.

```text
feature-pack/
  INDEX.md          navigation and current execution policy
  SPEC.md           accepted requirements or links to canonical project spec
  CONTRACTS.md      affected contract decisions or links to their real owners
  DECISIONS.md      actual scope decisions and unresolved questions
  manifest.json     requirement/task IDs, dependencies, paths and required checks
  tasks/T001.md     one bounded outcome, context and handoff
  evidence/         only actual results, created as work runs
```

For an existing planning system, integrate equivalent fields/files rather than forcing these names. Keep initial instructions and task-specific files sufficient for an agent with no chat history. Do not create AGENTS/CLAUDE rules that silently activate another workflow.

## Shape each task for one useful increment

Each file needs: requirement/story IDs and spec revision; one outcome; included and excluded changes; prerequisite task states; exact existing files/contracts to read; allowed edit paths; small ordered actions; observable acceptance including relevant negative/failure cases; check IDs/commands or precise manual checks; stop/change conditions; and a handoff location.

Prefer a vertical behavior slice where it is independently verifiable. Split genuine prerequisite discovery, migration, implementation, or external activation when each needs a separate decision/checkpoint. Do not split every function into a task or leave an untestable half-feature disguised as a finished story. Shared-file edits are dependencies unless ownership is explicitly coordinated. Mark parallel eligibility only after checking files, shared state, schema, and contract compatibility; the pack does not authorize spawning agents.

Use 600-1,200 English words as an initial authoring target for a substantial task, not a minimum, token limit, or vendor guarantee. Smaller self-contained tasks are better. If context, unresolved decisions, multiple outcomes, or several failure domains make completion uncertain, split along a verifiable boundary. Never delete critical constraints to meet a word budget. Avoid estimates that promise completion within every runtime session.

## Execution profile

Packs target well-specified agentic work at moderate reasoning effort, the setting vendor guidance such as [S02](../reliable-software-engineering/references/standards-sources.md#s02) recommends for that kind of work, while remaining plain Markdown/JSON usable by any agent. Model/effort must actually be selected in the host/API; writing a model name here does not configure it. Check current official model/runtime documentation before configuration. Do not assume one vendor's context/token counter applies to another.

Load INDEX, the selected task, its accepted requirement excerpts, contracts it touches, and prerequisite handoffs. Search/read affected code progressively; do not ingest the entire source tree, all completed task files, or all skill references. Reserve room for tool output, a code change, focused checks, and the final handoff. Bound searches/log output; summarize established decisions with locations. A large advertised context window does not make an oversized task safe.

Work through the selected authorized task and its checks without stopping merely to ask whether to continue. Stop when accepted work is complete, when a consequential scope decision is unresolved, or at a real execution/permission boundary. Do not start unrelated enhancements or repeated review loops after checks pass. A blocked task must not be marked done; continue only independent tasks within the requested execution scope.

## Completion and resumption

Before execution confirm actual repository state, prerequisite evidence, approved requirements, and allowed paths. After execution inspect the diff for untraced additions and unexpected files. Verify actual APIs/imports against installed versions. Record revision/dirty state, changed paths, acceptance evidence, commands/results/environment, outstanding limitations, and next action. Update the manifest only with actual states. Evidence is not an approval event.

If the session budget tightens, checkpoint safely before losing context: exact last successful check, pending edits, failure output location, and next command/reproduction. Leave the task `in_progress` or `blocked`. The next agent verifies current files and revision before resuming; a handoff is not proof the repository stayed unchanged.

## Optional structural validator

Run `<python> -B <skill>/scripts/validate_task_pack.py <pack>` (`<python>` is `python3`, `py -3` or `python`, whichever exists; Python 3.9+) to check references, unique IDs, requirement coverage, task dependencies/cycles, safe pack paths, readiness declarations, and completion-evidence consistency. Use `--task T001` to test declared scheduling eligibility. Exit 0 means structurally valid (and eligible when selected), 1 means invalid, and 2 means the selected task cannot start under declared states. The tool does not execute checks, assess code correctness, prove approval authenticity, enforce a filesystem edit sandbox, or certify security. Confirm those from actual sources/tool results and the real user instruction.

Completion evidence must include `spec_revision` matching the manifest and `spec_sha256` of the current spec file. Obtain the value with `--spec-hash` rather than computing it by hand; it hashes the file with BOM and line endings normalized, so a Git CRLF/LF checkout does not invalidate evidence while any content change still does. Raw-byte hashes written by 2.3.x remain accepted while the bytes are unchanged. After any spec file change, re-evaluate and reverify affected tasks before updating evidence; the hash also invalidates unchanged tasks conservatively. Requirement anchors support Markdown headings (repeated headings take GitHub's `-1`, `-2` suffixes) and explicit HTML anchor IDs; use unambiguous anchors. Before any task is active, the validator also rejects `REPLACE_` placeholders left in pack-level Markdown such as CONTRACTS.md and DECISIONS.md. The manifest is the sole source of task state; omit State/Status fields from task files. Existing 2.3.0 completion evidence must be revalidated and migrated; never invent evidence or hashes for checks not rerun.

Evidence JSON example (replace every value with actual observations):

```json
{"source_revision":"actual-code-revision", "spec_revision":"actual-spec-revision", "spec_sha256":"sha256-of-spec-file-bytes", "environment":"actual-test-environment", "checks":[{"id":"CHK-001", "result":"passed", "evidence":"actual-command-and-result"}], "acceptance_observations":["actual-observed-behavior"]}
```

The hash detects any content change to `spec_file`, not changes to other linked requirements. Check linked files and actual approvals independently.
