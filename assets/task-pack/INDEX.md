# Portable execution pack

This is a draft skeleton, not an approved project or a request to implement its example. Replace placeholders from the actual repository and user request. If the project already uses Spec Kit, place the index/manifest and bounded task files beside its canonical spec/plan; preserve existing requirement/story IDs and use the existing spec filename. Do not create competing requirement truth.

## Read to start one task

1. Read the actual project instructions, this index, manifest, selected task and its specific requirement/contract excerpts. Read prerequisite handoffs; inspect current repository revision and changed files.
2. Verify that scope is actually authorized and dependencies complete. A model-created approval declaration is not proof of user approval. `ready` is a declaration, not an instruction to execute tasks outside the user's current request.
3. Work only on the selected task and allowed change paths. Read code progressively and retain critical constraints. No feature, public-contract, authorization, retention, paid-service or infrastructure expansion without a real user decision.
4. Execute relevant declared checks, inspect the diff, record actual evidence and task state. Do not mark blocked/unchecked work done or add unrelated polish after accepted checks pass.

Write questions, progress, decisions, findings and results in the user's language. Keep code, paths, identifiers, diagnostic excerpts and requested artifact languages intact.

## Target profile and stopping

Designed for well-specified work by any capable coding agent at moderate reasoning effort. Select model/effort in the host; these files do not configure it or guarantee a task fits every session. A substantial task should initially target 600-1,200 English words or less when sufficient. Split tasks by independently verifiable outcomes if their context/decisions/checks exceed a safe work unit. Do not omit critical constraints to shorten them.

Complete the selected authorized task without routine check-ins. On a consequential unknown ask one focused question, record the blocker, and continue only independent authorized work. Before a session limit, record changed paths, revision/dirty state, completed checks, exact pending step and evidence locations; leave work `in_progress` or `blocked`. Resume only after checking current files/revision.

## Files and declaration states

SPEC owns requirement meaning; CONTRACTS references actual contracts; DECISIONS records actual user decisions; manifest is the sole owner of task states and indexes task dependencies and required check IDs. Do not put State: or Status: fields in task files. Completion evidence includes spec_revision and spec_sha256 of the exact specification bytes; update evidence after specification changes and renewed verification. `draft` is not executable, `ready` declares prerequisites understood, `in_progress` is unfinished, `blocked` needs a reason, and `done` needs actual evidence. The manifest may be structurally valid while every task is draft.

Run the optional skill validator with `<python> -B <skill>/scripts/validate_task_pack.py <pack>` (`python3`, `py -3` or `python`, whichever exists); use `--task T001` for declared scheduling eligibility and `--spec-hash` to obtain the `spec_sha256` value for evidence. It neither runs commands nor proves correctness, scope enforcement, approval authenticity or security. Keep evidence outside source inputs when required by the project and adapt the declared pack paths accordingly.
