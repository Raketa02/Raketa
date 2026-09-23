# ADR-0167 — A yes lands on its own screen, and the room is opened by a tap

- **Status:** Accepted — **§2's *the next dark screen argues for its own record, here* answered
  2026-09-14 by [ADR-0169](0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)** §7: the deck card is the second dark surface, a surface and not a
  screen, fenced as this one is.
- **Date:** 2026-09-14
- **Supersedes, by named sentence,**
  [`the-loop-screens.md`](../specs/the-loop/the-loop-screens.md) §2.1's *"`I'm in` goes to the
  room … The reply is still the redraw (§2.4), and then the screen pushes the room"* — the reply
  is still the redraw, and the screen pushes **the yes screen**; the room is opened by a tap (§1).
  Everything else in that paragraph stands and moves behind the button: the teller writing the
  room off the outbox after the accept has answered, the door waited for on a short bounded
  cadence, and a yes that completed the court waiting for the room to carry its game.
- **Amends** [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md) §4 — *the client
  may never derive a familiar form from [a handle]* — by **one drawing, named in full** (§3), and
  leaves the rule standing for every sentence, every spoken name, every toast and every other
  drawing, the Chats rows included: [#338](https://github.com/Raketa02/Raketa/issues/338) §5's
  refusal of a monogram there is untouched.
- **Leaves standing** [ADR-0012](0012-player-app-design-system.md) and the design system's 15.4 —
  *there is no dark mode* — which is exactly why §2 is a record and not a Part 16 row: the yes
  screen is one ground and not a theme, and Part 16 is where the app ticket writes its values as
  *for this screen only*. Leaves standing
  [ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) §7 — membership is
  derived, and the picture the screen draws is that rule;
  [ADR-0149](0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md) §3 — the chat
  door is a join over the reader's rooms, and the button is that join;
  [ADR-0154](0154-a-mutual-names-the-game-it-has-and-names-nothing-when-it-has-none.md) — a mutual
  naming no chat says nothing more, and gets no screen;
  [ADR-0134](0134-the-poster-draws-a-player-and-no-value-is-invented.md) — the poster is a fact
  about an id, and the initials ride on it; and
  [ADR-0157](0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)
  — the header's stems are a different case with a different argument, and neither moves.
- **Does not decide** the other side seeing the moment (§5).
- Settles [#432](https://github.com/Raketa02/Raketa/issues/432), the first child of
  [#431](https://github.com/Raketa02/Raketa/issues/431), which is its spec; built by
  [#433](https://github.com/Raketa02/Raketa/issues/433) and
  [#434](https://github.com/Raketa02/Raketa/issues/434). **No backend change and no contract
  change**: every fact the screen draws is already on the wire. Grilled 2026-09-14.

## Context

**Two taps change something between two people, and neither is shown.**

- **`I'm in` teleports.** The accept reply redraws the challenge screen in the first person, and
  then the screen polls the rooms list — 750 ms apart, bounded at 6 s
  (`conversations/domain/roomOpening.ts`) — until the row for that challenge is there, carrying
  its game when the yes completed the court, and **pushes the room**. Past the bound the screen
  stays and draws *Open the chat*. Tomek taps *I'm in* on Ewa's tennis challenge; the screen
  redraws under his thumb, and a second later — sometimes three — he is inside a chat room he did
  not ask to open, with the challenge screen still behind it on the back stack.
- **A mutual is a grey line.** On Match me the yes is optimistic — the card flies on the press —
  and when the reply says `mutual` the deck picks one of three sentences for a toast: a one-sided
  yes (*Noted — …*), a mutual naming no chat (*You both said yes — … sees it the next time they
  open Raketa*), a mutual naming one (*You both said yes — … is in your Chats now*). Nothing
  navigates; the row in Chats is the door. Tomek taps *Let's play* on Marek, Marek had already
  said yes, and what he gets is gone in under three seconds. If he blinks, the next card is up.

The one moment the product has to say *something just happened between two people* is spent on a
loading pause and a teleport, or on a toast.

### The design, and the rule for reading it

A design arrived for that moment — three mocks, held by the author outside the repo — and it is
the priority: **where it disagrees with the locked design system or an accepted record, the
design wins and the record is amended.** The mocks show one dark immersive screen: the faces of
the people on the court, one lime word — *Challenge!* or *Matched!* — and two pills, *Open the
chat* and *Later*. Nothing else — no names, no sport, no day, no place, no tab bar, no header —
because after accepting, a player already knows who they will play with.

It disagrees with four things this repository already holds, and #431 named each so that no
build ticket discovers one mid-way:

1. **The client walks into the room** — above.
2. **The design system is paper-only.** The one dark thing is a card on a page (5.2). The mock's
   two background colours are, to the byte, the prototype's *stage* colours the system dropped by
   name in Part 0 — *"they exist only to frame a picture of a phone"*. Every button is a 10 pt
   rounded rectangle and the pill is the chip's alone (4.2). The app has one lime, `volt`, a hair
   yellower than the mock's. The largest sans word is 19 pt: a 26 pt `display` role was added on
   2026-09-08 for a figure and retired on 2026-09-12 with it, and its own note says *"the record
   below stands as the reasoning that would apply again the day a sans word above 19 is genuinely
   needed"*.
3. **There is no monogram.** A face is a photograph or a generated poster — a silhouette on a
   two-stop gradient whose hue is hashed from the player id (ADR-0134) — and the poster is what
   every court draws for the reader's **own** seat, because nothing carries a player's own photo
   onto a court. Initials were proposed for the Chats rows by both chat designs and **refused**
   (#338 §5) on ADR-0107 §4: the client never derives a familiar form of a handle. `handleStem`
   and the seat's three-character caption were admitted *inside* that rule — a prefix cut at a
   character the owner typed invents nothing (ADR-0157,
   [`the-words.md`](../specs/matchmaking/the-words.md) §15). Two initials are not a prefix.
4. **The app avoided the word *match* for a game.** An earlier design used it as a noun that
   promised results and history; the glossary has no entry for it, the thing two people arrange
   is a **Challenge** and then a **Game**, and
   [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md) rejected `matches` as the
   context's name because *"the wire, the card and the newcomer path all say game"*. The word
   survives as the engine's — *Match Fit*, *matchmaking*, the *Match score* on a challenge screen
   — and as the Play segment's *Match me*; none of those is a noun for a game, and the glossary's
   own prose says *matches* in passing where it means games (*no counted matches*, *a two-player
   padel match*) without ever defining one.

## Decision

### 1. The client no longer walks into the room

**A yes lands on the yes screen, and the room is opened only by a tap on *Open the chat*.** A yes
is `I'm in` answered, or `Let's play` come back `mutual` **and naming a challenge** — the two acts
the app already calls a yes, ending on one screen because both end in a challenge: the accept
reply *is* the challenge's standing, and the mutual reply names the challenge it opened
(ADR-0154). The screen lives in the challenges feature, keyed by that challenge, with one
validated parameter saying which yes it is; a route parameter is not app state, so the screen
reads everything it draws from the challenge the query cache holds, and a bad or foreign
parameter draws nothing and leaves.

- **The reply is still the redraw.** The challenge screen underneath keeps its standing in the
  first person exactly as §2.4 says; what changes is where the screen goes next, and that it does
  not go there by itself.
- **The awaited door survives unchanged, behind the button.** The bounded rooms-list poll — 750 ms
  apart, up to 6 s — and the rule that a yes which completed the court waits for the row to carry
  its game move into the yes screen and run from the moment it opens, so by the time most players
  tap, the room is already known. *Open the chat* shows *busy* until it is, and is never
  disabled: past the bound the tap lands on the **Chats list**, where the row will appear. *No
  door rather than a dead one* still holds — here the door is the list.
- **Where it lands is the same from both entries:** the stack becomes [Chats list, the room], the
  challenge screen — where there was one — gone with the yes screen, so back from the room is the
  Chats list and never the celebration. From the deck this switches the tab; Play keeps its held
  deck.
- ***Later* goes back.** After a challenge's yes, to the Chats list, popping the challenge screen
  with it; after a mutual's, a plain pop — the deck's next card, or wherever the player was when
  the reply landed. Android back is *Later*. The iOS swipe-back is off on this route, because a
  swipe that popped to the challenge screen underneath would land somewhere *Later* never does.
- **Two sentences keep their toasts.** A mutual naming no chat — the pair already have a game
  being arranged, or a gate refused; one answer, two causes, deliberately not distinguished
  (ADR-0154) — and a one-sided yes say what they say today, verbatim. A full-screen celebration
  must never overstate what happened. The third sentence, the mutual-with-chat toast, retires into
  the screen. *Not this time* goes nowhere, as today.
- **The screen is one-shot, and it is the reader's alone.** Leaving it by any exit removes it and
  nothing re-shows it; a reply that lands after the player moved on — to the next card, or to
  another tab — still opens it, wherever they are. The other side is §5.
- **The challenge screen's own *Open the chat* arm** — drawn on later visits, on every arm whose
  reader the room would hold — is untouched, and so are *Leave the game*, the fill route and the
  builder.

### 2. The yes screen is the app's one dark ground

**The design system stays paper-only, and this screen is the single exception.** Not a dark mode
— 15.4's *there is no dark mode* stands, and adding one is still its own ADR — but one ground,
on the mock's two colours, drawn as a radial glow with the SVG the poster already uses. They are,
knowingly, the prototype's dropped stage colours; the design wins and the record says so, rather
than the two values being nudged to look like something the system already had.

Four things arrive with it, each **for this screen only**:

| Value | What it is | Why it is not a copy of something |
| --- | --- | --- |
| two ground colours | the glow's centre and its edge — *the yes screen's ground* | no other surface may use them; the next dark screen argues for its own record, here |
| the pill | a radius option on the existing `Button`, not a second primitive | 4.2's *the chip — the only true pill* gains one exception, on this screen; a button is 10 pt everywhere else |
| one ~30 pt sans role | the word, at the heaviest weight, with one use | recorded as a decision made for this word, not a role to reach for — and not the retired `display` back under a new name, though 3.3's reasoning is the reasoning |
| the lime | **`volt`**, exactly as it is | its recorded meaning — *they want you to play*, *the plan is settled* — is what this screen says; no second lime, and the mock's slightly greener one is not matched |

Each is written into `theme.ts` and the design system's Part 16 **in the same commit**, by the app
ticket, as 15.3 demands: this record is where the exception is decided, and Part 16 is where its
values are recorded. Every measurement — tile size and corners, the gap at `vs`, the word's size,
the pills' height and padding, the glow's radius — is taken from the mock rather than from this
text.

The status bar stays, with light content. The tab bar **stands down** for this route by the
mechanism the room already uses (`barStandsDown` — not rendered, not hidden, nothing animates it
away), which makes the yes screen the second route named there. The stack is still a stack: no
modal presentation, no second navigator.

**It moves once.** About 600 ms — the two sides slide in from the edges and meet, the word rises,
the buttons fade in last — and one soft success haptic as the word lands, which adds
`expo-haptics`, the first haptic in the app. Under *reduce motion* everything is simply there and
nothing buzzes. Nothing loops.

### 3. The initials tile is the one drawing exempt from the whole-handle rule

**The yes screen draws two initials over a poster, never over a photograph.** A tile is the face
the app already draws — `PlayerPhoto`, photograph or poster — with two additions for this screen:
initials over a poster, and an outlined empty state. The cut is a formatting rule beside
`handleStem`: the first letter of each word, split at the handle's word breaks — a dot or a
space, the same two the stem cuts at, so the two rules stay one, though a `Nickname` cannot hold
a space; `_` and `-` stay inside a word — at most two, and fewer where the handle has fewer to
give (a handle opening with a break keeps what follows it); a one-word handle yields its first
two characters; upper-cased for drawing only. `Tomek.K` → `TK`, `dorota_w` → `DO`, `Ola.N` →
`ON`. Over a photograph nothing is drawn: the face names the person. An empty seat is the same
tile, outlined, with nothing in it.

**This is an exception to ADR-0107 §4, argued as one rather than smuggled under the rule.**
`handleStem` and the seat caption were admitted *within* §4 — a prefix of the handle, cut at a
character its owner typed, is not a derived form. Two initials are a derived form; #338 §5 said so
and refused them on the Chats rows. What is argued here is what the rule protects:

- **§4's harm is a sentence.** *"Inventing a first name is the product addressing a person by a
  name they never gave it."* Addressing is a sentence's act. The tile is a **drawing**: no
  accessible name, no toast and no copy ever carries the initials; the tile's spoken name is the
  whole handle, and the screen's announcement — *Challenge! You and Ola.N against Kuba.W and
  Zofia.B*, with *an empty seat* where one is, and *Matched! You and Marek.P* — is built from
  whole handles. Nobody is ever addressed as `TK`. The-words §15 drew this line for truncation —
  *"the accessible name carries the whole handle, which is where the rule actually bites"* — and
  it is the same line.
- **The poster is a fact about an id** (ADR-0134), not a face. Initials on it give the poster an
  identity the gradient alone cannot at tile size — as the mock draws it. Initials on a photograph
  would cover the one thing that already names the person, which is why they are refused there.
- **The fence has four sides:** never spoken, never in copy, never over a photograph, never on any
  other surface. The Chats rows stay as #338 left them — photograph, poster and the handle beside
  it — and the header keeps its stems.

Anything that wants initials elsewhere starts from this record, and has to show a surface with no
room for the handle and no sentence to leak into.

**The reader's own face costs one read.** The other players' photos come off the seat cards the
challenge already carries; the reader's own comes off their own record — one read, fired when the
screen opens, cached for the session, the poster if it does not answer — through `player_record`'s
public surface, a new feature edge for the boundary script to hold open. The entrance waits for
its faces, so no tile swaps mid-animation.

### 4. *Matched!* is the one place the word appears

**Said once, on this screen, in every sport, as the past tense of *Match me*.** The glossary kept
*match* out because an earlier design used it as a noun that promised results and history; the
Play segment is nevertheless *Match me*, and a player who tapped *Let's play* under that word and
was answered is, in that word's own tense, matched. The screen draws the two of them side by side
with no `vs` and no empty seats, in every sport: in tennis the two are opponents, in padel
partners with a side to fill, and both are true statements about two people — so the word never
claims a court, and the court's shape is the chat's business one tap later.

*Challenge!* is the other face — after `I'm in`, singles or doubles, whatever standing the reply
came back with, even when this yes completed the court: you, then your partner or an empty seat,
the small grey `vs`, then the other side, reader first regardless of who sent the challenge or
who said yes first. *Game on!* for the completing yes was refused: one word for one act.

**The noun stays out.** No sentence in the client calls a game a match — the row, the card, the
room and the game screen say *game* — `matches` is still not a context, and *Matched!* adds no
glossary term: it is copy, in the screen's presentation module. The client glossary's new entry
is **the yes screen** — the screen a yes lands on, *yes* being what the app already calls both
acts (*You both said yes*, the client glossary's *outstanding yeses*, ADR-0165's *a yes can be
taken back*) — and *moment* is not a term.

### 5. What it does not decide — the other side seeing the moment

The organiser when somebody says `I'm in`; the first of two to say `Let's play`. Both learn from
their Chats list on their next look, as today. Showing them the moment needs the backend to
remember *not yet seen*, or a live channel outside a room — neither exists, and neither is a
client decision. It is a follow-up spec, and the asymmetry §1 admits (*the reader's alone*) is
the cost this record leaves on the table rather than papers over.

### 6. Records and copies

ADR-0107 §4 carries the amendment in place, under its heading. `the-loop-screens.md` §2.1's
*`I'm in` goes to the room* paragraph is rewritten in place, pointing here, as ADR-0165 rewrote
that spec's §2.5 and §2.6 — a spec states what is decided, and only a record is immutable. The
design system's Part 16 rows, the theme, the challenges, play, shell and shared feature records,
and the client glossary's *the yes screen* travel with #433 and #434, because a record of what is
built moves with the build. The root `CONTEXT.md` gains nothing: every fact the screen draws is a
domain fact it already defines, and *the yes screen* is client vocabulary.

## Consequences

- **The one moment is a screen, and it draws only what the app already holds.** No backend
  change, no contract change, one new feature edge — challenges → player_record, for the reader's
  own photo.
- **The wait did not go away; it moved behind a button.** A player who taps *Open the chat*
  inside the first second sees *busy* where before they saw a redraw and then a room, and a
  delivery worker that is behind still lands them on the Chats list at 6 s rather than in the
  room. The screen makes the wait invisible for most players and honest for the rest; it does not
  shorten it.
- **The challenge screen is one tap further away after a yes.** Back from the room is the Chats
  list, not the standing in the first person; the room's own *Details* door is where that
  standing lives now. On a later visit the challenge screen is unchanged.
- **The design system has an exception, and exceptions are how rules die.** Two ground colours
  whose only guard against a second surface is their name and a Part 16 row; a pill on a
  primitive that had one radius; a 30 pt role two days after the 26 pt one was retired for having
  no use. Each is fenced as *for this screen only*, and the next request to reuse any of them is a
  request to reopen this record, not a styling change.
- **ADR-0107 §4 now has an exception, drawn on a sentence/drawing line.** The line is real — the
  accessible name is where the rule bites, and the-words §15 already drew it for truncation — but
  #338's refusal was simpler when it was absolute. §3's four-sided fence is what has to hold: the
  day initials are spoken, or drawn over a photograph, or appear on a row, the exception has become
  the rule and this record was wrong.
- **One player celebrates and the other gets a row.** §5 leaves the moment one-sided; until the
  follow-up, a doubles organiser learns that Ola said yes from a line in a list while Ola saw a
  full screen. Deliberate, and visible.
- **A mutual is not always a screen.** The mutual naming no chat, and the one-sided yes, keep
  their toasts, so a player can get *Matched!* for one *Let's play* and a grey line for the next.
  That is the point — a screen must never overstate — and it will be asked about.
- ***Matched!* re-admits a word on a fence of one tense and one screen.** The next proposal to say
  *match* for a game starts here, with the noun still refused.
- **The mocks were drawn with posters throughout.** The photo-when-there-is-one rule is the
  author's, on top of them, so the screen as built differs from the mocks for anybody with a
  photo, and the build is checked against the mocks *and* against that rule — by the author, since
  a session cannot see the screen.
- **`expo-haptics` is a new dependency**, the first haptic; not a styling dependency, and reduced
  motion switches it off with the entrance.
- **The tests that pinned *accept pushes the room* move**, named rather than discovered —
  `challengeScreen.test.tsx`'s *the room an acceptance opens* block — and the deck's
  mutual-with-chat toast test retires with its sentence; the other two sentences keep theirs.
