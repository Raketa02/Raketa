# ADR-0170 — A player may write one line, and it is read as their own

- **Status:** Accepted — **§1 and §2's *100 characters* amended 2026-11-03 by
  [ADR-0200](0200-a-level-is-asked-where-play-begins.md) §9**: an intro is up to 250 characters. One line,
  optional and the contact fence stand. The step's paragraph of rules goes, and the contact rule is
  said only when broken.
- **Date:** 2026-09-14
- **§5's *not editable yet* ended by [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §6** — the You tab is the surface that
  edits the intro, the tags and the photos as one piece of work; `IntroChanged` joins the stream.
- **Amends** [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md) §2's closed
  list by one field, **`intro`**, and takes §3's first refusal — *"No bio, and no free-text field
  of any kind on a card. If a player is ever to write a sentence about themselves, that is its own
  decision with a moderation story attached"* — as the invitation it was: this is that decision,
  with that story. §3's second refusal (no activity recency) and §4 (no name, nothing shortens
  one) stand untouched. Amends [ADR-0089](0089-player-profile-context-event-sourced.md)'s event
  list by one event.
- **Moves** the root glossary's *A bio* out of *terms this context refuses* and defines
  **Intro** in its place, with *bio*, *tagline*, *about* and *status* as words to avoid.
- **Leaves standing** the closed Social tag vocabulary — *never free text, never
  player-authored* — which is about scoring and this line is never scored;
  [ADR-0129](0129-the-photo-check-is-a-sidecar-the-backend-asks.md) — the photo check is a
  sidecar, and §2 says why the line gets no sidecar today; and
  ADR-0104 — the card is attached to
  the search record when it is served, so a line is read as it stood at the deal.
- **Does not decide** editing the line after onboarding (§5), reporting a line (§2), or a second
  language for it.
- Settles the intro half of the Players deck spec
  ([#438](https://github.com/Raketa02/Raketa/issues/438)) and is built by the same backend and
  client children. Grilled 2026-09-14, in the same session as
  [ADR-0169](0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md).

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The search card, the candidate index and the Players deck are gone, so §3's `player_card.intro`, §4's deck-card and shortlist rules, and the Consequences about a search record carrying the line describe nothing. The intro itself is live: one optional line of at most 100 characters, its own event, refused at the write for contact (§1–§2), drawn on the player record. Sign-up still asks for it between tags and photos and now ends on *Who you play with*, because the opt-in it was to precede was removed (#581, #582). Editing arrived with ADR-0179.

## Context

**The deck card quotes a sentence nobody can write.**

The Players mocks (ADR-0169) put a line in italics between the meta line and the tags — *"Two
games in. Moved here in September, still learning the city."*, *"Will travel for a hard game."*,
*"Perfect attendance. Brings the shuttles and a friend."* — and every one of them is the kind of
sentence a person writes about themselves. No such field exists. ADR-0107 §3 refused it by name:
free text about oneself, shown to strangers, is a moderation surface before it is a feature, and
the Social tag vocabulary was closed for the same reason. The glossary lists *A bio* under *terms
this context refuses*. The player profile is an event-sourced aggregate (ADR-0089) whose events
name tags, photos, availability, location, radius, gender, opt-in and intent — and no text.

The grilling put both options to the author: drop the line, or add the field as its own feature.
The answer: *"I would go with b. This is something I was planning to add in the onboarding, so
now is the right time."* ADR-0107 §3 predicted the request in those words — *"players want to
say something about themselves"* — and asked that the proposal start from the reason. It does:
the reason was moderation, and §2 is the moderation story.

**What the platform has to hold a line with.** Photos get a CLIP sidecar on upload (ADR-0129); a
block exists for a person; there is no report mechanism for anything. The only free text on the
platform is a plan's *place* line and chat messages, neither shown to strangers. A player can
change availability, radius and declaration after onboarding — not tags, not the photo.

## Decision

### 1. The intro is one line, up to a hundred characters, and optional

**A player may write an intro: one line about themselves, at most 100 characters after
trimming, no line breaks, in any language.** It is a fact about the player, not about a sport, so
it is one per player. It is **optional**: the onboarding step offers a visible *Skip*, and a
player who skips has no intro — not an empty one. The name is **intro** — *your intro* on the
screens, `intro` on the wire — chosen over *bio* (which the glossary refused and which promises
a paragraph), *tagline* (marketing) and *about* (a heading, not a thing).

**It is its own event.** `IntroWritten` on the profile stream, emitted by the commit when the
line is present and not at all when it is absent — a blank leaves nothing behind, the shape
sportsmanship already takes. `PlayerProfileCreated` does not grow a field: an event stored
verbatim is read by every replay ever written, and an optional field that most streams lack is
the kind of thing an upcaster is later written for.

### 2. The moderation story is a rule at the write, and the fence is contact

**A line is refused at the write when it carries a phone number, an email address, a URL or a
handle** — `@name`, a bare domain, a number with enough digits to dial — and when it breaks the
shape (over 100 characters, a line break, nothing but whitespace). One code, `intro_not_admitted`,
with one coarse reason — `too_long | multiline | contains_contact` — so the client can say what
to change without the server explaining what it matched. The patterns are the backend's and
conservative: a false refusal costs a player a rewrite; a false admission leaks contact.

**Why contact, and why rules.** The realistic abuse of a line shown to strangers before any game
exists is not rudeness — it is *"WhatsApp me on …"*, which takes the arrangement, the reliability
record and the block out of the app. A rule catches that deterministically and a classifier would
not do it better. Rudeness is what a block is for, and a block already reaches every surface. A
text sidecar in the shape of the photo check is **not** added today: it is a dependency, a
latency and a false-positive rate bought against an abuse nobody has yet committed. If lines turn
out to need one, the sidecar is its own ticket and slots in where the rule runs.

**No report.** A player who sees a line they object to blocks the person; that is the whole of
the recourse, and it is the same recourse a tag or a photo has today. Named as a gap, not as a
feature.

### 3. It crosses on the card and on the record, and nowhere else

**`player_card.intro`**, a string, omitted when none — the one field ADR-0107 §2's closed list
gains, under §2's own admission rule (a fact about the person, assembled by `player_profile`,
projected to the candidate index like tags) and its size rule (a short string, paid per row, read
on the one surface that shows one person at a time). **`intro` on the player record**, omitted
when none. Not on a seat, not on a Chats row, not in a conversation header, not on a challenge
card: those are places a person is *named*, and the intro is a place a person *speaks*.

The card is attached to the search record when served (ADR-0104), so a deal shows the line as it
stood at the deal; the record sheet reads the current one. Today they cannot differ (§5).

### 4. It is drawn on the deck card and on the record sheet

**The deck card** draws it as the mock does — quoted, italic, between the meta line and the tags
— and closes the gap when there is none. **The record sheet** draws it under the person's name.
**Find a game's shortlist and pool cards do not**: those cards are about the game, and the line
is about the person — the same split ADR-0169 §8 draws between the two surfaces. The line is
never spoken as the player's name and never truncated: at 100 characters it fits the card's two
lines at the mock's size, and the cap is what makes an ellipsis unnecessary rather than a rule
that hides one.

### 5. It is asked once, after tags, and not editable yet

**A new onboarding step, *intro*, between tags and photos** — *you've picked your tags; now say
it in your own words* — with the opt-in still last, because nothing may come after the question
whose answer opens the commit. The step is part of the social part; a player who has already
finished onboarding is not sent back for it.

**Not editable after onboarding — with tags and the photo.** Today a player cannot change their
tags or their photo either; a single field editable while the two beside it are frozen reads as a
bug to a player. The intro follows tags: it becomes editable the day a profile-edit surface
arrives for all three, as one piece of work. Until then the commit is its only write, and the
field carries no route of its own.

## Consequences

- **The platform shows a stranger's own words for the first time.** Every earlier refusal of
  free text was a refusal of *this*, and the fence is one rule at the write. The day a line is
  hurtful rather than contact-shaped, the rule has nothing to say and the block is the whole
  recourse; that is the cost named here, and the sidecar is the escape.
- **The card grows one string, paid per row.** ADR-0107's size rule is met at 100 characters,
  and the line is still the first card field that is not a value or a code. The projection to the
  candidate index gains a case, and every search record from here on carries a line for whoever
  wrote one.
- **The mocks were drawn with a line on every card; most players will have none.** The layout
  closes up, so the card as built differs from the mocks for anybody who skipped, and the build
  is checked against both.
- **Contact rules have false positives.** *"Three sets, 100 zł to the winner"* dials nothing and
  may still trip a digit rule; the reason code tells the player what to change, and the pattern
  is tuned from refusals, not from a guess. A rule that lets a phone number through is the worse
  failure and is the one the tests exist for.
- **Frozen at the deal, editable never (yet).** Once editing arrives, old search records will
  quote lines their authors have since changed — ADR-0104's cost, extended to a sentence.
- **A step is added to onboarding, and optional steps get skipped.** The skip rate is the first
  number to read; if nobody writes, the deck cards look like the mocks minus their best line, and
  the step's copy is where that is fixed, not the field.
- **Language is the player's.** A Polish line beside an English tag row is what the product looks
  like in Kraków; nothing translates it, nothing asks for a second language, and a filter that
  reads only English would refuse nothing it should.
- **One event, no upcaster.** `PlayerProfileCreated` is unchanged; a replay of a stream with no
  `IntroWritten` folds to *no intro*, which is what those players have.
