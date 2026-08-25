#!/usr/bin/env python3
"""AFK agent loop for Raketa, driven by sandbuket.

Usage from the repo root:

    make afk-build
    make afk
    poetry -C tools/afk run python afk.py 10 --branch agent/my-feature
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from sandbuket import claude_code, create_sandbox
from sandbuket.errors import AgentError, AgentIdleTimeoutError
from sandbuket.sandboxes.docker import docker

# --- workaround: sandbuket's 64 KiB stdout line cap --------------------------
# sandbuket's stream_subprocess() calls asyncio.create_subprocess_exec() without
# a `limit=`, so stdout gets asyncio's default 64 KiB StreamReader cap. Claude
# Code speaks stream-json — one JSON object per line — and any line carrying a
# large tool result or message exceeds that, so readline() raises
#
#     ValueError: Separator is found, but chunk is longer than limit
#
# which kills the run mid-iteration and loses that iteration's work.
#
# Patching asyncio.streams._DEFAULT_LIMIT does NOT work: create_subprocess_exec
# binds it as a default argument at import time. Wrapping the function does,
# because sandbuket resolves it through the module at call time.
#
# Remove once sandbuket passes an explicit limit of its own.
_create_subprocess_exec = asyncio.create_subprocess_exec


async def _create_subprocess_exec_unbounded(*args, **kwargs):  # type: ignore[no-untyped-def]
    kwargs.setdefault("limit", 64 * 1024 * 1024)
    return await _create_subprocess_exec(*args, **kwargs)


asyncio.create_subprocess_exec = _create_subprocess_exec_unbounded  # type: ignore[assignment]
# -----------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_FILE = REPO_ROOT / ".sandbuket" / "prompt.md"
COMPLETION_SIGNAL = "<promise>COMPLETE</promise>"
DEFAULT_IMAGE = "sandbuket:raketa"
DEFAULT_BRANCH = "agent/afk"
DEFAULT_MODEL = "claude-opus-5"
# xhigh is the documented best setting for coding and agentic work, and is the
# default in Claude Code itself. `max` exists above it but is for extremely hard,
# latency-insensitive work — it shows diminishing returns and can overthink the
# routine issues this loop mostly picks up. Sweep down to `high` or `medium` if
# an iteration's token spend is not buying quality.
DEFAULT_EFFORT = "xhigh"
DEFAULT_LABEL = "ready-for-agent"
# Sandbuket's watchdog fails an iteration after this many seconds with no stdout
# line from the agent, and its own default is 600. That is too tight for this
# loop: the prompt requires the app's *full* gate before committing, and a cold
# `poetry install && make check` is one Bash tool call that emits nothing to the
# orchestrator until it returns — the agent is working hard and looks idle. The
# timeout still earns its keep against a genuinely wedged process, so it stays;
# it is just set above the longest legitimate silence rather than below it.
DEFAULT_IDLE_TIMEOUT = 30 * 60
# How many iterations may fail back-to-back before the loop gives up. One is too
# few — a dropped connection is transient far more often than not. Unbounded is
# wrong too: a broken image or a bad credential fails identically every time, and
# spinning the whole budget through it wastes the run and buries the real error.
MAX_CONSECUTIVE_FAILURES = 3


def _sh(args: list[str]) -> str:
    return subprocess.run(
        args, cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def fetch_issues(label: str) -> str:
    raw = _sh(
        [
            "gh",
            "issue",
            "list",
            "--state",
            "open",
            "--label",
            label,
            "--json",
            "number,title,body,comments,labels",
        ]
    )
    issues = json.loads(raw or "[]")
    if not issues:
        return f"(no open issues labelled `{label}`)"
    return json.dumps(issues, indent=2)


def fetch_recent_commits(branch: str | None = None) -> str:
    # Log the AGENT's branch, not HEAD. The host repo sits on whatever branch you
    # were last on; the agent's commits live on `branch` and are not ancestors of
    # it, so logging HEAD reports "no previous AFK commits" on every iteration and
    # the agent restarts blind — redoing work it already did, on top of itself.
    cmd = ["git", "log"]
    if branch:
        cmd.append(branch)
    cmd += ["--grep=AFK", "-n", "10", "--format=%H%n%ad%n%B---", "--date=short"]
    try:
        out = _sh(cmd)
    except subprocess.CalledProcessError:
        out = ""  # branch does not exist yet — first iteration
    return out or "(no previous AFK commits)"


def worktree_for(branch: str) -> Path | None:
    """The host worktree checked out on ``branch``, or None if there isn't one.

    Read out of git rather than off the sandbox object. Sandbuket carries the
    path on a private attribute, and a private attribute is a thing that moves
    without a release note; `git worktree list` is a public contract.
    """
    try:
        out = _sh(["git", "worktree", "list", "--porcelain"])
    except subprocess.CalledProcessError:
        return None
    path: str | None = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = line.removeprefix("worktree ")
        elif line == f"branch refs/heads/{branch}" and path:
            return Path(path)
    return None


def preserve_partial_work(branch: str, reason: str) -> None:
    """Commit whatever an interrupted iteration left, so the next one can finish it.

    Called twice: once at startup, to adopt anything an earlier run left behind,
    and again after each caught iteration failure.

    An interrupted iteration leaves a half-finished ticket in the worktree. Left
    uncommitted, the next iteration inherits it *invisibly* — RECENT COMMITS only
    shows committed work, so the agent sees a clean-looking start and a dirty tree
    it has no memory of, and either builds on code no gate has seen or fights it.

    Committing rather than stashing is what makes the work resumable. A stash is
    preserved but invisible: nothing in the prompt mentions it, so the next
    iteration silently starts a different ticket and the stash rots. A commit is
    preserved *and* visible — `fetch_recent_commits` greps for AFK, so the marker
    below lands in RECENT COMMITS, and prompt.md tells the agent to finish that
    task before picking a new one.

    The tradeoff, deliberately taken: this puts code on the branch that never
    passed the app's gate. The subject line says so, and the next iteration is
    required to gate it before building on it.

    A no-op when the branch has no worktree yet or the worktree is clean, which
    is the normal case for a healthy run.
    """
    worktree = worktree_for(branch)
    if worktree is None:
        return
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=worktree,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not dirty:
        return
    message = (
        # `AFK:` first, or fetch_recent_commits' --grep misses it and the whole
        # point — making the work visible to the next iteration — is lost.
        f"AFK: WIP — interrupted during {reason}; gate never ran\n"
        "\n"
        "Committed by the orchestrator, not by the agent: the iteration died "
        "before it could verify or commit. This code has NOT passed the app's "
        "check gate and may not even parse.\n"
        "\n"
        "The next iteration owns it: finish this task, run the gate, and amend "
        "or replace this commit. Do not start a new ticket on top of it."
    )
    subprocess.run(["git", "add", "-A"], cwd=worktree, capture_output=True, text=True)
    committed = subprocess.run(
        # --no-verify because a pre-commit hook is exactly what half-finished code
        # fails, and a hook veto here would discard the work this function exists
        # to save. The commit is a holding pen, not a claim that the code is good.
        ["git", "commit", "--no-verify", "-m", message],
        cwd=worktree,
        capture_output=True,
        text=True,
    )
    if committed.returncode != 0:
        print(
            f"  ! could not preserve {len(dirty.splitlines())} uncommitted path(s): "
            f"{committed.stderr.strip() or committed.stdout.strip()}\n"
            f"  ! they are still in {worktree} — deal with them before re-running.",
            file=sys.stderr,
        )
        return
    print(
        f"  ! {len(dirty.splitlines())} uncommitted path(s) left behind; committed "
        f"as a WIP marker so the next iteration finishes them.\n"
        f"  ! inspect with: git -C {worktree} show HEAD",
        file=sys.stderr,
    )


def build_prompt(label: str, branch: str | None = None) -> str:
    base = PROMPT_FILE.read_text()
    return (
        f"# ISSUES\n\n```json\n{fetch_issues(label)}\n```\n\n"
        f"# RECENT COMMITS\n\n```\n{fetch_recent_commits(branch)}\n```\n\n"
        f"---\n\n{base}"
    )


async def afk(args: argparse.Namespace) -> int:
    if not PROMPT_FILE.exists():
        print(f"error: {PROMPT_FILE} not found", file=sys.stderr)
        return 2

    agent = claude_code(args.model, effort=args.effort)
    sandbox = docker(image_name=args.image)

    print(
        f"AFK loop: up to {args.iterations} iteration(s) on branch "
        f"'{args.branch}' (image {args.image}, model {args.model}, "
        f"effort {args.effort})."
    )

    # Sweep the worktree BEFORE handing it to sandbuket, not after. Two reasons.
    #
    # First, the in-loop handler below only covers failures this process lives to
    # catch. A run killed by a signal, an unhandled error, or a laptop that slept
    # leaves the worktree dirty with nobody to clean it, and sandbuket preserves
    # the worktree on failure by design — so the mess outlives the run that made
    # it and there is no other moment that would notice.
    #
    # Second, sandbuket reuses an existing managed worktree and inspects it to
    # decide what to do (worktree_manager.create): a clean one is fast-forwarded
    # from origin, a dirty one is handed over untouched. Stashing first therefore
    # buys the fast-forward too. Stashing afterwards would get neither — the
    # decision is already made by the time control returns to us.
    preserve_partial_work(args.branch, "an earlier run")

    async with await create_sandbox(
        sandbox=sandbox,
        branch=args.branch,
        base_branch=args.base_branch,
        cwd=str(REPO_ROOT),
        name="afk",
    ) as sb:
        consecutive_failures = 0
        for i in range(1, args.iterations + 1):
            print(f"\n--- iteration {i}/{args.iterations} ---")
            try:
                result = await sb.run(
                    agent=agent,
                    prompt=build_prompt(args.label, args.branch),
                    completion_signal=COMPLETION_SIGNAL,
                    max_iterations=1,
                    idle_timeout_seconds=args.idle_timeout,
                )
            except (AgentError, AgentIdleTimeoutError) as exc:
                # The agent process died — most often a connection lost
                # mid-response, which is transient and says nothing about the
                # work. Before this guard it tore the whole run down: one blip
                # at iteration 2 of N cost the remaining budget and left a
                # half-finished ticket dirty in the worktree.
                #
                # These two only, deliberately. The rest of the SandbuketError
                # family is infrastructure — Docker missing, a sync failure, a
                # bad cwd — and none of that gets better by being retried.
                #
                # AgentIdleTimeoutError is named separately because it does NOT
                # subclass AgentError — it descends straight from SandbuketError.
                # Catching the base class alone let a watchdog timeout escape as
                # an unhandled traceback: the run died instead of retrying, and
                # the iteration's partial work was never quarantined.
                consecutive_failures += 1
                print(f"  ! iteration {i} failed: {exc}", file=sys.stderr)
                preserve_partial_work(args.branch, f"iteration {i} of this run")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    print(
                        f"\n{consecutive_failures} iterations failed back to "
                        f"back; stopping rather than burning the budget. Work "
                        f"so far is on branch '{args.branch}'.",
                        file=sys.stderr,
                    )
                    return 1
                continue
            consecutive_failures = 0
            if result.commits:
                shas = [c.get("sha", "?")[:8] for c in result.commits]
                print(f"  commits this pass: {shas}")
            if result.completion_signal:
                print(f"\nAgent signalled completion after {i} iteration(s).")
                print(f"Work is on branch '{sb.branch}'.")
                return 0

    print(f"\nIteration budget exhausted. Work is on branch '{args.branch}'.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "iterations", nargs="?", type=int, default=5, help="max iterations"
    )
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--base-branch", default=None)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--effort",
        default=DEFAULT_EFFORT,
        choices=["low", "medium", "high", "xhigh", "max"],
        help="reasoning effort (default: %(default)s)",
    )
    parser.add_argument("--label", default=DEFAULT_LABEL)
    parser.add_argument(
        "--idle-timeout",
        type=int,
        default=DEFAULT_IDLE_TIMEOUT,
        metavar="SECONDS",
        help="fail an iteration after this long with no agent output "
        "(default: %(default)s)",
    )
    args = parser.parse_args()
    try:
        return asyncio.run(afk(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
