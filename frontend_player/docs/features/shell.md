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
[ADR-0166](../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
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
