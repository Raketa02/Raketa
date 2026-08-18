# AFK Agent Loop (`sandbuket`)

Run AI coding agents away-from-keyboard over the Raketa monorepo — all three
apps, one at a time. An agent works a single issue per iteration and respects the
ownership boundary, so a task that would cross apps is one to split rather than
one to reach across.

This is built on [`sandbuket`](https://github.com/RobertConstantin02/sandbuket):
a Python library that runs an agent inside a Docker sandbox against a git
worktree and collects the commits.

## Layout

| Path | What |
| --- | --- |
| `tools/afk/afk.py` | Issue-driven orchestrator using `sandbuket.create_sandbox()` and `sb.run()`. |
| `tools/afk/pyproject.toml` | Isolated Poetry project pinning `sandbuket` from GitHub. |
| `.sandbuket/prompt.md` | Agent prompt for task selection, verification, commits, and issue handoff. |
| `.sandbuket/Dockerfile` | Sandbox image with Claude Code, Python 3.11, Poetry, Node 22, pnpm, make, git, gh and jq. |

**Two pins are load-bearing.** Poetry must match the version that generated
`backend/poetry.lock` — currently **2.1.3**, lock-version 2.1; an older Poetry
reads that lock differently and can resolve dependency groups wrongly. And `jq`
is required by `.claude/hooks/*`: without it both hooks fail safe and block every
tool call the agent makes.
| `.sandbuket/.env` | Local token file, gitignored. Copy from `.env.example`. |

## Prerequisites

1. Docker running.
2. `gh` authenticated on the host.
3. Tokens in `.sandbuket/.env`:
   - `CLAUDE_CODE_OAUTH_TOKEN`
   - `GH_TOKEN`
4. AFK tooling installed:

```bash
make afk-install
```

## Usage

```bash
make afk-build
make afk

poetry -C tools/afk run python afk.py 10 --branch agent/email-verification
poetry -C tools/afk run python afk.py 3 --label ready-for-agent
```

Options: `iterations` (default 5), `--branch` (default `agent/afk`),
`--base-branch` (default current HEAD), `--image` (default `sandbuket:raketa`),
`--model` (default `claude-opus-5`), `--effort`
(`low|medium|high|xhigh|max`, default `xhigh`), and `--label` (default
`ready-for-agent`).

**On `--effort`.** `xhigh` is the documented best setting for coding and agentic
work and is what Claude Code uses by default. `max` sits above it but is meant for
extremely hard, latency-insensitive work — it shows diminishing returns and can
overthink routine issues. If an iteration's token spend stops buying quality,
sweep down (`high`, then `medium`) rather than up.

Work lands on the named branch. Review the branch and open a PR when done.
