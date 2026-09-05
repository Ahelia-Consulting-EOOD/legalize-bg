# The `corpus-integrity` job must become a required status check on `main`

**Date:** 2026-09-06
**Status:** open — needs an owner action in the repository settings, not a code change
**Raised by:** Part II Task 6 (the single corpus write gate), PR for `feat/corpus-write-gate`

## The finding

Owner Directive 12 says a gate blocks or it does not exist. Two of the three layers of
defence in depth (convergence plan Part IV.3) are now in the tree:

1. the **write gate**, `corpus_gate.write_act`, which refuses a defective act at ingestion
   and which no module can route around, because `find_corpus_writers` fails the build if
   any module other than the gate writes a corpus path;
2. the **corpus-wide runner**, `python -m corpus_integrity`, wired into `.github/workflows/ci.yml`
   as the `corpus-integrity` job, which catches anything that reached the tree by another
   route, a hand-edit included.

Layer 2 currently *reports* rather than *blocks*. The job runs on every pull request and exits
non-zero on any unwaived violation, any stale waiver and any count drift, but GitHub does not
prevent a merge on a failing job unless that job is listed in the branch protection rules for
`main` as a **required status check**. Until it is listed, a red `corpus-integrity` is a red
tick next to a merge button that still works.

**So Directive 12 is not satisfied by the job alone.** It is satisfied by the job plus the
branch protection setting.

## The action

Repository settings → Branches → the protection rule for `main` → Require status checks to pass
before merging → add **`corpus-integrity`**. It is an owner action: the setting is not in the
repository tree and cannot be committed.

Add the other jobs of `ci.yml` in the same pass if they are not required yet; this record names
`corpus-integrity` because it is the one Directive 12 turns on.

## Why it is not urgent and not optional

Not urgent, because the write gate makes the common path safe without it: the ingestion adapters
cannot write a defective act, and the static scan means no new adapter can appear that skips the
gate. Not optional, because the gate cannot see a defect that arrives another way — a hand-edited
file, a `git revert` of a repair, a merge that resurrects an old act — and layer 2 is what catches
those. A layer that reports and does not block is the state Directive 12 exists to name.

## Verification

After the setting is added, a pull request whose branch carries a corpus defect must show
`corpus-integrity` as a failing **required** check and must not be mergeable. A green run of the
same job on a clean branch is not evidence: the question is whether a red one blocks.
