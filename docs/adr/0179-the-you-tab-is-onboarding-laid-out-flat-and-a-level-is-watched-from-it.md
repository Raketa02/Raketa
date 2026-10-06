# ADR-0179 — The You tab is onboarding laid out flat, and a level is watched from it

- **Status:** Accepted
- **Date:** 2026-09-17
- **§9 amended 2026-09-29 by [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md)**: the tab gains an **Account** group — *Games & money*, *Payments*, *Notifications*.
- **§1's header card gains one element from [ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)** (2026-09-25): the profile switcher chip, in each profile (club mock 7). This record's own rule applied: the mock won and the record is amended. Everything else stands.
- **Amends** [ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) §6 by
  one shape — *no response shape carries a gender value out* gains the exception **the owner's
  own profile read**, and no other (§4); [ADR-0158](0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)
  §6's last sentence and its second amendment — *to the subject, a coarse band with no count*
  becomes **the published figure and its count, to the subject too** (§5), with the cost that
  record named written beside the reversal; [ADR-0170](0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)
  §5 — *not editable yet, with tags and the photo, the day a profile-edit surface arrives* — by
  being that day (§6); and the onboarding pass's *there is no re-take from inside the app* —
  a pass may now begin at the passport (§3).
- **Decides** what [ADR-0171](0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
  left open — *editing the name or the nickname from the You tab after onboarding* — the same
  act, from a row (§7).
- **Leaves standing** [ADR-0089](0089-player-profile-context-event-sourced.md) — every write
  here is one of the aggregate's existing transitions, and the one new event (`IntroChanged`)
  is on the shape §5 of that record set for later edits; [ADR-0094](0094-play-intent-declared-per-sport-in-its-own-aggregate.md)
  — the declaration section moves behind a row and changes nothing; [ADR-0174](0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
  §6 — the location's route is the cold start's, and a person pressing a control sends the same
  request; [ADR-0012](0012-player-app-design-system.md) — every screen composes objects the
  locked system already draws, and the two things without a numbered home are Part 16 rows.
- **Does not decide** blocked players on the tab (§9), a block control on any client surface,
  changing email or password, deleting an account, notifications, a games history.
- Settles [#465](https://github.com/Raketa02/Raketa/issues/465); the surface is
  [`docs/specs/you/the-you-screen.md`](../specs/you/the-you-screen.md) and the walkable
  prototype beside it, which is **locked**: where the prototype and a record disagree, the record
  is amended — this one first. The sentences are `the-words.md` §27. Decided in session
  2026-09-17 with the author, from a prototype walk over every screen; not grilled, because every
  question the walk raised was answered on the prototype itself.

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** *How far to look* and *Game suggestions* are gone with the search radius and the proposals opt-in (#581, #582), so their rows in §1 and §2, §2's opt-in write and radius paragraph, and §8's `proposals_opt_in` field and its `PUT` no longer exist. §9's block control *on the deck card* has no deck card to go on; a block is made from the player record (ADR-0193). Everything else stands.

## Context

**The tab says it is not built, and three sections sit under the sentence.** `YouScreen` is the
shell's one placeholder — *Your profile, your radius, your week — not built yet* — composing
the per-sport declaration (#296), the one sentence about the Location area (ADR-0174 §6) and the
account panel with *Sign out*. Everything else a player declared in onboarding is held on the
server, editable by the aggregate, and reachable from no screen.

**Onboarding promised the tab, four times.** The opt-in step says *you can stop any time, from
your profile*; the gender step says *you can change this later in your preferences*; the location
step says *set your area later from your profile* and its own record says *the area is editable
from the profile afterwards*; the profile surface's type says tags, photos and the area *are a
deferral this same route grows when You is built*. A promise a player has read is a debt.

**The backend built the edits before the screen.** `PlayerProfile` has one transition per
changeable fact under a heading that reads *Later changes, from the profile screen* —
`change_social_tags`, `change_photos`, `change_availability`, `change_location`,
`change_search_radius`, `change_gender`, `change_gender_preference`, `answer_proposals_opt_in`
— and `ConsentSurface.PROFILE` exists with a docstring saying *the endpoint that drives it does
not yet*. Three of the eight have routes. The intro has none, by ADR-0170 §5's own
reasoning: one editable field between two frozen ones reads as a bug, so it waits for the surface
that edits all three.

**The two things a player cannot edit are the two they most want to look at.** A Level is proved,
never declared; a Player Score is what the platform watched. The record sheet already draws both
— `GET /players/me/record`, ungated, *the same sheet everybody else is shown about you* — and
the onboarding result card already draws a rating with its confidence and its band. The tab
needs doors to those two drawings more than it needs anything new.

**The prototype settled the shape by walking it.** Every screen was drawn twice: first as a fresh
design, then — on the author's instruction, screen by screen — as the onboarding step or the
record section that already exists, with its explanatory prose removed. The second walk is the
decision. The principle it produced is the one ADR-0089 wrote in advance: *the profile editor
will obey these rules from a screen that looks nothing like this one* — and it turns out the
screen should look exactly like the step, because a player who set a value on a step recognises
the step when they come to change it.

Two of the walk's demands contradict accepted records, and both are privacy decisions rather
than drawings: the owner reading their own gender and preference (ADR-0096 §6), and the subject
reading their own sportsmanship figure (ADR-0158 §6). Neither is overridden quietly; §4 and §5
argue each and name what it costs.

## Decision

### 1. The tab: a header card, three groups, and *Sign out* where it is

**We will build You as one header card over three titled groups of rows**, each row a title, a
**live** one-line summary drawn from the read, and a chevron — [5.5](../../frontend_player/docs/design-system.md#55-row--the-key-value-line)'s
key-value row in a card, under a section title in `flab`:

```
header card       dark card — photo or poster · name · @nickname · intro · one sport pill per
                  rating · the Player Score ring — tapping it opens §2's record
PLAYING           Skill passport · Player reliability · What kind of game
FINDING PLAYERS   Your week · How far to look · Where you play · Who you play with ·
                  Game suggestions
ON YOUR CARD      How others see you · Photos · Tags · Intro · Name
Sign out          the account panel's button, at the foot, as today
```

Three groups because the rows answer three questions — *what has the platform concluded about
me*, *what does the matcher read when it looks for a game*, *what does a stranger read about me*
— and a fourth question, *the account*, is not asked on this tab (§9). The shell keeps what it
has always owned — the tab's title and the group titles — and composes; every row from *Skill
passport* down is `player_profile`'s, `player_record`'s, `onboarding`'s or `auth`'s. The
placeholder sentence goes, and `PlaceholderTab` becomes an empty union: the fifth tab has left the
table.

### 2. Every screen is the step or the sheet it came from, and nothing is explained twice

**We will draw each row's screen as the onboarding step that first collected the value, or the
record section that already draws it, reused as a component and stripped of its onboarding
chrome** — the eyebrow's *Step N of 8*, *Continue*, the note that argued for the value on first
asking. What a step said once, on the way in, is not said again on the way back:

| Row | Screen | What it is, exactly |
| --- | --- | --- |
| Skill passport | one card per rating | `ResultScreen`'s **`Verdict` dark card** — *Your level*, the figure, the likely range, the confidence ring with its ceiling tick on an Initial estimate, the on-dark level bar and legend, *Band* and *Rating status* as rows — with the **sport tag and a status chip** across its top; **`RecordBlocks` under each card** (*Player reliability · Last 5 · Counted*, the first the whole person's and the same on every card, the other two this sport's); then *Add a sport* (§3) and the ladder |
| Player reliability | the ring, then the rows | the Player Score in `ConfidenceRing`'s drawing on a dark card with the tone ladder's word, then **`RecordCard`'s rows as it draws them** — each strand's name and raw pair over its `Meter`, opponent variety, sportsmanship (§5). No weights, no sentence under a row, no card explaining what the number changes |
| What kind of game | `PlayIntentsSection` | as built, under one line — *This changes how people find you* — and without its heading, body or note |
| Your week | `AvailabilityGrid` | as `SocialAvailabilityStep` draws it — days down, parts across, the mint tick, the footnote inside the card — with *Save your week* and *Clear all*. The commit's floor of one slot does not bind: an empty week is a legal value and the footnote says what it means |
| How far to look | `RadiusSlider` | the figure, the words, the slider, and **a *Save* button** |
| Where you play | the location step's control | *Your area is set* with the tab's one sentence — the only state, because onboarding cannot finish without an area — and *Read my area again* in the step's three permission states; nothing else — no map, no name, no coordinate, and nothing on the read to branch on |
| Who you play with | `SocialGenderStep`'s two groups | each with its own *Save*; the reach sentence at the moment of the press; the step's scope sentences not repeated |
| Game suggestions | the opt-in step's promises | the three promises, the standing answer with its date and copy version, the two answers |
| How others see you | `PlayerRecordSheet` | `{ kind: 'me' }`, section for section, retitled — nothing added and nothing removed |
| Photos | `SocialPhotosStep` | the rule note, `PhotoRow`, `PhotoAddTile`, the poster tile, the two lines, the hold-for-options sheet, the flagged notice; the step's *Continue* is the one thing not there |
| Tags | `SocialTagsStep` | the eyebrow with the served bounds, the step's question as the title, the chips, the ceiling note; *Continue* is *Save*, shut under the floor with the step's own words |
| Intro | the intro step's box | the label, counter, hint, rule, the two shape refusals; *Save* and *Remove intro* |
| Name | `NamingScreen` | the two fields under their labels and *Save*; no sentence explains them |

**Two writes are not saved by a button.** Photos write on every change to the row — a
promotion, a removal, an upload that landed — because the step has no *Save* and the row is the
state. The opt-in writes on every press, including the same answer again, because consent is
evidenced and a re-affirmation against these words is a fact (ADR-0089). Everything else is a
draft until *Save*: the week, the radius, the tags, the intro, the name, each of the two gender
groups.

**The radius is saved by a button on You and by the search on Play, and the two are one
number.** Find a game writes the radius as the first half of pressing the card; that stays. On
You a slider that wrote on release would save a value the player was still deciding, so it does
not.

### 3. A pass may begin at the passport: *Add a sport*

**We will let a player rated in some sports rate another from the passport.** *Add a sport*
draws one chip per unrated sport; the chip begins an **onboarding pass of exactly one sport**, at
the question route, ending on the result card's *See your ratings* — which, for a pass begun
here, lands on the passport and not on the done screen, the data screen or the social steps,
because a profile already exists and the other screens are onboarding's.

This narrows the client glossary's *onboarding happens once, at the beginning — there is no
re-take from inside the app*. The rule's reason stands — a link naming a sport outside a running
pass is still sent to welcome, because a hand-built URL is not a shortcut into the middle of a
flow — and gains a second legitimate beginning: a pass has an **origin**, welcome or the
passport, and where it ends is read off it. Everything between is untouched: the question
screens, revision, the review, the calculating screen, the result card, the assessment routes.
Leaving mid-run offers the same sheet as onboarding — continue later, or abandon — and a run
deferred is held for the app session exactly as today; the entry gate's *resume* branch keeps
its rule, so a run begun here and left unfinished is resumed on the next cold launch like any
other. The new rating's Play intent is **undeclared** until the player declares it on *What
kind of game* or Play's interstitial, as every sport's is today; the passport's row says so.

### 4. The owner reads their own gender and preference — on one route, and no other

**We will serve `gender` and `gender_preference` on `GET /players/me/profile`**, and on no
other response shape. ADR-0096 §6 — *no response shape carries a gender value out, and no card
renders one* — is about responses that describe one player to another, and its test walks every
shape a stranger reads. A player reading their own answer on a route scoped to `me` is not what
§6 protects, and a screen that asks *who should we match you with* with nothing pre-selected is a
screen a player cannot trust: *did I set women only, or not?* is the exact fact the reach
sentence exists to make legible. §21's test is **extended, not weakened**: it asserts the two
values appear on that one shape and on none of the others. The profile read's own promise —
*withheld and always will be* — is rewritten to say what is withheld from whom.

### 5. The sportsmanship figure crosses to its subject, and the cost is named

**We will serve `sportsmanship` — the published average and the count of distinct raters — on
`GET /players/me/record` as it is served to any other reader, and retire `sportsmanship_band`.**
The record sheet then draws one row for everybody: *Sportsmanship, by players · 4,3 / 5 · 12
players*. ADR-0158 §6 withheld the figure from its subject for one reason, and the reason is
still true: an average beside a count is a subtraction — *moving from 4,80 over ten to 4,73 over
eleven names the new rating as a 4, and they know who they played* — so a rater becomes
identifiable to the one person they rated. The author has weighed that against a player being
told *Mixed* about themselves with no number to work on, and chosen the number. What holds it
in check is what ADR-0158 built and keeps: the collapse (a regular partner is one rater however
many evenings), the fifty-rater window, no zero on the scale, the matcher never reading it, and
no individual rating on any route. What is given up is stated plainly in the Consequences.

### 6. The intro, the tags and the photos are edited as one piece of work

**We will add `IntroChanged` to the profile stream and a route for it, and ship it with the
tags' and the photos' routes.** ADR-0170 §5 said the intro becomes editable *the day a
profile-edit surface arrives for all three, as one piece of work* — this is that surface, and
the three land in one backend ticket and one client ticket so that no field is editable while
the two beside it are frozen. The fence is unchanged: a line carrying a phone number, an email, a
URL or a handle is refused with `intro_not_admitted` at the write, and the two shape refusals are
pre-empted on the client as the step pre-empts them. A removal is a write of no intro — the
stream records that the line was withdrawn, and the profile folds to none. Search records already
kept quote the line as it stood at the deal (ADR-0104, as ADR-0170 accepted).

### 7. The name and the nickname are edited from the tab, by the same act

**We will open `NamingScreen` from the *Name* row**, pre-filled, saving through
`PUT /users/me/name` — the act ADR-0171 already made repeatable. A nickname another player holds
is refused by the server with `nickname_already_taken`, and the screen says *That nickname is
taken. Pick another.* under the field — the check is the server's on *Save*, never a lookup
while typing, because a handle search is the enumeration ADR-0159 refuses. Every sentence that
names the player says the new name from the next read; the poster's initials follow.

### 8. The wire: one read grows, six writes land, and nothing else is added

**We will grow `GET /players/me/profile`** — the route whose own description said *there will be
no second endpoint* — by `social_tags`, `photos` (ids in order, each with its verdict as the
uploader is owed it; an empty list is a real answer), `intro` (omitted where none),
`proposals_opt_in` (`accepted`, `answered_at`, `copy_version`), and §4's two values. **Not
`has_location`**: a profile cannot be committed without an area, so every profile the tab can
read holds one and a flag would always be true. **We will add six writes**, one per fact, each the aggregate's existing transition:

| Route | Transition | Note |
| --- | --- | --- |
| `PUT /players/me/social-tags` | `change_social_tags` | re-validated against the served vocabulary and bounds |
| `PUT /players/me/photos` | `change_photos` | ids in order, each owned by the caller; empty clears |
| `PUT /players/me/intro` | **`IntroChanged`** (new) | the fenced line, or no line |
| `PUT /players/me/gender` | `change_gender` | no-op on an unchanged value |
| `PUT /players/me/gender-preference` | `change_gender_preference` | no-op on an unchanged value |
| `PUT /players/me/proposals-opt-in` | `answer_proposals_opt_in` | **always records**; `surface: PROFILE`; `copy_version` from the screen |

Every write is unkeyed and idempotent on the profile surface's own argument — a `PUT` that
lands the same state twice has nothing to deduplicate — except the opt-in, which records twice
on purpose. The week, the radius, the location, the declaration and the naming keep the routes
they have.

### 9. What is not on the tab

**No Account group.** Blocked players would need a read that does not exist (`GET /blocks`, the
caller's own list with names and faces) and, more to the point, **no client surface makes a
block today** — a screen that only lifts blocks nobody can place is a screen for a control that
is not there. It returns with the block control on the record sheet and the deck card, as one
ticket, and `DELETE /blocks/{player_id}` is waiting for it. Email, password and deletion have no
routes and no design; erasure is a domain concept with no act behind it. *Sign out* is not
affected: it stays at the foot of the tab as the account panel draws it today, the only way out
of a session.

**Nothing explanatory.** *Nobody types a level in*, *what it changes*, *what clears it*, *a
preference, not a promise*, *why we ask your location* — each was on the first draft and each is
gone, because the passport is the result card and the reliability screen is the record card, and
each already says what it is.

## Consequences

- **The tab is built from parts that exist**, and every editing screen is the step it came from.
  A rule retuned on a step — the tag bounds, the radius bounds, the photo ceiling, the intro
  fence — is retuned on the tab in the same commit, because there is one component. The cost is
  that the steps grow a second caller with different chrome: each step's layout has to separate
  *the control* from *the onboarding around it*, which is refactoring inside `player_profile`
  before the first row draws.
- **A rater becomes nameable by their subject** (§5). ADR-0158 §6's subtraction is real and
  this record does not pretend otherwise: a player who watches their average move after each
  evening can attribute the change to the one card that closed. The collapse and the window
  blunt it — a partner's twentieth evening changes nothing, and fifty people is a crowd — but a
  player with three raters reads three opinions and knows three names. The mitigation kept is the
  one ADR-0158 §2 already accepted: the band was *deliberately too coarse to be informative about
  any individual*, and the figure is not. If honest answering falls off, this is the sentence to
  reopen, and the band is one amendment away.
- **Gender leaves the server on one route** (§4). §21's test is the fence, and it is now a test
  with an exception in it, which is a weaker sentence than *never*. The exception is one shape,
  scoped to `me`, and every stranger-facing shape is asserted clean as before.
- **The passport repeats one number** — *Player reliability* on every sport's card — because the
  blocks are reused whole and the author preferred the record's row intact under each card to a
  card with two blocks. A player rated in four sports reads their score four times.
- **A second door into the onboarding pass** (§3) makes the pass's origin a fact the ending reads.
  The entry gate's *resume* branch is unchanged, so a run begun from the passport and abandoned by
  killing the app is resumed at the next cold launch — the same rule as a deferred onboarding
  run, and arguably a surprise for somebody who was browsing their profile. The leave sheet's
  *continue later* is the remedy, as it is in onboarding.
- **The contract grows on one read** and six writes land; the client's wire types regenerate and
  the drift check is red between the backend tickets and the client tickets that follow them, by
  design. `sportsmanship_band` leaves the record's shape, so the client's two-armed `Opinion`
  collapses to one — a type made unrepresentable on purpose becomes representable on purpose.
- **Photos write on every change.** A player rearranging three photographs sends three `PUT`s;
  each is idempotent and the last one is the state. The alternative — a *Save* the step never
  had — was refused because the row is the truth and a draft of it would be a second one.
- **The words are the steps' own**, so `the-words.md` §27 is short: the group titles, the live
  lines, the passport's chip and status words, one line under *What kind of game*, the reliability
  ladder's three words, the *Save* labels and the area screen's states. Everything else is
  quoted from an earlier section.
- **What is deferred is named** (§9), and blocked players is the one a player will look for and
  not find. Until the block control exists nowhere, the absence is honest.
