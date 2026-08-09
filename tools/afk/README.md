# AFK Agent Loop (`sandbuket`)

Run AI coding agents away-from-keyboard over the Rakieta backend repo.

This is built on [`sandbuket`](https://github.com/RobertConstantin02/sandbuket):
a Python library that runs an agent inside a Docker sandbox against a git
worktree and collects the commits.

## Layout

| Path | What |
| --- | --- |
| `tools/afk/afk.py` | Issue-driven orchestrator using `sandbuket.create_sandbox()` and `sb.run()`. |
| `tools/afk/pyproject.toml` | Isolated Poetry project pinning `sandbuket` from GitHub. |
| `.sandbuket/prompt.md` | Agent prompt for task selection, verification, commits, and issue handoff. |
| `.sandbuket/Dockerfile` | Sandbox image with Claude Code, Python, Poetry, make, git, and gh. |
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
`--base-branch` (default current HEAD), `--image` (default `sandbuket:rakieta`),
`--model` (default `claude-opus-4-8`), and `--label` (default
`ready-for-agent`).

Work lands on the named branch. Review the branch and open a PR when done.
