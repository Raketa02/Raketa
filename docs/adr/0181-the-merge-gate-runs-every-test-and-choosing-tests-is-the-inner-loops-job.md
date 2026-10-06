# ADR-0181 — The merge gate runs every test, and choosing tests is the inner loop's job

- **Status:** Accepted
- **Date:** 2026-09-23
- **Leaves standing** [`docs/environments.md`](../environments.md)'s rule 1 word for word:
  **"The environment may select configuration defaults; it may never select behaviour a domain
  test could observe."** Item 3's work factor is argued against it and falls on the *default*
  side. The page's *Testing* section gains a paragraph that links here; its *Refusing to start*
  table gains the bcrypt row when [#483](https://github.com/Raketa02/Raketa/issues/483) makes
  the refusal real, not before.
- **Leaves standing** every "still fires" suite (`make test-drift`, `test-poetry-pin`,
  `test-judged-pairings`, `test-ruleset-diff`, `test-taskdef`, `test-contract-freshness`, the
  purity gates and the player's import-boundary proof). They move into parallel jobs; none is
  dropped from a push.
- Settles [#480](https://github.com/Raketa02/Raketa/issues/480) (PRD) and
  [#481](https://github.com/Raketa02/Raketa/issues/481). The work lands in
  [#482](https://github.com/Raketa02/Raketa/issues/482)–[#490](https://github.com/Raketa02/Raketa/issues/490):
  the race first, then the suite's overheads, then parallel runs, then CI's new shape, and last
  the `/implement` skill's wording for the end-of-ticket run.

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The judged-pairings and ruleset-diff gates were retired with the ranking they gated (#572), and their still-fires suites with them. §4's backend meta tier is one `backend-meta` job, not two, and there is no ruleset release-report job in any tier. ADR-0180, cited below for the flags repository's review convention, was deleted with the flags. Every numbered decision stands.

## Context

**Every ticket ends with a wait, and the wait grows with every ticket**, because every ticket
adds tests. On 2026-09-23:

- CI takes **50–65 minutes per push**, almost all of it the backend `pytest` step — **25 min
  on 2026-09-07, 48–60 min on 2026-09-23**.
- The full backend suite takes **26–43 min** on the laptop, and `/implement` runs it at the
  end of every ticket before CI runs it again.
- The player job takes about **9.5 min**.
- Everything is serial: one job per app, and inside each job every step waits for the one
  before it. Two pushes to one pull request both run to the end — that morning's 04:41 and
  04:52 runs took about 65 minutes each.

**The easiest way to make CI faster is to run less of it**, and it never looks like that from
inside the change that does it: skip the slow directory, run only what the diff touched, mark
the long test `slow` and leave it out, re-run the one that failed. This record exists so that
the next person who wants CI faster does not reach for any of those. The measurements below
are why none is needed.

**What was measured.** 5,288 backend tests and 294 player suites, with nothing in the
repository edited — the overheads were removed with a scratch plugin and environment
variables.

| Cause | Evidence |
| --- | --- |
| Password hashing at production strength | bcrypt at its default cost 12 is about 0.2 s a hash, and every sign-up, login and refresh-token issue hashes once. Three API test files: **170 s at cost 12, 19 s at cost 4.** |
| Coverage on every run | On by default in `backend/pyproject.toml`'s `addopts` and in CI. **2.4× slower** (19 s → 46 s). CI writes a `coverage.xml` nothing uploads, reads or gates on. |
| DEBUG log capture | `APP_ENV=local` puts the root logger at `DEBUG`, and aiosqlite logs two lines per operation — about 490 just to create one test's schema. **About 13%.** |
| No parallelism | Every test builds its own in-memory SQLite database, so the suite is parallel by construction, and it runs on one core. |
| Runner size | `Raketa02/Raketa` is **private**, so a standard `ubuntu-latest` runner has **2 vCPU and 8 GB** (GitHub's published table; a public repository gets 4 and 16). The workflow's comment assumes 16 GB. Jest defaults to one fewer worker than cores — **one worker** there — and the 293 shared player suites take 359 s in CI against about 1 m 40 s on the laptop. |
| Cold Jest transform cache | Every CI run starts cold. On one feature folder a warm cache takes 71 s to 38 s. |
| Serial "still fires" suites | They run after the tests, one after another: about 2.5 min on the backend job, 1 min on the player's. |

The whole backend suite with those overheads removed:

| Configuration | Time | Result |
| --- | --- | --- |
| Today | 26–43 min on the laptop, 48–60 min in CI | green |
| Serial, overheads removed | 6 m 47 s | green |
| `-n 2` (a CI runner's size) | 3 m 18 s | green |
| `-n auto` (one worker per laptop core) | **80 s** | green |

**The time was never the tests.** It was three overheads and one core.

**One test was not ready for parallel runs.**
`test_signup_event_is_delivered_by_embedded_worker` failed once with the laptop under load —
*Could not refresh instance UserORM* — and passed 50 of 50 on an idle machine. The embedded
outbox worker and the request it observes share one database connection. That single flake is
the strongest evidence in this record, and item 6 is built on it.

**Why a subset cannot be the gate.** Affected-only selection was measured on both apps, because
it is the obvious answer and the source article recommends it.

- **The player app selects most of itself.** Its 55 router-harness suites import the whole
  route tree, so any change under a screen selects all of them. A 3-file radar fix selected
  **75 of 294 suites, 53 of them router suites and the heaviest four among them**; the last 14
  commits selected between 75 and 164. The saving is partial and the gate would be no faster
  where it matters.
- **The backend's selector is blind to the tests the repo relies on most.** `pytest-testmon`
  selects a test when a line it *executed* changed. A test that reads the source tree *as text*
  executes none of the file it guards, so a change to that file deselects it — and those tests
  are this repo's structural fences: `test_kernel_purity.py`'s walk,
  `test_only_a_composition_root_imports_the_wall_clock`,
  `test_no_second_copy_of_a_tag_id_exists_anywhere_in_the_app`. testmon cannot see a JSON spec
  a test reads either, nor code run in a subprocess, which is how the seed command is tested.
  **A fence exists to catch the change nobody thought about, and a selector that skips it for
  exactly that change is not a gate.**

The source article is *[Breaking the CI bottleneck](https://dev.to/tamizuddin/breaking-the-ci-bottleneck-architecting-pipelines-for-the-ai-code-era-hm)*.
Adopted from it: tiers, parallelism, caches keyed on the lockfile, and impact analysis — for the
inner loop. What it proposes and this record refuses is listed under *Rejected*.

## Decision

1. **The merge gate runs every test, on every push.** Every collected backend test and every
   player suite runs on every push the workflow runs on — a pull request, `main` or `release`.
   The per-app path filters stay as they are: they decide *whether an app changed*, never
   *which of its tests matter*, and a change that touches an app runs all of that app's tests.
   Making CI faster by skipping, deleting, marking out or weakening a test is not an option
   this repo takes.

2. **Choosing a subset of tests is the inner loop's job, never the gate's.** While iterating on a
   ticket, one command per app runs only what the change can affect: `pytest-testmon` behind a
   backend make target, with its data file ignored by git
   ([#486](https://github.com/Raketa02/Raketa/issues/486)), and Jest's `--changedSince`
   against the branch's base behind a player pnpm script
   ([#487](https://github.com/Raketa02/Raketa/issues/487)). Both are conveniences for the
   inner loop. **Neither is a CI step, neither is the end-of-ticket run, and neither is ever
   what lets a pull request merge.** Each app's `CLAUDE.md` names the command and its blind
   spots, and says the full suite still runs at the end of every ticket and in CI.

3. **The suite gets fast by losing its overheads, never its tests.**
   - **bcrypt's work factor is configuration.** The hasher reads it from settings (#483
      names the variable after bcrypt's own term); the default is **12 everywhere**. The
      test configuration sets bcrypt's minimum, **4**, the way it already sets `APP_ENV` and
      its other defaults. **Every deployed environment — `development`, `staging` and
      `production` — refuses a value below 12**, on the settings object beside the existing
      refusals, so it holds for the API, a worker, a migration and a seed run; the message
      names the variable and never the value. `local` accepts whatever bcrypt accepts, because
      a test run *is* `local` — there is no `test` environment. This is a configuration default
      and not behaviour under rule 1: **a hash verifies the same at any cost**, so no domain
      test can observe it. Tests still hash and verify with real bcrypt, only cheaper, so the
      code under test is the code that ships. bcrypt stores the cost inside each hash, so an
      existing hash keeps verifying under any setting, and refresh-token hashing follows the
      same setting because it goes through the same port. One test pins production at 12 by
      reading the cost out of a real hash.
   - **Coverage leaves the pull request's path.** It is gone from the default pytest options. It is
      measured **nightly, on every push to `main`, and on demand** (`make coverage`), and the
      XML report is kept as an artifact ([#484](https://github.com/Raketa02/Raketa/issues/484),
      [#488](https://github.com/Raketa02/Raketa/issues/488)). **Nothing gates on coverage
      today.** Adding a threshold is a separate decision; whoever makes it should know that a
      threshold checked on every push brings the 2.4× back onto every push.
   - **Tests log at `INFO`**, a default the test configuration sets, as it sets `APP_ENV`
      (there is no `test` environment). A test that asserts on records
      sets its own level through `caplog`, which stays — `-p no:logging` removes that fixture
      and is never the fix.
   - **The suite runs in parallel by default.** `make test`, and so `make check`, runs
      pytest-xdist with one worker per core and work-stealing distribution, because test
      durations are uneven ([#485](https://github.com/Raketa02/Raketa/issues/485)). A serial
      run stays one command away, for chasing an order-dependent failure. **The race above is
      fixed first** ([#482](https://github.com/Raketa02/Raketa/issues/482)), reproduced
      deterministically before it is fixed, so the fix can say whether the shared connection
      is a test artifact or a real ordering bug.

4. **CI is tiered parallel jobs per app, behind one `ci-ok` check.** Inside each app the
   static checks, the tests, the generated-artifact checks and the "still fires" suites all
   start at the same moment, so a typo answers in a minute or two and never waits on the
   tests, and the tests never wait on it. The first shape
   ([#488](https://github.com/Raketa02/Raketa/issues/488)):
   - **Backend:** static (ruff, import-linter, mypy, Poetry pin drift); tests (split groups ×
     xdist, Postgres only where the one Postgres test runs); generated artifacts (contract
     freshness, judged pairings, ruleset diff, taskdef); meta (the purity gates and the "still
     fires" suites, over two jobs).
   - **Player:** static (eslint, prettier `--check`, tsc and the label rule — every static
     check `pnpm check` runs locally, two of which CI skips today — plus contract drift, which
     stays CI's own because it is not in `pnpm check`);
     tests (`--shard=i/3`, two workers, a cached transform directory); the deck in a job and
     a process of its own; meta (the import-boundary and drift proofs).
   - **Always:** the guardrail hooks and the ruleset release-report block.

   **One `ci-ok` job needs every job** and fails on any failure or cancellation; a job skipped
   because its app did not change passes. A newer push to a pull request cancels the older
   run; a push to `main` always finishes. Each app has one setup action that restores caches
   keyed on the **lockfile hash, never the branch**, and the Poetry install keeps a literal
   `poetry==<version>` so the pin-drift check still finds it. The job list is the first shape,
   not a contract; what this item fixes is *parallel tiers, every test, one summary check*.
   **Every new check proves it goes red**, the repo's idiom — the shards-add-up check and
   `ci-ok` itself included.

5. **Growth is absorbed by adding shards.** The backend suite splits into N groups with
   pytest-split, from a committed durations file refreshed by a make target
   ([#489](https://github.com/Raketa02/Raketa/issues/489)). Every collected test lands in
   exactly one group, and a test missing from the file is given the average duration, so
   **stale durations unbalance the shards and never drop a test.** CI fails when the shards do
   not add up to the whole suite, so a sharding mistake cannot produce a green run that tested
   less. When the wall-clock creeps, the answer is another shard, never fewer tests.

6. **A failing test fails the run, the first time.** No retry-until-green — no
   `pytest-rerunfailures`, no `jest.retryTimes`, no habit of re-running failed jobs until one
   passes — and **no flaky quarantine**. The only flake the measurement found was a real race,
   and a retry would have turned it green on the second attempt and buried it for good. A test
   that fails some of the time is a bug report about the test or about the code, and it is
   fixed red → green the way #482 fixes the race. A quarantine list is a list of tests the gate
   no longer runs, which is item 1 broken through a side door. Re-running a job whose
   *runner* failed — lost communication, a cache that would not download — is not a retry of a
   test, and stays allowed.

7. **The runner is 2 vCPU / 8 GB, and the workflow says so.** That is GitHub's standard
   `ubuntu-latest` for a private repository. Worker counts and heap limits are sized from it,
   and the number is written in the workflow beside the settings it sizes; the comment that
   says 16 GB is corrected in #488. Larger or self-hosted runners are out of scope for #480,
   not rejected: shards come first.

## Rejected

From the source article, each with its reason:

- **Affected-only tests as the gate.** Adopted for the inner loop (item 2) and refused for the gate,
  for the two measured reasons in *Context*: the player app selects most of itself, and
  testmon cannot see the tests that read the source tree as text.
- **Retry-until-green.** It would have hidden the one race the measurement found (item 6).
- **Flaky-test quarantine.** It is a subset gate with a friendlier name (item 6).
- **A Node or Python version matrix.** The project ships one Node and one Python. A matrix
  multiplies every job to test runtimes nothing deploys.
- **LLM self-healing commits in CI.** A fix is written and reviewed on the laptop, through
  `/implement` and `/code-review`, before it is pushed. A commit CI writes to itself is a change
  nobody reviewed, pushed onto a branch somebody else owns.

Not taken now, and not rejected: upgrading Python to 3.12+ for coverage's cheaper `sysmon` core
(a runtime decision of its own), fixing the deck suite's 5.4 GB heap (it keeps its own process
here), and a snapshot of the seeded world for the five seed-cohort tests (under xdist they
spread across workers).

## Consequences

**Easier**

- **A push answers in about five minutes instead of about an hour** (extrapolated from laptop
  timings at today's CI-to-laptop ratio of about 1.5×; #488's pull request measures the real
  ones), and the full backend suite at the end of a ticket costs about a minute and a half.
- **Every test still guards every change.** The fences that read the source as text run on
  every push exactly as they do today.
- Static failures show up within a minute or two, beside the tests rather than ahead of or
  behind them.
- One status says whether a push is green, and a superseded push stops costing minutes.
- **Billed minutes should drop too**, from about 70 per push to about 25–30, though there are
  more jobs; the repository is private, so Actions minutes are billed.
- A suite that grows gets a new shard, not a longer wait.

**Harder**

- **The workflow gets much bigger.** One job per app becomes about a dozen jobs, a setup action
  per app, a cache per toolchain and an aggregator. Every new CI check has to decide which tier
  it joins and has to come with its own proof that it goes red.
- **The loop and the gate can disagree, by design.** A change can be green under
  `make test-affected` or `pnpm test:affected` and red in CI, because the inner loop cannot see a
  fence the gate runs. That is the gate working, and it will feel like CI being wrong.
- **Parallel-safety becomes a property the suite must keep.** A test that shares state across
  processes — a file, a port, a global — now fails intermittently instead of never, and item 6
  means it fails the run. The first one is #482; there will be others, and each one blocks
  merges until it is fixed properly.
- **No retry means an infrastructure hiccup still costs a manual re-run,** and telling a lost
  runner from a flaky test is a judgement somebody has to make honestly each time.
- **Coverage stops being on every run's screen.** A drop is visible nightly and on `main`, not
  in the pull request that caused it; nobody reads it unless they look.
- **A deployed environment has one more way to refuse to start**, and a later wish to lower
  production's cost — for a login-latency target, say — has to argue with that refusal first.
- **The durations file is one more committed artifact**, which goes stale quietly. Stale is
  harmless by construction (item 5), but an unbalanced shard is minutes nobody sees being lost.
- **`ci-ok` becomes the required check only by a GitHub setting**, and
  ADR-0180
  records that a private repository on this free account has no branch protection. Until the
  plan changes, `ci-ok` is the one status a human reads before merging, not one GitHub
  enforces.
