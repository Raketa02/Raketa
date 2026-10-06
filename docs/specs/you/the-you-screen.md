# The You tab — what it holds, and what each row changes

**Status:** decided, 2026-09-17 — [ADR-0179](../../adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
records the decisions, the PRD is [#465](https://github.com/Raketa02/Raketa/issues/465) and the
tickets are its children. Investigated against the codebase as it stood on
`feat/RKTA-05_chats_and_now_game_cards`; it has been built since (#466–#473). The walkable
prototype is [`the-you-prototype.html`](the-you-prototype.html) — it predates the removal of
*How far to look* and *Game suggestions* with Classic play (2026-10-06, #581, #582) and still
draws both. Open it in a browser (a `#passport`, `#record`, … hash opens a screen directly),
tap every row, and read the notes panel beside the phone: it names the read, the write and the consequence for whichever
screen is open, and logs every request the screen would send.

## 0. The one sentence

**You is where a player reads what the platform holds about them and changes the facts they
declared** — and the two facts they did *not* declare, the Level and the Player Score, are the
first two rows because they are the two a player most wants to look at and the two they cannot
touch. *A level is proved, never declared*; *a Player Score is what the platform watched*. Both
are drawn as graphics, neither has a control.

Everything else on the tab is a **declaration**, and every declaration was first collected in
onboarding. The tab is onboarding's second part laid out flat, with the questionnaire's output
and the record on top — which is exactly what
[ADR-0089](../../adr/0089-player-profile-context-event-sourced.md) said would happen when it
put the rules in `features/player_profile/` rather than in `onboarding/`: *"the profile editor
will obey these rules from a screen that looks nothing like this one."* **Every editing screen
on the tab is the onboarding step that first collected the value, reused**, and the two
read-only screens are the onboarding result card and the player record, reused. Nothing on this
tab is a new drawn object.

## 1. Where the rows come from

### 1.1 What onboarding collects, in order

| Step | Fact | Where it is written | Changeable later? |
| --- | --- | --- | --- |
| Sign-up | email, password, **Adult attestation** | `POST /users` | No route for email or password; the attestation is a precondition of holding an account, never re-asked |
| The naming | **Name** and **Nickname** | `PUT /users/me/name` — *repeatable* | Yes — the route exists; ADR-0171 explicitly left the You-tab screen as a follow-up |
| The questionnaire, per sport | **Skill rating** — Level, uncertainty, band, status | Completion of an Assessment | **Never.** Only a confirmed counted result moves a Level. A *new* sport can be rated — §3.1 |
| The tail of every rating run | **Play intent**, per sport | `PUT /play-intents/{sport}` | Yes — already a section on You (#296) |
| Social step 1 · tags | 2–6 **Social tags** from a closed vocabulary | the profile commit | Aggregate method exists, **no route** |
| Social step 2 · intro | one line, ≤ 100 characters, fenced against contact | the profile commit | **No change method and no route** — ADR-0170 §5 |
| Social step 3 · photos | up to three, first is the profile photo, each on-court-checked | `POST /photos`, then the commit | Aggregate method exists, **no route** |
| Social step 4 · availability | the 7 × 3 **Availability grid** | the profile commit | Yes — `PUT /players/me/availability` |
| Social step 5 · location | the coarse **Location area** | the profile commit | Yes — `PUT /players/me/location`, but it is *the cold start's write, and no screen's* |
| Social step 6 · gender | **Gender** and **Gender preference** | the profile commit | Aggregate methods exist, **no route**, and the values are **never served back** |

### 1.2 The promises the app has already made

Four sentences a player has already read say that something is editable *from your profile*.
The tab has to make them true, and each is a row below:

- Gender step: *"You can change this later **in your preferences**. It applies to every search."* → §3.7
- Location step: *"…continue and set your area later **from your profile**."* → §3.6 (the
  finish then insists on it, so *later* has always meant *before the end of setting up*; the
  row keeps the promise for re-reading it)
- Location step's docblock: *"the area is editable from the profile afterwards."* → §3.6
- `PlayerProfileSurface`: *"tags, photos and the location area are a deferral this same route
  grows when **You** is built."* → §3.6, §3.10, §3.11

### 1.3 What the tab carries today

`shell`'s `YouScreen` is still a placeholder — *"Your profile, your radius, your week — not
built yet"* — with three sections composed under it: `PlayIntentsSection` (#296), the
`AreaUpdatesNote` (ADR-0174 §6) and the `AccountPanel` (name, `@nickname`, email, *Sign out*).
The first two become rows; the panel's *Sign out* stays at the foot of the tab, where it is.

### 1.4 What the backend already supports

`PlayerProfile` has one method per changeable fact under a heading that reads, verbatim, *"Later
changes, from the profile screen"*: `change_social_tags`, `change_photos`,
`change_availability`, `change_location`, `change_gender`, `change_gender_preference`. Two
have routes.

`GET /players/me/record` — *"the same sheet everybody else is shown about you"* — already
carries the name, handle, photo and its on-court verdict, the intro, the tags, one pill per rated
sport, the skill panel (level, band, confidence, counted games, likely range, last five), the
reliability pill with its metered rows, opponent variety, and the sportsmanship **band** (the
figure was withheld from its subject; ADR-0179 §5 reverses that — §5.3). The client already draws all of it as
`PlayerRecordSheet` with `{ kind: 'me' }`. **The two graphics the tab wants exist; what is
missing is a door to them from the tab.**

## 2. The screen

```
ScreenHeader      eyebrow PLAYER PROFILE · h1 You
  header card     dark card: photo or poster · name · @nickname · intro · sport pills · score ring
                  → taps open §3.9 How others see you

  PLAYING         Skill passport · Player reliability · What kind of game
  FINDING PLAYERS Your week · Where you play · Who you play with
  ON YOUR CARD    How others see you · Photos · Tags · Intro · Name

  Sign out        AccountPanel's button, at the foot — as today
```

Three groups, because the rows answer three different questions: *what has the platform
concluded about me* (read-only), *what does a proposed game read about me* (declarations the
new games read: the proposer reads the week and the Play intent, the pair rule on every court
reads the gender preference, and every distance to a club is measured from the Location area),
and *what does a stranger read about me* (the card and the record). The groups are section
titles over cards of rows — [5.5](../../../frontend_player/docs/design-system.md#55-row--the-key-value-line)'s key-value row
with a title, a **live** one-line summary drawn from the read, and a chevron.

**There is no Account group.** Blocked players and the account rows (email, password, deletion)
were on the first draft and are out — §4 says why and what each would need.

| Row | Live line (example) | Tap opens | Update | Status |
| --- | --- | --- | --- | --- |
| Skill passport | `Padel 2,71 · Tennis 3,10 · Squash 2,30` | the onboarding result card per sport, with the record's three blocks under each; *Add a sport*; the ladder | **none** on a rating; *Add a sport* starts a questionnaire | reads exist; questionnaire exists |
| Player reliability | `92 of 100 · 3 things counted` | the ring, then the record card's rows | **none** | read exists; one decision (§5.3) |
| What kind of game | `Padel Competitive · Tennis For fun · Squash not set` | one row per rated sport, expands to the three answers | in place, `PUT /play-intents/{sport}` | **built** |
| Your week | `10 slots ticked` | the availability grid as the step draws it, *Save* / *Clear all* | `PUT /players/me/availability` on *Save* | route exists, screen missing |
| Where you play | `Area set · updates when you open Raketa` | *Your area is set*, *Read my area again*, the permission states | `PUT /players/me/location` | route exists, screen missing |
| Who you play with | `Matched with anyone` | the gender step's two radio groups, each with *Save*; the reach sentence at the press | two new `PUT`s | **needs a decision** (§5.2) and two routes |
| How others see you | `Your player record, as a stranger reads it` | `PlayerRecordSheet` for yourself, section for section | none — the doors are the rows below | **built**, needs a door |
| Photos | `2 of 3 · profile photo on court` | the photos step as it is: tiles, add, promote, hold for options, the flagged notice | `POST /photos`, then `PUT /players/me/photos` on every change | needs a route and the read |
| Tags | `4 of 6 · Stays for a drink, Plays to win, +2` | the tags step as it is, with *Save* | `PUT /players/me/social-tags` | needs a route and the read |
| Intro | `“Will travel for a hard game.”` | the intro step's box with its counter and fence, *Save* / *Remove intro* | `PUT /players/me/intro` | needs an aggregate change + route, ADR-0170 §5 |
| Name | `Tomek Kowalski · @tomek.k` | the naming screen, pre-filled | `PUT /users/me/name` | route exists, screen exists (`NamingScreen`), needs a door |

## 3. Each row

Every row below answers the same four questions: **what it is**, **what opens**, **how the
update happens**, and **what changes in Raketa when a new value lands**. The last is the reason
the row is on this tab at all — a preference that changed nothing would be decoration.

### 3.1 Skill passport

**What it is.** The Skill ratings this player holds — one per rated sport, never per format —
each a Level on the 1,0–5,0 scale, its uncertainty, its band and its status. The word comes from
the original design (v37 §5.1) and survives because it is the right one: a passport is a document
other people read and you cannot write.

**What opens.** One card per rated sport, in the registry's order, and **the card is the
onboarding result's** — `ResultScreen`'s `Verdict` dark card, reused as it is:

- a row over it with the sport tag and the **status chip** — *Initial estimate* · *Calibrating* ·
  *Stable* — which is the one thing the result screen prints as a row and the passport prints as
  a chip, because a chip is how a list of three sports is scanned;
- *Your level* with its info mark, the Level in the display figure, the likely range with its
  info mark (`2,24–3,18 likely range`);
- the **confidence ring** (7.8) — the volt arc, the figure, *Confidence* beneath — with the 30 %
  ceiling tick where the rating is still an Initial estimate and no tick once real results have
  moved it;
- the **level bar** in its on-dark variant (7.5) with the four band names and the legend
  (*Your level* · *Likely range*);
- *Band* and *Rating status* as the card's two rows.

**Under each card, the record's three blocks** — `RecordBlocks` (7.13), reused: *Player
reliability* (the whole person's number, the same on every card), *Last 5* (this sport's run of
form, never padded) and *Counted* (confirmed counted results in this sport, `0` being a real
answer). They sit under the card as a sibling, exactly as they sit under the record's skill card.

Under the cards, **Add a sport** — one chip per unrated sport (*Rate Badminton*) — and **the
ladder**: the four bands with their edges and meanings, the player's own marked.

**How the update happens.** A rating has no control, and the domain refuses a manual edit rather
than a permission check guarding one. **Adding a sport is in scope and reuses the
questionnaire**: the chip starts one Assessment (`POST /assessments`) and walks onboarding's own
pass for exactly one sport — the question screens, the review, the result card, the Play intent
asked at the tail as it is for every rating run — and ends back on the passport rather than on
the social steps, because a profile already exists. Nothing already held changes; a rating is per
sport and the new one sits beside the others.

What the client needs for it: a **second door into the onboarding pass**. Today a pass begins
only at the welcome picker, and `onboardingPass.ts` says so in as many words — *"there is no
re-take from inside the app **yet**"* — so a link naming a sport outside a running pass is sent to
welcome. The change is a pass that begins at this chip with a queue of one and ends on the
passport; the routes, the question screens and the result card are untouched.

**What it needs from the contract.** Nothing new: `GET /ratings` for the cards,
`GET /players/me/record?sport=` for *Last 5* and *Counted* per sport, `POST /assessments` for a
new sport. All exist.

### 3.2 Player reliability

**What it is.** The Player Score — out of a hundred, computed from what happened and never from
opinions or results — and the rows the record draws beside it. Five rows, and the distinction
that matters is that **three of the five are strands and weigh on the number, and two sit beside
it and do not**:

| Row | Weight | What it counts | In the number? |
| --- | --- | --- | --- |
| Shows up | 35 | plans that settled → games that happened; a Ghost game is charged to everybody on that court | yes |
| Answers about results | 15 | scores put to you → answered inside the window; **a counter is as good as an acceptance**; forgets after twelve months | yes |
| Keeps plans | 12 | booked games whose hour came → kept with every seat held; **broken only by leaving** so that the game is called off at its cut-off, or after it with nobody taking the seat (#544) | yes |
| Opponent variety | — | different people over times on a court, whole record; two counts and the share | no — context for a Level |
| Sportsmanship, by players | — | what other players said | no — matchmaking never reads it |

*Answers challenges* stands down — challenges no longer wait for an answer (#544) — and *Settles
up* has nothing to measure, because the court money is taken up front; neither is a row.
*Confirms results* was struck and stays struck (ADR-0137). The weights are the player's own —
35 / 15 / 12 — renormalised over the strands that are there, and **they are not printed**: the
record does not carry them on the wire and the screen draws what the record draws.

**What opens.**

- a dark card: the **score ring** in volt with the figure, and the one word the record's tone
  ladder gives it (*Reliable* from 90, *Holding* from 70, *Under the bar* below);
- **the record card's rows, as `RecordCard` draws them** — each strand's name and its raw pair
  (`11 of 12`) on one line, the `Meter` under it at the served `pct` in the record's tone (mint
  from 90, night between, red under 70); then *Opponent variety* as `70% · 14 of 20`; then
  *Sportsmanship, by players* as **the figure and its count** — `4,3 / 5 · 12 players` — which
  is what the record prints to a *reader* and, since ADR-0179 §5, to the subject too (§5.3).

Nothing else. The explanatory cards of the first draft (*what it changes*, *what clears it*)
and the sentence under each row are gone; the rows are the explanation.

**How the update happens.** It does not. Only what the player does moves it.

**What it needs.** `GET /players/me/record`, which exists and is ungated — *"this is the one
screen a held player has for finding out how they appear."* Absence is honest: a player nothing
has fallen due for has no `reliability` at all, and the row says *nothing counted yet* rather than
drawing a nought. The sportsmanship figure needs §5.3.

### 3.3 What kind of game — Play intent, per sport

**What it is.** `COMPETITIVE · FOR_FUN · NO_PREFERENCE`, declared per rated sport, never inferred
and never transferred between sports. *Mode is one game's kind; intent is the player's standing
declaration.*

**What opens.** Under the title, one line — **This changes how people find you** — and then
`PlayIntentsSection` as it is built today (#296): one row per rated sport, the row expands in
place to the three answers with their glosses, the footnote where a sport is undeclared. The
section's heading and body sentence are dropped; the line under the title says what they said.

**How the update happens.** In place: pressing an answer sends `PUT /play-intents/{sport}` with
`surface: PROFILE_SCREEN`. Idempotent — the same value twice records nothing. The value drawn is
the route's answer arriving in the cache, never the request echoed back.

**What changes.** Which kinds of game a group's Games deck deals this player in the sport —
*Competitive* the Competitive segment, *For fun* the For fun one, *No preference* both — and so
which proposed games and rescues the proposer puts them in: only a kind their intent wants. An
undeclared sport deals them nothing until it is answered; the deck asks the question in its
place.

### 3.4 Your week — the Availability grid

**What it is.** Seven days × three parts of the day, Monday-first. *A preference, not a promise*
— nobody ever sees it as a calendar; only the count of shared slots is ever rendered to anybody.

**What opens.** `AvailabilityGrid` exactly as `SocialAvailabilityStep` draws it (6.8): the card,
days **down** as rows (`MON` … `SUN`), *Morning · Afternoon · Evening* across as heads, 44 pt
cells in `paper2`, a ticked cell in `mint` with the white tick, and the step's footnote inside the
card under its hairline (*10 slots ticked. Overlap with another player is counted from these.* /
*Nothing ticked means we do not know when you play, never that you are unavailable.*). Under the
card, *Save your week* and *Clear all*. The commit's floor of one slot **does not bind here**: an
empty week is a legal value and the footnote says what it means.

**How the update happens.** Tap cells, press *Save*: one `PUT /players/me/availability` carrying
the whole week. Unkeyed, idempotent; the response carries the grid as stored and that is what the
screen draws. `useChangeAvailability` exists.

**What changes.** Which court hours this player is dealt: the proposer puts them only in a game
whose whole hour their week has free, and a booked game that lost somebody is offered to them as
a rescue only at such an hour — one rule, `free_for_the_hour`, asked by the proposer, posting and
the rescue board alike. And the **overlap grid** on every Games card they are on: how many of the
people on it are free together, never who, with its grade. A blank week deals nothing, because
being free is a claim a week has to make; a card with a blank week on it grades *Slim*, never
*High*.

### 3.5 How far to look — the Search radius

*Removed with Classic play on 2026-10-06 (#581, #582).*

### 3.6 Where you play — the Location area

**What it is.** A cell about a kilometre across, rounded to on the way in; the precise fix is
never stored. It moves silently on a cold start and after a day in the background.

**What opens.** No map, no name, no coordinates — nothing on this platform can turn the cell into
a neighbourhood and the screen does not pretend to. Two things:

- **the state**: *Your area is set* (mint) with the one sentence the tab already carries — *Your
  area updates each time you open Raketa; it is never finer than about a kilometre*. **It is the
  only state**: onboarding cannot finish without an area (*the one answer setting up cannot
  finish without*, the last step's own words), so every profile the tab can read holds one;
- **Read my area again** — the control from the location step, in its three permission states
  (*Raketa cannot see where you play · Location is turned off for Raketa → Open Settings*, and
  the plain control).

**How the update happens.** Pressing the control reads the phone once, coarsens on the client
exactly as the step does, and sends `PUT /players/me/location`. A fix that rounds to the cell
already held records nothing and answers `204`. The route exists, written for the cold start; a
screen calling it is the same request with a person behind it.

**What changes.** The distance to the club this player reads on a game's details, a booked game
and *Post a game*'s clubs, all measured from the cell; the nearest-first order of *New group*'s
home-club search and of the search for a group to join; and *In your area* on a record that
names them. Nothing else moves — no reset, no prompt.

**What it needs from the contract.** Nothing. The first draft asked the read for
`has_location`; it would always be true, and a flag that cannot be false is a branch nobody
tests. The screen branches on the permission state alone, which is the device's.

### 3.7 Who you play with — Gender and Gender preference

**What it is.** Two answers on one screen, because the second is unanswerable without the first:
`WOMAN · MAN · PREFER_NOT_TO_SAY`, self-declared and freely changed, and `ANY · WOMEN_ONLY ·
MEN_ONLY`, durable and **mutual** — it binds the other side's courts, not only this player's.

**What opens.** `SocialGenderStep`'s two radio groups under its two headings (*About you* / *Who
we should match you with*), each with its own *Save*, and the **reach sentence at the moment of
the press** — *You will not be matched with men — and men will not see you at all, even if they
are open to anyone* — which ADR-0096 owes the player on the surface that takes the value. The
step's scope sentences are not repeated here. The list row draws only the preference (*Matched
with anyone*); the gender is drawn on this screen and no other.

**How the update happens.** Each group saves on its own: `PUT /players/me/gender` and
`PUT /players/me/gender-preference`, both idempotent no-ops on an unchanged value. Neither route
exists; both aggregate methods do.

**What changes.** The pair rule on every court this player is dealt — mutual, never relaxed,
never scored, and read live on every proposal, fill and rescue (`PlayerFit`): no game is
proposed, filled or offered as a rescue with a pair on it that either preference excludes.
`PREFER_NOT_TO_SAY` fits only a preference of *anyone*. A narrowed preference keeps this player
off the excluded side's courts entirely, including those of people open to anyone; widening
restores them from the next proposal. In a four, every gate binds all six pairs.

**The decision this row needs** is in §5.2: the screen has to draw the current answers, and the
profile read promises never to serve them.

### 3.8 Game suggestions — the Proposals opt-in

*Removed with Classic play on 2026-10-06 (#581, #582).*

### 3.9 How others see you

**What it is.** The player record, opened about yourself: *"the same sheet everybody else is
shown about you, which is what makes it worth having: the numbers on it have been deciding who
you are offered to since you signed up."*

**What opens.** `PlayerRecordSheet` with `{ kind: 'me' }`, **section for section and nothing
else**, exactly as a court opens it today:

1. `RecordHeader` — the `PhotoPanel` at record size (the photograph or the generated poster,
   the flat scrim, the ON COURT mark where the photo passed, the resolved sport's Level over
   it), and beside it the name with *(you)*, the `@nickname`, the intro, and one sport pill per
   rated sport. No distance line and no fit pill, because `is_self` says so.
2. `SkillCard` — `PADEL · 2,71 · 61% sure` over the level bar with its band names.
3. `RecordBlocks` — *Player reliability · Last 5 · Counted*.
4. `RecordCard` — the metered strands, *Opponent variety*, *Sportsmanship, by players*.
5. `SocialTagRow` — every tag as the base tag with its emoji; no *you too* on your own sheet.

**How the update happens.** It does not, here. Every field on this sheet is edited by one of the
four rows beneath it on the tab, and the sheet is what they change. The header card at the top of
the tab is a compact form of this header and opens the same sheet.

**What it needs.** A door. The feature, the route and the sheet are built. The sportsmanship row
carries §5.3's decision like §3.2 does.

### 3.10 Photos

**What it is.** Up to three, in the player's order; the first is the profile photo; each carries
the on-court check's verdict — *passed*, *flagged*, or *nobody looked*, which is its own answer.
None is not an absence but a generated court poster.

**What opens.** `SocialPhotosStep` **as it is**, under its own title (*Your court photos*) and
eyebrow (*On-court only — up to three*): the rule note (*Rackets mandatory, faces optional*),
`PhotoRow` with its three 3:4 tiles — the profile tile bordered in ink with the night foot strip
reading *Profile*, the remove square top-right, an upload's progress bar in the strip, *Failed*
in red — `PhotoAddTile` with *Add a photo* and the slots left, the poster tile when there is
none, the two lines (*Tap a photo to make it the profile photo* · *Press and hold a photo to
replace, add or edit*), the `BottomSheet` on a hold with *Replace this photo · Add new photo ·
Edit* and their hints, and the flagged notice (*we could not see a court — nothing is blocked*).
The step's *Continue* is the one thing that is not here.

**How the update happens.** Each new picture is `POST /photos` as today; **every change to the
row — a promotion, a removal, an upload that landed — sends one `PUT /players/me/photos`** with
the ids in order, the aggregate's `change_photos`, idempotent on an unchanged list. There is no
*Save*, because the step has none: the row is the state. Removing the last one sends an empty
list and the poster returns.

**What changes.** The face on every card, seat and record that names this player, and the
ON COURT mark — **only a passed check earns the shield**, and a card marks only the pass; the
uploader is the one who sees a flag.

**What it needs from the contract.** The write route, and the read has to carry the photo ids
with their verdicts. The record serves the first photo only, which is right for a stranger and
short for the owner.

### 3.11 Tags

**What it is.** Two to six ids from the platform's closed vocabulary of nineteen, in three groups
— *After the match · On the court · Why you're here*. Never free text; a tag id is permanent.

**What opens.** `SocialTagsStep` **as it is**: the eyebrow with the served bounds (*Pick 2 to
6*), the step's question as the title (*What kind of player are you?*), the three groups under
their `flab` headings, the `Chip`s with their emoji labels — ink when picked — the ceiling note
pinned above the button (*6 tags is the most — Nothing changed. Remove one you have already
picked to make room for another.*), and the button shut under the floor with the step's own
words (*Pick 1 more tag to save*). The step's *Continue* is *Save*.

**How the update happens.** *Save* sends `PUT /players/me/social-tags` with the ids; the server
re-validates against the same vocabulary and bounds the picker read. No route yet.

**What changes.** The tags on this player's record, and nothing else: **a tag is shown, never
scored**, and no proposal reads one. **A tag is not an intent**: `HERE_TO_COMPETE` and a
`FOR_FUN` declaration coexist and nothing overrules either.

### 3.12 Intro

**What it is.** One line, at most 100 code points, no line breaks, any language, optional — a
player who wrote none has none. Fenced at the write: a phone number, an email, a URL or a handle
is refused.

**What opens.** The intro step's box with its label (*Your intro*), placeholder, counter
(`27 / 100`), hint (*One line, up to 100 characters. Optional.*) and rule (*Other players read
this on your card. Leave out phone numbers, emails, links and handles — people reach you in the
chat*), then *Save* and *Remove intro*. The two shape refusals (*too long*, *multiline*) shut
*Save* before anything is sent; `contains_contact` is the server's pattern and lands as the coral
note on the reply.

**How the update happens.** `PUT /players/me/intro` with the trimmed line, or a removal.
**Neither exists**, and ADR-0170 §5 says why: *"a single field editable while the two beside it
are frozen reads as a bug… it becomes editable the day a profile-edit surface arrives for all
three, as one piece of work."* This tab is that surface, so the intro's write ships with the tags'
and the photos' — an aggregate change (`IntroChanged`) plus its route.

**What changes.** The line under the name on this player's record, and on their own header card
on this tab, from the next read.

### 3.13 Name

**What it is.** The **Name** — free text, 2–64 characters, never unique, *what every sentence
says* — and the **Nickname** — a unique handle, `[A-Za-z0-9_.-]`, drawn as `@nickname` on the
record and on this tab and said nowhere.

**What opens.** `NamingScreen` (#451) pre-filled: the two fields under their labels (*Name* ·
*Nickname*) and *Save*. No sentence explains the two; the naming step's own question does not
need repeating on a screen that only edits the answer.

**How the update happens.** `PUT /users/me/name` carries both; the naming is *repeatable — a
later change is the same act*, keeping your own nickname is admitted, and **another player's is
refused by the server** with `409 nickname_already_taken`, drawn in the app's own words — *That
nickname is taken. Pick another.* — under the field. The check is the server's on *Save*, never a
client-side lookup while typing. The client re-reads `GET /users/me` before returning.

**What changes.** Every sentence, row, card, sheet, toast and seat label that names this player,
from the next read; the two initials over a generated poster; the handle on the record and here.

## 4. Considered and left out

| Candidate | Why it is not a row |
| --- | --- |
| **Blocked players** | Out of this build. Its read now exists (`GET /blocks`, the caller's own list with names and faces, #586) — but **no client surface makes a block today**; a screen that only lifts blocks nobody can place is a screen for a control that is not there. Comes back with the block control on the record sheet, as one ticket (#587). `DELETE /blocks/{player_id}` exists for it. |
| **Account** — email, password, deletion | Out of this build. None has a route; erasure is a domain concept (*erasure reaches both sides*) with no act behind it. *Sign out* is not affected: it stays at the foot of the tab as `AccountPanel` draws it today, the only way out of a session. |
| Alerts and notification preferences | No push channel exists in the app (no `expo-notifications`, no token route). A row of switches that switch nothing is a lie the design system already forbids (*no coming soon*). |
| A games history | *A history surface, on You* is on the loop's fog map; `GET /games` exists but what a finished game's tail should be is undecided. Not a preference. |
| Default sport, default mode, language, city | No such facts exist. Play remembers its segment and the sport last picked, per account on the phone (ADR-0188); language was struck as a nationality proxy; there is no city — only a cell (ADR-0174 §1). |
| Rankings | Nothing on this platform ranks players against each other; the prototype's ladder was cut with the reset. |
| Explanatory cards on the read-only screens | *Nobody types a level in*, *what it changes*, *what clears it* were on the first draft and are gone: the passport is the result card and the reliability screen is the record card, and each already says what it is. |
| Confirms results, Answers challenges, Settles up | Struck or standing down; a row drawn for one would be a nought under a name. |

## 5. What the contract needs

The reads and writes below are one backend ticket, or two if the decisions in §5.2 and §5.3 are
argued separately. `GET /players/me/profile`'s own description forbids a second read: *"this is
the route that grows them when the You screen is built — there will be no second endpoint for
them."*

### 5.1 The read grows

`PlayerProfileReadResponse` gains, beside `availability` and `play_intents`:

- `social_tags` — the ids, in the vocabulary's order (required at commit, so never absent);
- `photos` — the ids in order, each with its verdict as the uploader is owed it, or an empty list
  (**an empty list is a real answer** — a profile may hold none);
- `intro` — the line, or omitted where none was written.

### 5.2 Decided (ADR-0179 §4): the owner reads their own gender and preference

The read promises *"`gender` and `gender_preference` are withheld and always will be."* That
sentence was written to keep ADR-0096 §6 — *no response shape carries a gender value out, and no
card renders one* — and §6 is about **responses that describe one player to another**. A player
reading their own answer on a route scoped to `me` is not the thing §6 protects, and a screen
that asks the question with nothing pre-selected is a screen a player cannot trust: *did I set
women only, or not?* is exactly the fact the reach sentence exists to make legible.

**Decided:** ADR-0179 §4 amends ADR-0096 §6 — both values are served on `GET /players/me/profile`
only, and §21's test asserts they appear on that one shape and on no other.

### 5.3 Decided (ADR-0179 §5): the sportsmanship figure, shown to its subject

> Built on 2026-09-17 (#468): `GET /players/me/record` serves `sportsmanship` and
> `sportsmanship_band` is gone from the contract. The paragraph below describes the backend
> as it stood when the question was put.

The reliability screen and the record draw *Sportsmanship, by players* as **the figure and its
count** — `4,3 / 5 · 12 players` — the way the record prints it to a reader. **The backend does
not serve that to its subject and was decided not to**: `GET /players/me/record` carries
`sportsmanship_band` (*Good · Mixed · Poor*) and omits `sportsmanship`, because
[ADR-0158](../../adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md) argues that
an average beside a count in front of the person it is about is a subtraction — *moving from 4,80
over ten to 4,73 over eleven names the new rating as a 4, and they know who they played* — so
every answer would be identifiable by the one person who must never see it, and people stop
answering honestly once that is true. The client's `Opinion` type enforces it: the subject's arm
carries a band and no figure, and the port's self-facing method *cannot* return one.

**Two ways to build the screen as drawn, and one to keep the rule:**

1. Overturn ADR-0158's subject rule — serve `sportsmanship` on `/players/me/record` — and accept
   that a rater becomes nameable by their subject. That is the prototype as it stands.
2. Serve the figure but not the count (*4,3 / 5*) — weaker than it looks, since the count is how
   a player tells one opinion from twelve, and a figure alone still moves visibly on each new
   rating.
3. Keep the rule and draw the band word on both screens, as the sheet does today.

**Decided: (1).** ADR-0179 §5 amends ADR-0158 §6 — `sportsmanship` is served on
`/players/me/record` as to any reader, `sportsmanship_band` retires, and the cost is written
beside the reversal. The client's two-armed `Opinion` collapses to one.

### 5.4 The writes

| Route | Aggregate | Note |
| --- | --- | --- |
| `PUT /players/me/social-tags` | `change_social_tags` | re-validates against the served options |
| `PUT /players/me/photos` | `change_photos` | ids in order, each owned by the caller; empty clears |
| `PUT /players/me/intro` (+ removal) | **new** `IntroChanged` | ADR-0170 §5 — ships with the two above |
| `PUT /players/me/gender` | `change_gender` | no-op on unchanged |
| `PUT /players/me/gender-preference` | `change_gender_preference` | no-op on unchanged |

Regenerate `openapi.player.json` and `make gen-api`; the drift check will hold the client to it.

## 6. Build order, briefly

The tickets are #465's children; the order below is theirs.

1. **The composition** — the tab as three groups, drawing what exists: the passport from
   `GET /ratings` and the record's per-sport panel, reliability and *How others see you* from
   `GET /players/me/record`, intents as built, the week from the surface with its existing
   write, the area's control over the existing route, the naming screen behind a door,
   *Sign out* as it is. Every row from `PlayIntentsSection` down is a `player_profile` component
   composing the step it came from; `shell` composes and owns the group titles. No contract change.
2. **Add a sport** — the second door into the onboarding pass (§3.1). Client only; the
   questionnaire and its routes are untouched.
3. **The read grows and the five writes land** (§5.1, §5.4), one backend ticket, blocking:
4. **The three social edits as one piece of work** — photos, tags, intro — which is the shape
   ADR-0170 §5 asked for; then gender and preference behind §5.2's decision.
5. **The sportsmanship figure**, behind §5.3's decision, whichever way it goes.

## 7. What this document does not decide

- The words. The sentences on these screens are the steps' and the sheet's own, reused; the few
  new ones (*This changes how people find you*, the group titles, the live lines) are proposals
  for `the-words.md`'s next section.
- Whether the header card's ring is the Player Score or nothing — a player with no reliability
  record has no score, and the card draws the pills alone.
- Design-system amendments. Every screen composes objects the system already draws (5.5 row, 6.8
  grid, 6.9 tiles, 6.10 slider, 7.5 level bar, 7.8 ring, 7.13 record block, 7.16 photo panel);
  the status chip on the passport's card and a section title over a card of rows are the two
  things without a numbered home, and both are existing roles (`Tag`, `flab`).
- The prototype's own visual choices. It follows `theme.ts` so the rows read as the app's, and
  it is throwaway: nothing in it is a component.
