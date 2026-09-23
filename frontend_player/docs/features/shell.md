# shell — five tabs over one stack

> The design record for `src/features/shell/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**The shell is five tabs over one stack, and it remembers nothing.** `TabShell` mounts the
`TabBar` once, below the navigator, and reads the active column off the current path —
`tabForPathname`, by the **first** segment, so ⚡Play stays lit for every screen inside Play.
It is a `Stack` and deliberately **not** `<Tabs>`, which keeps a history per tab and restores
it: built that way, a player who leaves the deck and comes back lands on the deck, and _back
goes where I came from_ fails with **no symptom** — nothing throws and nothing looks wrong
([#227](https://github.com/Raketa02/Raketa/issues/227)). So switching tabs **replaces**, and
entering Play lays down `[Now, Find a game]` — two screens, which is the whole of _back from
Play leaves Play_. Both go through **one function**, `resetShellStack`: a flanking tab lays
down one screen, `enterPlay` lays down two, and the second caller of `enterPlay` is the _Find
a game_ segment, because re-entering the tab from inside it is arriving rather than going
back. **A Play session ends exactly when the reset runs**, which is the definition the Play
state ticket is owed. **A press that would land where the player already is does nothing at
all** — `openTab` takes the pathname the bar's own lit column is drawn from and declines that
one case. Every press ran the reset until 2026-09-10, so tapping Play on Find a game rebuilt
the screen underneath the player: the session ended, the working week went back to the
profile's copy, and whatever was ticked went with it — a reload with no cause, on the gesture
people press twice when something feels slow. The rule the reset serves is _pressing a tab
goes to that tab's start_, and somebody standing on it is already there; from anywhere else in
the tab, including one screen deeper, the press still lays the stack down. **The bar stands
down on exactly one route, the conversation**, where the
composer replaces it ([#400](https://github.com/Raketa02/Raketa/issues/400)): `barStandsDown`
beside `tabForPathname` names the whole path rather than `/chats/*`, `TabShell` does not render
the bar there rather than hiding it, and the room takes the bottom safe-area inset the bar owns
everywhere else — the one exception to design-system §10.1, recorded in Part 16. The column
stays lit while the bar is down. **Two of the five tabs are honest placeholders** now that Now has a screen
([#367](https://github.com/Raketa02/Raketa/issues/367)): one sentence naming what the tab will be
plus that it is not built, one of them a citation of a decision taken elsewhere. **No sentence the
shell writes says "nothing is happening"** — it began as Now's refusal, because Now is where a send
lands and asserting emptiness would be a lie one tap after a challenge went out, and it now governs
the two built tabs' empty states as well. `shellCopy.test.ts` holds that refusal, and it **moved
with the copy** rather than being deleted when the placeholder it was written for died. The **You**
tab still carries the account panel, because signing out is
the only way back to the beginning and the shell arriving is what gave it a home. The bar's
**transitions** follow the two moves: `none` by default, because a replace that slid in from
the right would read as going deeper on the gesture whose meaning is that nothing was kept,
and the push kept for the four Play screens, which genuinely are ones — Find a game is entered,
and the deck, the builder and the pool are each pushed over what stays underneath them.

**The bar stands down on a second route — the yes screen under a challenge**
([#433](https://github.com/Raketa02/Raketa/issues/433),
[ADR-0167](../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
§2). `barStandsDown` names it in full beside the room — `chats`, `challenge`, the id, `yes`, and
nothing after — and for the opposite reason: the room replaces the bar with its composer, and the
yes screen replaces it with nothing, because the screen is the whole phone and its two pills are the
only doors the record gives it; a bar under it would be a way out it does not have. Same mechanism
— not rendered, not hidden, nothing animates — and the screen takes both safe-area edges on its own
frame as the room does. The builder at `…/fill` beside it keeps its bar, which is why the match is
still the whole shape and not a prefix. `TabShell` names the route for one option only: **the iOS
swipe-back is off**, because a swipe that popped to the challenge screen underneath would land
somewhere _Later_ never does; it keeps the shell's own `none` transition deliberately, since the
screen has one motion of its own and a push sliding in under it would be a second. The column stays
lit.

**The second column is Players, and it is the deck** ([#443](https://github.com/Raketa02/Raketa/issues/443),
[ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §1).
It was Around — a placeholder promising _players and courts near you_, drawn with `map-pin`
after `radar` was refused for a tab with no scan behind it (ADR-0135) — and the rename is
**whole**: key `players`, label _Players_, Feather `users` (`user` is You's, and the family
finding stands), route `/players`, and the harness's route table with it, because a
half-rename is the thing a later session trips over. Around's line retired with the tab; nothing
had been decided about courts and they get their own home when they arrive. The Chats panel's
note that _when you count yourself into something tonight_ was Around's now says the phrase has
**no tab**, which is what it has. The screen at the root is `features/play`'s own `DeckScreen`,
named by its route file exactly as Find a game is — the tab has no words of its own for the
shell to compose anything under, and `tabScreens.tsx` holds two entries now, one of them still
a placeholder. **A single-screen root like the other flanking tabs**: the shell keeps no
per-tab history, so Players opens on the deck every time and the held deal is what makes that
cheap; the toggle on it is the screen's own state and lands on Deck on every arrival for the
same reason. What the bar and the header changed to carry it — the glyph, the label cap, a
header with no heading, and the two slots `ShellScreen` now forwards — is
[`_shared.md`](_shared.md)'s.

**Play lost its depth by one, and the reset a caller.** `/play/deck` is gone with the segment
that reached it and the `Stack.Screen` that gave it the push transition
([#443](https://github.com/Raketa02/Raketa/issues/443), ADR-0169 §1), and `enterPlay` is no
longer exported from the shell's surface: the _Find a game_ half of that segment was the reset's
fourth caller and its only outside one, and `resetShellStack` has three callers again — a
flanking tab, ⚡Play and the send. The Play stack is still `[Now, Find a game]`, and the builder
is the depth a test pushes to show a press from inside the tab still lays it down.

**The Players header's right slot is the chip, and its page fills**
([#444](https://github.com/Raketa02/Raketa/issues/444),
[ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §4,
§7). The slot #443 left empty carries _2 want to play you_ — a volt pill the deck draws from the
deal's `pool.want_to_play_you`, at one and above and never at nought, so a header with nothing
waiting has nothing in the slot. `ShellScreen` gained `fill` for the same tab, forwarded and not
designed: the deck's stage takes the height the phone gives it, with the three round buttons in
the pinned `action` slot below it.

**Pull to refresh on Chats** (2026-09-16). `ShellScreen` takes an `onRefresh` and draws the
platform's `RefreshControl` over its page — forwarded, not designed, and absent on every screen
that says nothing — spinning from the pull until the promise settles, refused or not, and never
for a refetch the player did not ask for; a second `refresh` in the same tick is read off a ref
the state could not have rendered yet. `ChatsScreen` hands it both of its lists' keys,
invalidated and awaited, so what the server now says is what the tab then shows. Walked in
`chatsRefresh.test.tsx`; the control itself in `ShellScreen.test.tsx`.

**You draws one more of another feature's sections: the Location area sentence**
([#462](https://github.com/Raketa02/Raketa/issues/462)). `AreaUpdatesNote` sits under
`PlayIntentsSection` and above the account panel, composed exactly as the section above it is;
the sentence, the refresh it is the trace of and the reasons are the profile feature's
([`player_profile.md`](player_profile.md)).

**You is a screen, and the last placeholder went with it**
([#469](https://github.com/Raketa02/Raketa/issues/469),
[ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
§1). `YouScreen` — in a file of its own, as Chats is, because it is not thin — is a header card
over three titled groups of rows and _Sign out_ at the foot: **Playing** (Skill passport ·
Player reliability · What kind of game), **Finding players** (Your week · How far to look ·
Where you play · Who you play with · Game suggestions), **On your card** (How others see you ·
Photos · Tags · Intro · Name). Three groups because the rows answer three questions — what has
the platform concluded about me, what does the matcher read when it looks for a game, what does
a stranger read about me — and the fourth, the account, is not asked on this tab (§9). **The
shell owns the tab's own words and composes the rest**: the title, the eyebrow _Player profile_
and the three group titles are `youCopy`'s, and every row from _Skill passport_ down is the
feature's whose fact it is — `player_record`'s two read-only facts and the door to the sheet,
`player_profile`'s declarations, `auth`'s name — each reading its own fact, saying it in a live
line, and pushing its own screen. What this file decides is which row sits in which group and in
what order, and `theShell.test.tsx` asserts that as an order. A group is a `flab` title over one
`Card` of `DoorRow`s (5.5 as amended, Part 16 2026-09-17), and the header card is the record's
own header, compact. **The one overlay the tab holds** is _How others see you_ — the record
sheet on `{ kind: 'me' }` — because the header card and the row both open it, so whether it is
up is this screen's state and both are handed the same press; the sheet is a sibling of the
screen it covers, as every overlay is. **`PLACEHOLDER_COPY`, `PlaceholderTab` and
`PlaceholderScreen` are gone**, not emptied: the line _your profile, your radius, your week — not
built yet_ was the last citation in the table, every column the bar draws has a screen behind it
now, and an empty union kept for a case that cannot recur is a shape and not a fact.
`shellCopy.test.ts` keeps the two refusals over every sentence the shell still writes, the group
titles included, and asserts the placeholder's line absent so it cannot come back as a
gap-filler. **The pushed screens take the push transition**: `TabShell` names the twelve
`you/…` routes one by one for `animation: 'default'`, as it names every pushed screen, and the
harness's route table spells `you/index` as the file tree does. **`ShellScreen` forwards two
more things, designed nowhere**: `subline`, which _What kind of game_ is the first shell screen
to wear (its one line replaced the section's heading and body, ADR-0179 §2), and
`avoidsKeyboard`, which the _Name_ screen is the first shell screen to need — the scroller and
the pinned action wrapped in `KeyboardAvoidingView` under `KEYBOARD_AVOIDANCE`, as
`SocialStepLayout` already does, and off everywhere else. **Not seen on a device**: the header
card's fit beside a long name, the row lead's 28 pt against the chevron, and the push over the
tab.
