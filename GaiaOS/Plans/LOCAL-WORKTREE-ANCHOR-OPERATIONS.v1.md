# GaiaOS Local Worktree Anchor Operations v1

AUTHORITY: NAOMI / LIGEIA
STATUS: ACTIVE READ-ONLY MAINTENANCE GUIDANCE
EFFECT_AUTHORITY: NONE

## Problem this prevents

A repository created with `git clone --no-checkout` may intentionally act only as the shared Git object/ref anchor for linked worktrees. In that layout the anchor can have no populated index while `HEAD` contains hundreds of tracked files. Ordinary `git status` output can therefore resemble a catastrophic staged deletion even though no source objects were lost.

`EMPTY_ANCHOR_INDEX != MASS_DELETION`

## Required diagnosis before repair

Before changing an apparently empty root checkout:

1. read `git rev-parse HEAD`;
2. count `git ls-tree -r --name-only HEAD`;
3. count `git ls-files`;
4. inspect `git worktree list --porcelain`;
5. inspect whether `.git/index` exists;
6. use a separate clean linked worktree for maintenance whenever possible.

If the root index is absent or empty, `HEAD` has a populated tree, and valid linked worktrees exist, classify the root as an intentional no-checkout anchor candidate. Do not run checkout, reset, or index reconstruction merely to make the anchor look like a normal working tree.

## Read-only checker

Use:

`python GaiaOS/Tools/GAIAOS-WORKTREE-ANCHOR-CHECK.py <repository-root>`

The checker performs only Git and filesystem reads and emits JSON. It never runs checkout, reset, clean, add, commit, worktree remove, or ref mutation.

## Boundaries

This document describes local operator hygiene only. It does not change canonical GitHub state, grant deployment authority, or make any linked worktree disposable. Untracked artifacts in linked worktrees must be reviewed before cleanup.
