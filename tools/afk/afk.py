#!/usr/bin/env python3
"""AFK agent loop for Rakieta, driven by sandbuket.

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
DEFAULT_IMAGE = "sandbuket:rakieta"
DEFAULT_BRANCH = "agent/afk"
DEFAULT_MODEL = "claude-opus-5"
# xhigh is the documented best setting for coding and agentic work, and is the
# default in Claude Code itself. `max` exists above it but is for extremely hard,
# latency-insensitive work — it shows diminishing returns and can overthink the
# routine issues this loop mostly picks up. Sweep down to `high` or `medium` if
# an iteration's token spend is not buying quality.
DEFAULT_EFFORT = "xhigh"
DEFAULT_LABEL = "ready-for-agent"


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

    async with await create_sandbox(
        sandbox=sandbox,
        branch=args.branch,
        base_branch=args.base_branch,
        cwd=str(REPO_ROOT),
        name="afk",
    ) as sb:
        for i in range(1, args.iterations + 1):
            print(f"\n--- iteration {i}/{args.iterations} ---")
            result = await sb.run(
                agent=agent,
                prompt=build_prompt(args.label, args.branch),
                completion_signal=COMPLETION_SIGNAL,
                max_iterations=1,
            )
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
    args = parser.parse_args()
    try:
        return asyncio.run(afk(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
