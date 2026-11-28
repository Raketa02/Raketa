# ADR-0199 — A player is known by their nickname

- **Status:** Accepted — **its *Context*'s *"there is no friendship in Rakieta"* superseded
  2026-11-06 by [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)**: players have
  friends, held across their groups. The alternative that line argued against, *keep the name, show
  it to friends only*, stays rejected: the Name is retired, and a friend reads the nickname everybody
  reads.
- **Date:** 2026-11-03
- **Supersedes [ADR-0171](0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
  in full.** The **Name** is retired. The **Nickname** is what every sentence, row, card, sheet,
  notice, seat label and email says about a player, and it is never written with an @ (§1).
- **Amends [ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
  §4.** An account an Invitation opens holds **no player name**. The name the club typed stays on
  the **Administrator** (§4). The naming asks for a nickname, which is all it ever asks now, and
  the gate's first player destination reads *no nickname* (§3).
- **Restores [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md) §4's sentence**
  as it stood before ADR-0171: *every sentence naming somebody uses the whole handle or names
  nobody*, read on the nickname. §4's argument never moved. §2's closed list carries the nickname
  where ADR-0171 had it carry the name.
- **Amends [ADR-0167](0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md) §3's
  cut.** The two initials over a poster are cut from the nickname, and `_` and `-` now break a
  word as a dot does (§2). The four-sided fence stands.
- **Leaves standing**
  [ADR-0157](0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)
  (the stem is cut at the nickname's first dot, as it was before ADR-0171);
  [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §7
  (the You tab edits with the same act, from the row now called *Nickname*);
  [ADR-0002](0002-event-sourced-user-aggregate.md) (the `User` stays one aggregate); and
  [ADR-0170](0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md) (the intro is
  where a person speaks, and the nickname is where they are named).
- **Does not decide** a limit on how often a nickname changes, a search by nickname, reserved or
  offensive nicknames, or how club staff are named on the club surface and in their own emails,
  which stays as it is.
- Settles the nickname half of PRD [#722](https://github.com/Rakieta02/Rakieta/issues/722), decided
  in the onboarding grilling on 2026-11-03 (Q13, Q23, Q24) and written by
  [#723](https://github.com/Rakieta02/Rakieta/issues/723). Built by
  [#724](https://github.com/Rakieta02/Rakieta/issues/724) (the player API),
  [#725](https://github.com/Rakieta02/Rakieta/issues/725) (the club API),
  [#728](https://github.com/Rakieta02/Rakieta/issues/728) (the phone) and
  [#734](https://github.com/Rakieta02/Rakieta/issues/734) (the club website).

## Context

**Ania's name is on every screen, and her handle is on two.** ADR-0171 gave a player two terms. The
**Name** (*Ania Kowalska*) was free text, never unique, and what every screen said. The
**Nickname** (`ania.k`) was a unique handle, drawn as `@ania.k` under the name on her own You tab
and on her record, and said nowhere else. So when she joins Kuba's *Wednesday padel*, these all
say *Ania Kowalska*: Kuba's deck, the chat, *It's a game!*, his notifications, Members, the club's
Bookings page and join requests, and the payment emails.

**Players don't expect that.** The name feels private and isn't. What players expect is what
Instagram does: one handle is who you are, and it is what everybody sees. A real name Rakieta shows
to strangers is a real name Rakieta holds, and Rakieta has no privacy policy yet
([#735](https://github.com/Rakieta02/Rakieta/issues/735)).

**The naming is also one more field between sign-up and Home.** *How should people see you?* asks
for a Name and a Nickname, with *"Use letters, numbers, and . _ - only — no spaces."* under the
second. PRD #722 cuts onboarding to eight screens, and this is one of them.

**What ADR-0171 argued, and why it no longer holds:**

- **Its case for a name was the seed.** *Diego.Fabregat left* read badly because the seed spelled
  every account `First.Last`, to look like a name. That was a handle pretending to be a name. A
  handle the player chose (*ania.k*, *kuba*, *dorota_w*) reads as a handle, the way it does on
  Instagram, and the seed can spell handles as handles.
- **Its case against *a nickname only* was two people with one name.** Two *Ania Kowalska*s could
  not be told apart on a row. With no name, that cannot happen: a nickname is unique.
- **Its case against a unique name** (*the second Diego Fabregat is told his name is taken*) is a
  case about names. A handle being taken is ordinary.

**The alternatives:**

- **Keep the name, say the nickname.** The name would then be held and shown nowhere: data kept
  for nothing, about a real person, which is the opposite of what a newcomer expects.
- **Keep the name, show it to friends only.** There is no friendship in Rakieta (the Friends tab is
  out of scope), so this is a privacy setting to build and explain before anybody needs it.
  *(Superseded 2026-11-06 by [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md): there is now friendship. The alternative stays
  rejected, since the Name is retired.)*
- **Write the nickname with an @** (*@ania.k put a score up*). The @ is a chat app's mention mark.
  Rakieta has no mentions, and inside a sentence it reads as markup (Q23).

## Decision

### 1. The nickname is what is said, without an @

**The Name is retired** as a domain term. Nothing holds it, nothing asks for it, nothing shows it.

**The Nickname keeps its rule**: trimmed, 2–64 characters, `[A-Za-z0-9_.-]`, unique across the
platform. **It is what every sentence, row, card, sheet, toast, notice, seat label, spoken name
and email says about a player**, and it is **never written with an @**:

- Kuba reads *ania.k put a score up*.
- Her card and her You header draw **ania.k** large, with nothing under it.
- The club's Bookings page and join requests say *ania.k*.
- The payment emails open *Hi ania.k*.

ADR-0107 §4's sentence reads on it again: **the whole nickname, or nobody**. Nothing invents a
familiar form of it. A seat label may still truncate visually and a sentence may not
([`the-words.md`](../specs/matchmaking/the-words.md) §15), and the stem (ADR-0157) cuts at the
first dot.

### 2. The initials over a poster are cut from the nickname

The yes screen's tile (ADR-0167 §3) draws two letters over a generated poster: **the nickname's
first character, then the first character after its first `.`, `_` or `-`, else its second
character**, upper-cased for drawing only. *ania.k* → `AK`, *kuba* → `KU`, *dorota_w* → `DW`.

ADR-0167 kept `_` and `-` inside a word, because a name's space was the other break. With no name,
the handle's three separators are the only breaks a player types, and `dorota_w` → `DO` would draw
half of what she chose. The fence stands on all four sides: never spoken, never in copy, never over
a photograph, never on another surface. *(A call made in the spec, not grilled.)*

### 3. The naming asks for a nickname, and the nickname can change at any time

- **The step** keeps its title, *How should people see you?*, and has one field: **Nickname**. The
  rule sentence is drawn only as the field's error, when the player breaks it. A taken nickname
  reads *That nickname is taken. Pick another.* An account an Invitation opened reads *Pick a
  nickname — it's how players will see you.* The client writes the words; the backend names the
  code ([ADR-0022](0022-kernel-negative-space-and-constant-homes.md)).
- **The act** takes `{ nickname }` and nothing else. It stays **repeatable**: keeping your own
  nickname is admitted, and one another account holds is refused with `NicknameAlreadyTaken`.
- **The You tab** edits it with the same act, from the row now called **Nickname**, at any time,
  for as long as nobody else holds the new one. Everybody reads the new nickname from their next
  read. There is no limit on changes.
- **Sign-up** still asks for credentials only, and the account is created without a nickname. The
  gate's first player destination, *not named in full* since ADR-0185, reads ***no nickname***.
- **`/users/me` stops serving `name`.**

### 4. An account an Invitation opens holds no player name

The club types a name and an email when it invites an Administrator. **That name is the
Administrator's**, and it stays there. The club's own pages, such as its Administrators page, use
it, and so do the Administrator's own emails (the invitation, the removal).

**The account the invitation opens holds no player name.** When that person starts playing, they
pick a nickname like anybody else.

**One player surface reads the club-typed name:** *"… runs this group for Ogrody 33"* names the
Administrator by their nickname once they have one, and by the name their club typed until then.
An Administrator who has never played has no nickname to show, and the line must still say who
runs the group.

### 5. The club surface carries the nickname

The club website's **Bookings** and its official groups' **join requests** name each player by
nickname. The *A player* fallback, for an account that reads as nobody, stays. Administrators keep
the names their club typed.

### 6. The wire and the stream

- **Every field that carried a player's name is renamed `nickname`, on every surface**: seats,
  deck tiles, chat people, group people, members, join requests, blocked players and the club's
  booking players. The player record drops `name` and keeps `nickname`. It is the reverse of
  ADR-0171's rename, and the drift check is red between each backend ticket and its client ticket,
  by design.
- **The naming event's next version** (`users.user_named` v2) carries the nickname only. **The
  invitation-opened event's next version** (`users.account_opened_by_invitation` v2) carries no
  player name. An earlier version of either is read with its name ignored, so no account holds one.
- **The users projection drops its name column**, in a new migration.
- **The cross-context read returns each account's nickname.** An account without one reads as
  nobody, as an unnamed account did before.
- **The seed carries no player names**, and the dev console's roster shows nicknames.
- Only `local` runs, so the local event store may be reset after the re-versioning.

### 7. Where an older text quotes a name, it reads through this record

The specs are not rewritten example by example. A sentence that names a player by a name, such as
*Oscar Bertran left your game*, reads with that player's nickname: *oscar.b left your game*.
`the-words.md` §15 says so once for every spec. The ADRs that argued from a name (ADR-0171, and
ADR-0185 §4's *the step shows only the nickname field*) keep their text, read through this record.

## Consequences

**Easier**

- **One identity.** A player chooses one handle, sees it everywhere, and nothing they typed appears
  somewhere they didn't expect.
- **Rakieta holds no player's real name.** That is one less thing to explain in the privacy policy
  #735 will write.
- **The naming is one field**, and the club's desk sees the same handle the players do.

**Harder**

- **A desk reads handles.** A club that knows its players by name reads *ania.k* on its Bookings
  page and on its join requests. This is accepted (Q13); the club's own staff keep their names.
- **A rename reaches everybody at once, with nothing linking old and new.** Somebody who knew
  *ania.k* yesterday reads *ak.padel* today. No history and no *formerly* is shown, and with no
  limit on changes a player can rename every day. If that is abused, a limit is the follow-up.
- **This is the second rename of every read model in two months**, across both clients and the
  club surface. Two pairs of tickets carry it, after #723: #724 and #728, and #725 and #734. The
  drift check is red between each pair until the branch ends.
- **The initials and the stem now break differently.** ADR-0167 §3 cut the initials where the stem
  cuts, *so the two rules stay one*. The initials now break at `.`, `_` and `-`, and the stem
  (ADR-0157) at the first dot only, so `dorota_w` draws `DW` on a poster and `dorota_w` whole in a
  box. Whoever next touches either rule decides whether they meet again.
- **Two events move to v2.** No store outlives this branch, so nothing upcasts today. The day a
  store does, this record has already written the upcast: drop the name.
- **The nickname's characters are narrow.** `[A-Za-z0-9_.-]` has no Polish letters, so *Łukasz* is
  *lukasz*. The rule is unchanged, but it now shapes what everybody reads. Widening it is not
  decided here.
- **The nickname is now the only text that names a player to strangers, and its only fence is its
  characters.** ADR-0171 named a gap for the name: no contact fence. The gap moves to the nickname.
  Digits and dots are legal, so a phone number can be a nickname. If that happens, the intro's
  contact rule (ADR-0170 §2) is the pattern to reach for, and it slots in at the naming.
- **"… runs this group" has two sources.** A player can read the club-typed name for an
  Administrator who hasn't started playing, and the nickname the day after they do.

**Neutral**

- ADR-0185's *"A Name without a Nickname is a new shape"* no longer describes anything. An invited
  account holds neither until its naming at *Start playing*.
- The club's surface and the Administrator's emails still name staff as the club typed them.
- Every QA walk and mock that quotes a name reads through §7, as ADR-0171's walks once read through
  it.
- **Two code names keep the word *name*.** The naming route's path (`PUT /users/me/name`) and the
  phone's `playerName()` both now carry the nickname. *Name* there means *what a player is called*,
  which is the nickname. Renaming the route would be a contract change of its own, and this record
  doesn't ask for one.
