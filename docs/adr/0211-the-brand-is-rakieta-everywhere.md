# ADR-0211 — The brand is Rakieta, everywhere

- **Status:** Accepted
- **Date:** 2026-11-27
- **Supersedes [ADR-0187](0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
  §8, *"The brand is Raketa, everywhere"*.** Its copy rule stands: the copy deck's rule against
  naming the app inside a sentence still gives way wherever a mock sentence names the app. The app
  it names is now **Rakieta**.
- **Supersedes [ADR-0209](0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md) §5,
  *"Rakieta is the splash's wordmark, and nothing else's"*.** The splash keeps its drawn wordmark,
  which is no longer an exception. The rest of ADR-0209 stands.
- **Leaves standing:**
  - ADR-0187's four deployables, its four contract documents (§5) and its rule that every address
    is a setting (§7);
  - [ADR-0006](0006-backend-owns-api-contract.md): the backend owns the contract, and each client
    generates its types from its own document;
  - [the-words.md](../specs/matchmaking/the-words.md)'s §F1 rule 6, *no Rakieta*, and its one
    exception;
  - every concept in the glossary. Only the brand word in its terms changes (§3).
- **Leaves the domain to [#888](https://github.com/Rakieta02/Rakieta/issues/888):** which domain it is,
  switching on the link domain and its association files, the mail sender's DNS, Stripe live mode,
  the store listings and hosting.
- **Settles PRD [#889](https://github.com/Rakieta02/Rakieta/issues/889).** Decided in the rename
  grilling on 2026-11-27 (Q1–Q20) and written by
  [#890](https://github.com/Rakieta02/Rakieta/issues/890). Built by:
  - [#891](https://github.com/Rakieta02/Rakieta/issues/891), the guardrails, CI, the root `Makefile`
    and the sandbox;
  - [#892](https://github.com/Rakieta02/Rakieta/issues/892) and
    [#893](https://github.com/Rakieta02/Rakieta/issues/893), *Rakieta settings* and *Rakieta hours*
    in the backend and the club website;
  - [#894](https://github.com/Rakieta02/Rakieta/issues/894) and
    [#895](https://github.com/Rakieta02/Rakieta/issues/895), *New in Rakieta* in the backend and the
    player app;
  - [#896](https://github.com/Rakieta02/Rakieta/issues/896),
    [#897](https://github.com/Rakieta02/Rakieta/issues/897) and
    [#898](https://github.com/Rakieta02/Rakieta/issues/898), the app's identity and its link scheme in
    the player app, the backend and the public site;
  - [#899](https://github.com/Rakieta02/Rakieta/issues/899) to
    [#902](https://github.com/Rakieta02/Rakieta/issues/902), the sweep of each app;
  - [#903](https://github.com/Rakieta02/Rakieta/issues/903), the local setup (by hand);
  - [#904](https://github.com/Rakieta02/Rakieta/issues/904) and
    [#905](https://github.com/Rakieta02/Rakieta/issues/905), the GitHub rename (by hand) and every
    link to it;
  - [#906](https://github.com/Rakieta02/Rakieta/issues/906), the feature-flag repo (by hand);
  - [#907](https://github.com/Rakieta02/Rakieta/issues/907), the brand check;
  - [#908](https://github.com/Rakieta02/Rakieta/issues/908), the walk (by hand);
  - [#909](https://github.com/Rakieta02/Rakieta/issues/909), the repo folder (by hand).

## Context

**The company will be called Rakieta, and its domain is bought.** Every surface players and clubs
touch still spelled the old name:

- the phone's launcher name, its OS prompts, its copy, its share texts and its pushes;
- the club website's tab title, and the desk's settings and hours, both named after the brand;
- the public site's pages and every email the backend sends.

**The brand had two spellings.** ADR-0187 §8 decided one name for every surface. ADR-0209 §5 then
made the drawn splash its one exception, spelled **Rakieta**. So a player saw one spelling on the
first frame and the other on every frame after it, and ADR-0209 named the cost: *"a future rename
touches both."*

**The name ran below the surface too.** It was in the API's paths and schemas, the app's bundle id
and link scheme, the event names in the event store, the phone's storage keys, the club website's
cookies, the JWT issuer, the Stripe metadata, every identifier and file name, the glossary's terms,
the local stack, the deploy artifact, CI, the GitHub account, every document and the repo folder.
In all, about 11,000 occurrences in 1,431 files, plus 30 paths.

**Now is the cheapest moment it will ever be.** Nothing is in a store, and no environment but
`local` runs. Once the app ships, its bundle id and link scheme are permanent, and every rename
after that needs a migration.

Rejected on the way:

- **Renaming only what people see.** The code, the contract and the docs would then spell one
  name and the product another. A search for a concept would find two spellings, and the old one
  would creep back through copied text.
- **Aliases and fallbacks** for the old paths, the old event names, the old storage keys and the
  old scheme. Nothing outside the repo calls the API, and all local state can be thrown away. An
  alias would protect nobody and would stay forever.
- **Renaming the concepts with the brand**, for example *Rakieta hours* becoming *Offered hours*.
  That needs a grilling of its own, and it would change meaning in a change that should only
  change spelling.

## Decision

### 1. The rule: letter for letter, with the case kept

*Raketa* becomes **Rakieta**, letter for letter, keeping the case: the lower-case form becomes
`rakieta`, the capitals `RAKIETA`, and the possessive *Rakieta's*. There are no diacritics and no
other variant. Identifiers that contain the brand follow the same rule: `RakietaSettings`,
`NEW_IN_RAKIETA_PATH`, `MY_RAKIETA_GROUP`, `pk_test_rakieta`.

**It applies everywhere:** the copy of all three clients, every email, the API contract, every
identifier, file and path, the stack, the deploy artifact, CI, every document and the repo
folder. Players see *Rakieta* on the home screen and on every frame after it, including the
badged builds' *Rakieta local*, *Rakieta development* and *Rakieta staging*. Clubs see *Rakieta for
Clubs*.

### 2. Everything is renamed in place, with no alias

**All local state is thrown away and re-seeded**: the database and its volume, the stored photos,
the app's data on the phone, the club website's sessions and the Stripe test objects. So every
rename is free, and nothing is kept for the old name:

- **No upcaster.** The stored event names become `clubs.rakieta_settings_changed` (v1 and v2),
  `clubs.rakieta_hours_set`, `clubs.rakieta_paused` and `clubs.rakieta_resumed`, and nothing
  registers the old names.
- **No alias.** The API's paths, schemas, operation ids and titles are renamed, among them
  `/api/v1/club/rakieta-settings`, `/api/v1/club/rakieta-hours` and `/api/v1/new-in-rakieta`. This
  is a public API behaviour change, and every client is regenerated in the same PR.
- **No old-key fallback.** The phone's storage keys, the club website's cookies, the JWT issuer
  and the Stripe metadata keys and idempotency prefixes are renamed. Every token issued before is
  refused, and each open desk is signed out once.
- **The old link scheme is not accepted.**

### 3. The glossary is renamed by substitution, and no concept changes

The terms become **Rakieta hours**, **Rakieta settings**, **Only Rakieta**, **Rakieta sells them
alone** and **New in Rakieta**. So does every definition that names the platform, and so does the
phrase *Rakieta's terms*, which the glossary doesn't define and the backend's `rakieta_terms`
module is named after. **In these terms the brand is the other party**: a club offers hours *to
Rakieta*. `CONTEXT-MAP.md` and each app's `CONTEXT.md` follow.

### 4. The app's permanent ids

- The bundle id and the Android package are **`com.rakieta.player`**.
- The slug is **`rakieta-player`**.
- The link scheme is **`rakieta`**, and the backend's scheme setting agrees with it.

They are settled before the first store submission, so they never change twice. They need not
match the domain. A new bundle id is a new app: the old one is uninstalled and its storage goes
with it.

### 5. The GitHub names

The product owner renames the account and both repos: the account to **`Rakieta02`**, its
monorepo to **`Rakieta02/Rakieta`**, and its feature-flag repo to **`Rakieta02/rakieta-features`**.
`Rakieta` alone is taken by another user. Then, in one commit, every link in the repo, the `gh`
instructions and the git remote point at the new names. GitHub forwards renamed repos, but anyone
may claim a freed account name, and that would break every forwarded link.

### 6. The documents say Rakieta, except where they quote the old spelling

**Every document is renamed in place**: ADRs, specs, research and decision logs, and the file
names of documents, mocks and prototypes, but not their pixels, which already draw *Rakieta*. This
is the one exception to the ADR index's *immutable once accepted*: an accepted record changes its
brand word and nothing else. The briefs and decision logs a spec folder calls *verbatim* are
verbatim but for the brand's spelling. The rename also reaches quotes of past copy, measured
values, the ids of past builds, the product owner's own folder paths and the mocks' original file
names.
ADR-0196 and the research note on what Rakieta has get new file names, and every link to them
follows.

**The one exception is text about the spelling itself.** These passages keep the old name as a
quote, each with a note pointing here:

- ADR-0187's status line and §8;
- ADR-0209's status line, §5 and its *two spellings* consequence;
- their two lines in the [ADR index](README.md);
- `the-words.md`'s exception to *no Rakieta*;
- the splash spec's notes on the two spellings.

Git history, and the text of past GitHub issues and pull requests, are left as they are.

### 7. The brand check lands last

**A permanent check fails CI when a case-insensitive search for the old name finds any tracked
file's content or any tracked path outside its allowlist.** It runs in CI and from `make brand`.
`make test-brand` proves it still fires against a scratch tree, three ways: a planted word, a
planted path, and one extra occurrence in an allowlisted file. It joins `ci-ok`'s `needs`.

**The allowlist counts occurrences per file.** It holds the passages of §6, this record, and the
check and its own test, which hold the pattern. One more occurrence in an allowlisted file goes
red, so allowlisting a whole file can't let a new one slip in.

**It lands last**, once nothing is left to rename, because it can only go green then.

## Consequences

**Easier**

- **One spelling on every frame.** The splash, the launcher and every screen after them agree, and
  ADR-0187 §8 has no exception left to police.
- **A search for a concept finds one spelling**, in code, contract, glossary and docs alike.
- **The old name can't creep back.** The check catches copied text, an old mock's name, or an
  agent's habit, on the day it lands.
- **The app's ids are settled before any store sees them**, so they are never renamed again.

**Harder**

- **The rename touches about 1,431 files on one branch.** Every other branch conflicts with it on
  almost every file, so nothing else can be in flight while it runs.
- **CI is red in between.** The contract changes in the backend before each client regenerates
  from it, so the clients' drift checks fail until the last client lands. The branch goes green at
  the end, not per ticket.
- **Some steps only a human can take**: the Stripe dashboard's names in test mode, the real `.env`
  files, reinstalling the app on the phone, removing the old stack's Docker leftovers, the GitHub
  rename and the repo folder's rename. A stale database URL in a real `.env` file means the
  backend won't start against the renamed stack.
- **All local state is lost**, on purpose. Anyone with a local stack re-seeds it.
- **The links in GitHub's own past issues and pull requests aren't rewritten.** They rely on GitHub's
  forwarding for as long as nobody claims the old account name.
- **The allowlist is a list someone must keep honest.** A passage that quotes the old spelling as
  history raises its file's count, and each raise is a review question.
- **History spells the new name too.** The mocks' source paths and original file names, a quote of
  past copy, a measured value or the id of a build once installed on the A32 now read *Rakieta*,
  though the product owner's folders, an old GitHub issue or the phone may still hold the old
  spelling. They are read as history, not as paths, strings or ids to type.
