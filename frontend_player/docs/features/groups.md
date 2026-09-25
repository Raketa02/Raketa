# groups — Play › Groups, New group, Join a group, and a group's page

> The design record for `src/features/groups/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. **Append here** when a ticket changes what this
> feature does. Index: [`README.md`](README.md).

**Play opens on Groups, and the feature is four screens over six routes**
([#512](https://github.com/Raketa02/Raketa/issues/512), PRD
[#500](https://github.com/Raketa02/Raketa/issues/500), ADR-0182, ADR-0183). With `find_a_game`
off — the code default since #512 — the Play tab draws the shell's _Groups | Explore_ segment
([`shell.md`](shell.md)), and _Groups_ is `GroupsSection`: the groups the player belongs to,
newest joined first, with **+ New** (outlined, `secondary`) and **Join** (coral, `primary`)
above them in every state. **New group**, **Join a group** and **a group's page** are pushed
under `/play/…` — `play/new-group`, `play/join`, `play/group/[groupId]` — so the Play column
stays lit and _back_ is the list. Creating a group **replaces** New group with the group's page,
so _back_ from a new group is the list too, never the form. The words are the mocks' (play 1,
3–13, 23–40), with _Rakieta_ read as Raketa, in `components/groupsPresentation.ts`; the mocks
live in [`docs/specs/play-groups/`](../../../docs/specs/play-groups/README.md).

**Nothing about a group is computed on the phone.** The monogram's two letters and its colour
key are cut by the backend (ADR-0183 §5) — drawn as they come, never re-cased — and the sport
dots, the member count, the distance and every search's order are the server's. The one mapping
on this side is the colour **key** (0–7) to a hue: `MONOGRAM_HUES`, beside `POSTER_HUES` in
`theme.ts` and for the poster's reason outside `theme.color` — a hash-picked hue means nothing,
and a palette that picks by meaning must not carry one. Four of the eight are measured off the
mocks and four chosen between them; white letters clear 4.5:1 on every one
(`monogramHues.test.ts`, design-system 7.20). The tile's letters are set at a share of its side,
as the yes tile's initials are, and shrink to fit at large OS text sizes rather than turning font
scaling off, which Part 13 keeps for the level bar.

**Two rules, pure, in `domain/groupRules.ts`, and the form's one schema.** The New group form
is checked by `schemas/newGroupForm.ts` (_the form + one Zod schema_): `newGroupFrom` answers the
group to create — the name **trimmed**, at most 40 characters, and a home club, which PRD #500
makes required over play 4 — or nothing, and _Create the group_ is pressable exactly when it
answers. `groupAction` — what a row offers: _Join_ on an Anyone group, _Ask to join_ on a People I approve
one, _requested · waiting_ once asked, _you're in_ for a member; a declined request reads `NONE`
on the wire and so quietly comes back as _Ask to join_ (story 43). `searchOutcome` — clubs when a
search found any, otherwise _nothing at that link_ for a `LINK` read and _no match_ for text,
**quoting the text the answer was for** rather than what has been typed since: the search's text
travels on its answer (`ClubSearch.text`) for exactly this.

**Join and Ask to join are one tap on the wire, and the answer decides what the row becomes.**
Both are `POST /groups/{id}/membership`; the answer is the row itself with the reader's new
relation, and `useJoinGroup` writes it into **every cached search that holds that group** — a
club can be in the home-club answer and the join answer at once — so the button turns into its
word without a second read. A join that made the reader a member invalidates the Groups list.
**Neither is optimistic**: whether a tap admits or asks is the group's policy on the server, and
a client that guessed would draw _you're in_ over a group that has just switched to _People I
approve_. A failed join is a `bad` toast, because the row has no line to say it on, and the row
keeps its button; joining twice changes nothing server-side, but the second tap is the player's,
never a retry.

**The two searches are one hook over two routes, asking on every keystroke.** The text, trimmed,
is the query key, so each letter is a new question and the one before it is abandoned through its
`signal`; the answer on screen stays until the next lands (`keepPreviousData`), so the list
narrows under the finger instead of blanking — **except across a blank text**: ✕ cleared the
answer, and Query would otherwise offer the last answer that had data under the next letter, so
the hook remembers the clear and draws no placeholder until a real answer lands. **No debounce** — the ticket asks for every
keystroke, and a cancelled `GET` records nothing. A blank text asks nothing. **Twenty clubs a
page, more on scroll**: an infinite query over `next_page`, and each screen's scroller asks for
the next page within half a screen of its end. The results sit **inside the page's own scroller**
on New group rather than in a list of their own, because a list inside a form is two scrollers
under one thumb.

**New group is the screen's own state and dies with it** (stories 11–27). Every open is empty and
the back arrow discards it. The name field stops at 40 characters (`GROUP_NAME_MAX`); the server
trims and counts again. The home club card (`HomeClubCard`) holds no state and draws five:
**empty** (the hint, and what a home club is for), **searching** (rows of name · district · sports
and _Set as home ›_, the whole row the tap, **no distance** — #512 overrides play 7), **no match**
(_No club called "…"_ and that only clubs in Raketa can be one), **a club with groups** (tinted
`amberSoft` to the card's edges, tagged _group already here_, a white strip per group with its
action — the player can join from inside the form, and can still choose the club, because a second
group at one club is allowed), and **chosen** (the field replaced by the club on `mintSoft` with
its distance and **Change**, and the line under it now saying what the choice means). _Who can
join_ is two chips, _Anyone_ first and chosen, with the note that there is no sport to pick.
**Create the group** is disabled until the schema answers a group, busy while the create is in flight — two
creates are two groups, and the create is never retried — and on success it seeds the page's read
with the answer, replaces the form with the page and raises _Group created_ in `ok`. A refusal the
form can name (`group_name_invalid`, `home_club_unknown`) is said under the button in the form's
words.

**Join a group is one field and nothing else** (stories 29–44). The field takes the focus as the
screen opens; **Paste** — a chip inside the field, through the new clipboard port — drops a link
from WhatsApp into it, and becomes **✕** while there is text, which clears the text and the
answer. A club's card header is **context, not a choice**: one spoken element with no button role,
name over _district · distance · sports_. Each group row draws its dots, count and approver on one
truncated line with the action beside it; the approver is the Owner's **whole Name** (ADR-0171 §4,
#505 — the row truncates it, nobody cuts a first name from it), _anyone can join_ for an Anyone
group, and _the owner approves joins_ for an Owner who can no longer be named. The three ways of
there being nothing are three sentences: _No groups here yet_ on a club's card, _Nothing at that
link_, _No match for "…"_.

**Every failed read is one block** — `ReadFailure`: why, in the caller's words where it can name
the failure (`codeMessage`) and the recovery's otherwise, and _Try again_ **only where the
failure's recovery says trying again can help** — never for `group_not_found`, which answers the
same however often it is asked.

**A group's page is its header, for now** (play 40). `ScreenHeader`'s new `compact` form — the
title at `h2` beside the tile in the lead slot, the title and _N members · Home club_ each on one
line and ending in an ellipsis (story 50), spoken whole. The sport pill and the four tabs are
[#513](https://github.com/Raketa02/Raketa/issues/513)'s. An id that is not a UUID redirects to
Play; `group_not_found` — one code for _no such group_ and _not one of yours_ — is one sentence.

**Two things the mocks draw that this record departs from, and why.** The mocks draw the sport
dots on a card with **no sport name beside them**, which design-system 2.3's premise says a dot
always has: they are drawn as the mocks draw them, and **every element they sit in speaks the
sports by name** (_…, plays Padel, Tennis_), so a listener gets the words — a reader who cannot
tell the four hues apart still gets them only from the group's page. And the home-club field's
focus ring is **coral**, as the ticket asks (_live, coral focus ring_), which is a seventh coral
beside 1.2's closed list; both are recorded in design-system Part 16 for the product owner to rule
on. **Nothing here has been seen on a device.**
