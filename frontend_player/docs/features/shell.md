# shell — three tabs over one stack

> The design record for `src/features/shell/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**The shell is three tabs over one stack, and it remembers nothing.** `TabShell` mounts the
`TabBar` once, over the navigator's foot (below it until #881, see the next paragraph), and reads
the active column off the current path —
`tabForPathname`, by the **first** segment, so ⚡Play stays lit for every screen inside Play.
It is a `Stack` and deliberately **not** `<Tabs>`, which keeps a history per tab and restores
it: built that way, a player who leaves a screen and comes back lands on it, and _back goes
where I came from_ fails with **no symptom** — nothing throws and nothing looks wrong
([#227](https://github.com/Raketa02/Raketa/issues/227)). So switching tabs **replaces**, and
entering Play lays down `[Home, Play]` — two screens, which is the whole of _back from Play
leaves Play_. Both go through **one function**, `resetShellStack`, reading **one table**,
`TAB_STACK`: Home lays down nothing over itself, You and ⚡Play each lay their root over Home, and
_It's a game!_'s _Open game_ lands on `[Home]` before pushing the booked game's details. **Home is
the bottom of every stack and is kept, never laid down again** (2026-11-15): a press pops back to
the Home already there (`dismissTo`) and pushes only the tab's own screens. It used to be
replaced by every press of every tab — ⚡Play's included, since its stack starts with Home — and
Home is the heaviest screen in the app: a Galaxy A55 measured about four seconds of a frozen bar
per Home or Play press, all of it Home being rebuilt. Two things follow. **You is `[Home, You]`**,
as Play is `[Home, Play]`, so _back_ from You's root is Home rather than out of the app — Android's
own rule for a top-level screen that is not the start. And **a press that lands on Home shows its
top** (`homeStart`, Home's `ShellScreen` scrolls its page back, unanimated), because a kept page
keeps its scroll and _a tab press goes to that tab's start_; _back_ to Home from a screen pushed
over it is a return, not a landing, and keeps the scroll. And **`HomeScreen` is memoised**: the
route that draws it is drawn again on every move the navigator makes, so a kept, unmemoised Home
re-rendered every row, card and poster on every press — most of a second on the same device. You
and Play are still laid down fresh on every press, so _the shell keeps no per-tab history_ is
exactly as true as it was. **A press that would land where the player already is does nothing at
all** — `openTab` takes the pathname the bar's own lit column is drawn from and declines that
one case: every press ran the reset until 2026-09-10, so tapping Play on Play's root rebuilt the
screen underneath the player — a reload with no cause, on the gesture people press twice when
something feels slow. From anywhere else in the tab, including one screen deeper, the press still
lays the stack down. **Arriving in the app is a second move, `useShellLanding`** (2026-11-04): a
rating pass comes back into an app whose tree it tore down, at `/`, and laying its group or passport
down through `resetShellStack` waited for Home to be drawn first — a blink on a device. The landing
is one reset of the navigation state at the root, `(app)` › `(tabs)` › the tab's start and the
screen on top, made by the entry gate before the shell mounts; screens are named as `Stack.Screen`
names them, resolved against `PUSHED_SCREENS` and the two unpushed roots
([`onboarding.md`](onboarding.md)'s landing paragraph). **The bar stands down on exactly one route, a booked game's room**, where the
composer replaces it ([#400](https://github.com/Raketa02/Raketa/issues/400)): `barStandsDown`
beside `tabForPathname` names the whole path, `TabShell` does not render the bar there rather than
hiding it, and the room takes the bottom safe-area inset the bar owns everywhere else — the one
exception to design-system §10.1, recorded in Part 16. The column stays lit while the bar is
down. It also stands down on Android while the keyboard is up, on any route (below). **No sentence the shell writes says "nothing is happening"** — it began as Now's refusal,
because Now is where a game lands and asserting emptiness would be a lie one tap after one did, and
it governs every empty state the shell writes. `shellCopy.test.ts` holds that refusal, and it
**moved with the copy** rather than being deleted when the placeholder it was written for died.
The bar's **transitions** follow the two moves: `none` by default, because a replace that slid in
from the right would read as going deeper on the gesture whose meaning is that nothing was kept,
and the push kept for the screens pushed over a tab, which genuinely are ones.

**The bar floats over the screen, and every screen inside the tabs ends at its reach**
([#881](https://github.com/Raketa02/Raketa/issues/881), 2026-11-25;
[ADR-0210](../../../docs/adr/0210-the-tab-bar-floats-as-glass-and-its-selection-travels.md) §3,
design-system §10.1). It was a flex sibling under the stack, which ended every screen above it for
free; it is now drawn absolutely at the phone's foot and owns no layout, so the screens draw to the
bottom of the phone — the prefactor that left the dock (#883) a look change only. **The reach** is
the room the bar takes there: the dock's lift and its 54 while it is drawn (66 on the A32, 88 on a
notched iPhone, #883), and nothing while it stands down. `TabShell` says it
(`useSaysTabBarReach(barShown)`), and so does the administrator's `AreaShell`, whose bar is the same
dock with two columns. It is a followed value in `shared/ui`
(`tabBarReach.ts`, the page band's pattern) rather than a context, because sheets and the toast
host sit at the root, above the shell; a shell mounting puts its first value in place before what
it holds renders, so no screen draws a first frame at the phone's foot. **What reads it**:
`ShellScreen` ends its page at reach + 15 — or, with an `action`, ends its layout at the reach so
the CTA sits above the bar in flow — and every tab screen with its own scroller ends at reach + the
gap it kept (the group page and its tabs, the deck's ✕ · i · ✓, game details, the booked game,
Post a game, Edit group, Join a group, Members, New group, Play, the See all pages, _Groups heating
up_ and the administrator's screens). Post a game and _New group_ stand at reach + the gutter, and
Group info and the administrator's You end at the reach, their feet pinned. **What a page says is on
screen is what shows above the bar**: `ShellScreen` hands Home's rows its band less the reach, so a
card under the bar is not seen and a FOR YOU line unfolding brings its foot to the bar's top, as
before. **Rankings ends at the reach** like a pinned screen — whether the reader's row is on screen
(the jump button) and where a jump centres it are FlatList's own measure of its frame, which takes no
inset — so its rows do not pass under the bar; the dock (#883) inherited that call.
The Undo toast stands 9 above the reach, or above the inset in the chat (`useRoomAtTheBottom`, which
_Start playing_ also ends at); the toast stands 9 above the **full** reach on every screen
(`useFullTabBarReach`), so it still clears the chat's composer. `TAB_BAR_HEIGHT` is private to the bar
now. **What it costs**: on an iPhone with the keyboard up, a form that avoids it (New group, Edit
group, Where you play) keeps the reach under its last field, room nobody sees until scrolled to the
end. Two costs #881 recorded went with the dock (#883): the bar no longer grows past its reach at the
1.6 text cap — the dock is 54 at every size — and a scroller's indicator, drawn at the screen's edge,
no longer runs under the bar, which stands 12 in from either side.
`theShell.test.tsx`, the group page's Fill in, You're in and Games suites, `theFill.test.tsx` and
`administratorArea.test.tsx` walk it against the reach worked out from the theme
(`test-support/tabBarReach.ts`).

**The bar is the dock, and the selection marker stands under the lit tab** ([#883](https://github.com/Raketa02/Raketa/issues/883),
2026-11-25; ADR-0210 §2, §4–§7, design-system §10.2). `TabBar` draws a rounded slab 54 tall, 12 in
from each side and lifted the larger of 12 and the bottom inset: `color.glass` over `expo-blur` on
the iPhone, and opaque `surface` on Android, where the A32 measured the blur costing frames
(`theme.glass.android`, off). Its three columns are Ionicons over `tag` labels — outlined in
`tabIdle` while idle, filled `coral` with a `coralInk` label while lit, the bolt filled always — and
the lit one sits on an opaque `coralSoft` capsule, 75 × 42, which is the dock's own layer under
the words, placed from the window's width so the first frame has it. The ⚡Play disc, its ring and
`shadow.fab` are gone, so Play dims under a finger like the other two; Home's badge stays on the
house. **The shell is unchanged**: the lit tab is still the URL's, so the marker stands under
whichever tab that is — under Play for a group opened from Home's _Groups heating up_, under Home
inside a booked game. The administrator's area draws the same dock with Groups (`people`) and You.
`theShell.test.tsx` and `administratorArea.test.tsx` walk where the marker stands (`markerUnder`);
the look is the phone
walk's ([#885](https://github.com/Raketa02/Raketa/issues/885)), and a phone build needs a native
rebuild for `expo-blur`.

**The marker travels** ([#884](https://github.com/Raketa02/Raketa/issues/884), 2026-11-25; ADR-0210
§8, design-system §10.2). On every change of the lit tab after the dock's first draw it slides to
the new one on `motion.tabMarker`'s spring — 460 ms at damping ratio 0.75, so it overshoots by a few
points and settles — stretching like a bubble with its own speed and recoiling as it brakes, and
the new tab colours in from 140 ms into the slide while the tab left goes idle at once. The shell
needs nothing for it: the lit tab is the URL's, so a press, a landing, a notice landing in another
tab, a group opened from Home's _Groups heating up_ and back all change the one value the bar is
handed, and **the bar cannot tell them apart**. Nothing moves where that value does not change — a
press of the lit tab, a branch's own pushes — and nothing moves on the dock's first draw, which is
also every time it comes back after the chat or Android's keyboard, since the shell draws it anew.
Under Reduce motion the marker is placed and the colours switch at once. `markerTravels.test.tsx`
walks it through the shell, `hottestGroups.test.tsx` the trip to Play and back, and
`administratorArea.test.tsx` the Administrator's two tabs. **A press while the marker is still
travelling cannot be walked through the router harness**, whose flush on the second navigation lands
the first slide, so the turn mid-flight is the bar's own suite's. The feel is the phone walk's
(#885), and so is whether the slide stutters while a tab's screen mounts under it
([#886](https://github.com/Raketa02/Raketa/issues/886), measured on the A32 by the spike).

**On Android the bar stands down while the keyboard is up** ([#882](https://github.com/Raketa02/Raketa/issues/882),
2026-11-25; ADR-0210 §9, design-system §10.1). Android shrinks the window for the keyboard, and the
floating bar sits at the window's foot, so it would ride up above the keyboard and over a field near
it: Intro, Name, New group, Edit group, Post a game and the administrator's forms, whose pages no
longer end above the bar. `TabShell` and `AreaShell` both read `useKeyboardShrinksTheWindow` (up, on
a phone whose window resizes for it) and treat it as the chat's room is treated. The bar is not
rendered and the reach is nothing, so a form's page ends its own 15 above the keyboard and the Undo
toast stands 9 above the bottom inset; the toast keeps the full reach. Nothing animates, and the bar
is back, its column lit, when the keyboard goes. An iPhone draws its keyboard over the window and the
hook never answers yes there, so nothing redraws. **The platform's `keyboard.ts` is the app's one
listener for the keyboard's show and hide.** It already held the avoidance value and the dismissal,
so the reading joined it (ADR-0210 §9 corrects the PRD's _a new port_), and the lint fences React
Native's `Keyboard` to it as it fences `Share` to the share port. `theShell.test.tsx` walks New group
on both phones with `fakeKeyboard()`, `administratorArea.test.tsx` the area's New official group,
and `theFill.test.tsx` the Undo toast. **Not seen on a device**: the bar going and coming with the
keyboard is for the phone walk (#885).

**You draws one more of another feature's sections: the Location area sentence**
([#462](https://github.com/Raketa02/Raketa/issues/462)). `AreaUpdatesNote` sits under
`PlayIntentsSection` and above the account panel, composed exactly as the section above it is;
the sentence, the refresh it is the trace of and the reasons are the profile feature's
([`player_profile.md`](player_profile.md)).

**You is a screen, and the last placeholder went with it**
([#469](https://github.com/Raketa02/Raketa/issues/469),
[ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
§1). `YouScreen` — in a file of its own, because it is not thin — is a header card
over three titled groups of rows and _Sign out_ at the foot: **Playing** (Skill passport ·
Player reliability · What kind of game), **Finding players** (Your week · How far to look ·
Where you play · Who you play with · Game suggestions), **On your card** (How others see you ·
Photos · Tags · Intro · Name). Three groups because the rows answer three questions — what has
the platform concluded about me, what does the matcher read when it looks for a game, what does
a stranger read about me — and the fourth, the account, is not asked on this tab (§9). **The
shell owns the tab's own words and composes the rest**: the title and the three group titles are
`youCopy`'s — the eyebrow _Player profile_ over the title went at the product owner's ask (#529,
2026-10-02), since the bar under the screen already says _You_ — and every row from _Skill passport_ down is the
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
now, and an empty union kept for a case that cannot recur is a shape and not a fact. **_Sign out_ is pinned** (#529, 2026-10-02): the account panel is the shell's `action`, under
the scroller and above the bar, so it is at the tab's foot in one place however many rows are over
it — the administrator's You tab pins it the same way — and `AccountPanel` puts no step of its own
above the button, since whoever pins it spaces the slot.
`shellCopy.test.ts` keeps the two refusals over every sentence the shell still writes, the group
titles included, and asserts the placeholder's line absent so it cannot come back as a
gap-filler. **The pushed screens take the push transition**: `TabShell` gives
`animation: 'default'` to every name in `pushedScreens`, which names the `you/…` routes one by
one as it names every pushed screen, and the harness's route table spells `you/index` as the
file tree does. **The list is held to the file tree** (`pushedScreens.test.ts`): every route
under `(tabs)` but Home's and You's roots must be on it, and nothing else may be. A route left
off still opens, swapped in with no transition, and Info over a group's page — whose header is
the page's own — read on a device as a blink; Post a game, a game's details and a rescue had
shipped the same way. **`ShellScreen` forwards two
more things, designed nowhere**: `subline`, which _What kind of game_ is the first shell screen
to wear (its one line replaced the section's heading and body, ADR-0179 §2), and
`avoidsKeyboard`, which the _Name_ screen is the first shell screen to need — the scroller and
the pinned action wrapped in `KeyboardAvoidingView` under `KEYBOARD_AVOIDANCE`, as
`SocialStepLayout` already does, and off everywhere else. **Not seen on a device**: the header
card's fit beside a long name, the row lead's 28 pt against the chevron, and the push over the
tab.

**Play is a _Groups | Explore_ segment, and the shell draws it**
([#512](https://github.com/Raketa02/Raketa/issues/512), play mocks 1 and 3, PRD #500 stories 1–4).
`PlayScreen` is the shell's for the reason Home and You are — a tab owns its own words and
composes other features' pages under them: _Groups_ is `features/groups`' list, _Explore_ is
`features/find_a_game_next`'s empty screen. The segment is `Segment`'s new **`prominent`** form —
`ink` under a `surface` label on a `paper2` track, a `btn`-high thumb, and no shadow although the
mocks draw one (design-system 6.3 as amended) — and it is **pinned above the page** rather than in
`ShellScreen`'s header, whose title column would take half its width. **The segment is the first
value the phone remembers** ([ADR-0188](../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)):
`usePlaySegment` reads it once per account per session from `shared/lib/preferences` into the
Query cache (under `shared/lib/preferences`' `phonePreferenceKeys`, so the next two values'
owners share one root; `networkMode: 'always'`, never stale), and **draws nothing until the read
lands** — a local key, so a frame — because a screen that drew Groups and jumped to
Explore is §4's flash. A choice is written to the cache and then to the phone, fire and forget.
`playSegmentFrom` turns whatever was saved into a segment, and anything this build does not know
is Groups — and so is a phone that cannot tell whose choice to read, which is §4's store that
cannot be read. The account is read from the cache once and never observed, so entering Play
never refetches `/users/me`. The walks are `components/playSegment.test.tsx`: the segment across a relaunch and
across a tab change, another account on the same phone, a sign-out, and a value that is not a
segment. **Not seen on a device.**

**The You header's right slot is the profile switcher's chip** ([#518](https://github.com/Raketa02/Raketa/issues/518),
club 7; ADR-0185 §3 amends ADR-0179 §1's locked header by this element). The You route hands it
to `YouScreen` (`headerRight`), which forwards it to `ShellScreen`'s right slot: the chip is the
administrator feature's, and the shell importing it would close a cycle through `auth`, so the route
file — whose job is composition — composes it. What it draws, its sheet and the switch are that
feature's ([`administrator.md`](administrator.md)). **It draws
nothing for an account that only plays**, so the tab most people see is unchanged. **Not seen on a
device.**

**Now is Home** ([#550](https://github.com/Raketa02/Raketa/issues/550), the Games & Fill in
screens A1), renamed whole — key `home`, label _Home_, `HomeScreen`, `HOME_COPY` (title only; its
two lines are still true of the tab), `landOnHome`, and the harness's `HOME_TAB_LINE` — on the same
route, `/`. **Home carries a badge**: the booked games that need you, handed to the bar as
`gamesNeedingYou`. The price is stated, as #326 stated the first badge's: **the shell holds the
read the count comes from for the whole session**, so an act that invalidates it re-reads it at
once.

**The You tab asks the fourth question since money arrived** — _how do I pay for a game_ — in an
**ACCOUNT** group after _On your card_ and before _Sign out_ (ADR-0189 amending ADR-0179 §9; the
screens A7), which the paragraph above predates. It holds _Games & money_ (`proposals`,
[#554](https://github.com/Raketa02/Raketa/issues/554)) then _Payments_ (`payments`, #552);
_Notifications_ (#559) joins under them. Both screens are pushed under `you/` and listed in
the shell's `PUSHED_SCREENS`, so they take the push transition and keep the You column lit.

**A booked game is pushed over Home** ([#556](https://github.com/Raketa02/Raketa/issues/556);
the Games & Fill in screens A8) under a `booking` segment `INSIDE_A_TAB` counts as Home's — its
details, its chat and its result, each a `Stack.Screen` with the push transition — and **the bar
stands down in its room** (`/booking/{id}/chat`), for the room's own reason. `HomeScreen` puts
`proposals`' _TO CONFIRM_ above the rail, drawn only while a payment waits. _It's a game!_'s _Open
game_ lays Home down and pushes the booking's details (`openGame(bookingId)`).

**Home has a bell, and the notices are held around the tabs** ([#559](https://github.com/Raketa02/Raketa/issues/559);
the Games & Fill in screens A9). `HomeScreen` puts `notifications`' `NoticeBell` in `ShellScreen`'s
right slot; the list behind it is `/notices`, pushed over Home under a segment `INSIDE_A_TAB` counts as
Home's, with the push transition, and the bar stays up there. `TabShell` mounts
`NoticesHost` inside the fill, after the bar, for the session — the phone registered, a notice while
the app is open drawn as the banner over every screen, a tapped push opened — and lists
`you/notifications` in `PUSHED_SCREENS`; _Notifications_ is the ACCOUNT group's third row, under
_Payments_ (mock 50). **The price, stated as the badges' were: the shell now holds
`GET /players/me/notices` for the session** — the banner's second source — read again every minute
while the phone is not being pushed, so every launch makes it and the harness's gate stubs it.

**The old loop left, and the bar is Home · ⚡Play · You for good**
([#576](https://github.com/Raketa02/Raketa/issues/576), PRD [#569](https://github.com/Raketa02/Raketa/issues/569)).
The Players and Chats columns, the `classic_play` flag that drew them (and `useFollowedFeature`, the
followed read the bar took it through), the Chats tab's inbox and its pull to refresh, the yes
screen the bar stood down on, Find a game's builder and pool under Play, the old game screen at
`/games/[id]`, and the Play session the reset used to end are gone — so `TabBar` takes no switch and
draws three fixed columns, `SHELL_TAB_ROOT` names three routes, and `barStandsDown` names one.
**Home is booked games only**: its rail is `proposals`' `HomeRail` — the heading's count, the pager
and its dots, the empty state and the error note, as before — and the badge is `useHomeBadge`'s,
the server's `needing_you` and nothing added to it. So **the shell holds one list**, `GET /home`
(and the notices, above): it no longer holds `GET /games`, `GET /plans` or `GET /challenges`, and an
act that invalidates the games list now marks it for the result screen that reads it rather than
re-reading it at once — `theFill.test.tsx` asserts the flag. The bar's label cap stays where five
columns left it, 1,6: at a third of the screen every word fits at more than twice that, so the
width no longer decides it (`tabBarLabelCap.test.ts`). The walks are `theShell.test.tsx` (three
columns, the booked badge, no old-loop read, the bar standing down in a booked room) and
`homeAndBookedGame.test.tsx` (Home booked-only, its pager and badge). **Not seen on a device**: the
three-column bar at a large text size.

**Home pulls to refresh** (the bug report's P2): the pull re-reads what a notice does —
`proposals`' `rereadHome`, the games, _TO CONFIRM_ and the live yeses — and `ShellScreen`'s
`onRefresh` spins until they have landed, refused or not.

**_Finding players_ is three rows** ([#582](https://github.com/Raketa02/Raketa/issues/582)):
_Your week · Where you play · Who you play with_. _How far to look_ and _Game suggestions_ left
with the two questions they answered again — the Search radius and the Proposals opt-in, read
only by the old loop's ranking — and their screens, `you/radius` and `you/game-suggestions`,
left `PUSHED_SCREENS` with them. The group keeps its title: what it holds is still what a proposed
game reads. The walk is `theShell.test.tsx`, which asserts neither title is drawn.

**ACCOUNT ends with _Blocked players_** ([#587](https://github.com/Raketa02/Raketa/issues/587)):
`blocks`' row under _Notifications_, its line _Nobody_, _1 player_ or _2 players_, and its screen
`you/blocked-players` in `PUSHED_SCREENS`. The gate stubs `GET /blocks` (none), because the row reads
it on every visit to the tab. The record is [`blocks.md`](blocks.md).

**_Name_ is _Nickname_** ([#728](https://github.com/Raketa02/Raketa/issues/728),
[ADR-0199](../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). The **On your
card** group's last row is `auth`'s `NicknameRow`, its line the nickname whole and never with an
@, and the header card draws the nickname large with nothing under it. The screen behind the row is
still `you/name`: the route keeps the word, as the act's path does. The paragraphs above that say
_Name_ read through it.

**_Show me in General_ closes _On your card_** ([#778](https://github.com/Raketa02/Raketa/issues/778),
the You screen 3.14), after _Nickname_: `player_profile`'s `ShowMeInGeneralRow`, the one row on the tab
that is a switch rather than a door. The record is [`player_profile.md`](player_profile.md).

**Home asks a member of a group rated in nothing for a level, first**
([#731](https://github.com/Raketa02/Raketa/issues/731), ADR-0200 §7). `groups`' `HomeLevelCard`
is drawn at the top of Home, above _TO CONFIRM_ and the rail, because until she has a level nothing
under it can happen; what it says and when, and the reads it costs, are in
[`groups.md`](groups.md). The gate stubs both reads empty, so a suite's Home draws no card unless it
puts the player in a group. **Calls made here**: its place on Home; the pull does not re-read it.

**_Finding players_ is _Your games_** ([#733](https://github.com/Raketa02/Raketa/issues/733),
ADR-0200 §10). Nothing on the tab finds players any more, so the group holding _Your week · Where
you play · Who you play with_ is named for what they are read by — a game proposed to the player.
`YOU_COPY.groups.findingPlayers` became `yourGames`, and the three screens behind the rows wear it
as their eyebrow. The paragraph on #582 above that says _the group keeps its title_ was true until
this one.

**Home holds FRIEND REQUESTS above Your games** ([#753](https://github.com/Raketa02/Raketa/issues/753);
the friends screens §6; Q13): the level card, _TO CONFIRM_, then `friends`' `FriendRequestsRow`, then
the rail — drawn only while a request waits. The shell hands it the two things that are
`player_record`'s, the reliability chip (`PlayerScoreTag`) and the record a card's face opens, so
`friends` never imports the feature that draws its record button. #757 adds FRIENDS GAME above it.

**ASKED FOR A LEVEL sits under FRIEND REQUESTS** ([#765](https://github.com/Raketa02/Raketa/issues/765);
the friends screens §6.4; Q129): `friends`' `LevelAsksRow`, drawn only while a friend's ask waits,
handed the record a face opens — one sheet for both rows (`HomeFriendRows`) — the bell's re-read, and
`notifications`' `OPEN_NOTICE_WORDS.unstarted` for a start that fails. **It stands in place of the
level card** — `groups`' rule, which reads the same Home, so the shell still draws `HomeLevelCard`
plainly. **What a level got changes on Home is the shell's** (`useRereadAfterALevel`, exported): the
sport's ask card dropped from Home's cache and Home and the bell re-read, handed by the entry gate to
`useEndOnboardingPass` and run as a rating pass ends — the record is [`friends.md`](friends.md).

**You › Friends is composed here** ([#754](https://github.com/Raketa02/Raketa/issues/754)).
`friends`' row closes the You tab's _Your games_ group, and `YouFriendsScreen` mounts `friends`' page
with the three things that are other features' handed in: the record a row opens (`player_record`'s),
and the Add friends sheet's group tiles and door into Members (`groups`' `MyGroupMonogram` and
`groupMembersRoute`) — each of those features draws a `friends` control, so `friends` importing them
back would be a dependency both ways. `you/friends` is a pushed screen. The record of the page is
[`friends.md`](friends.md).

**_Invite a friend_ into an empty seat is composed here** ([#760](https://github.com/Raketa02/Raketa/issues/760)):
`InviteAFriendScreen`, at `booking/[bookingId]/invite`, mounts `friends`' page and its picker with one
seat around `proposals`' `SeatInvite` (the game, and who is on it) and `InviteOrder` (the order at the
foot), with `groups`' doors in the Add friends sheet — three features, each read by another, so
neither can draw the rest. The pick is the screen's own; the record of it is
[`proposals.md`](proposals.md).

**Home has a trophy left of the bell, and Rankings is pushed over Home** ([#775](https://github.com/Raketa02/Raketa/issues/775);
the rankings screens §1, §2; Q11, Q13). `HomeScreen`'s right slot is a row now, `rankings`'
`RankingTrophy` then `notifications`' `NoticeBell`, so the bell keeps the corner. `/rankings` is a
pushed screen (`PUSHED_SCREENS`) under a segment `INSIDE_A_TAB` counts as Home's, so the Home column
stays lit there, as on the notices. The trophy reads Home's own read, so it costs no request; the
page's reads are the feature's ([`rankings.md`](rankings.md)). The entry gate lands a pass begun on
Rankings back on it with Home beneath (`useShellLanding`), as it lands a group with Play beneath.

**_Show me to new people_ closes _On your card_** ([#799](https://github.com/Raketa02/Raketa/issues/799)):
`player_profile`'s `ShowMeToNewPeopleRow`, in the place `ShowMeInGeneralRow` stood — the paragraph
above's row, renamed with its switch. The record is [`player_profile.md`](player_profile.md).

**The five Home rows begin below _Your games_, HOTTEST GROUPS first**
([#800](https://github.com/Raketa02/Raketa/issues/800); ADR-0204; the Home rows screens §1).
`HomeScreen` draws `groups`' `HottestGroupsRow` after `HomeRail`, and the pull re-reads it beside
Home's own reads (`rereadHomeGroups`, the row and the Groups list) — each row reads on its own, so a slow or failed one holds up
nothing. **A reader in no group** reads _Join a group to get games — the hottest ones are just below._
where _Play finds you one._ stood (§31.1): the first empty line is the tab's and stands, the second is
handed to `HomeRail` from `groups`' answer (`useInNoGroup`) and its words (`GROUPS_COPY.hottest`), as
the empty sentences have always been handed down. The walk is `groups`' `hottestGroups.test.tsx`.

**NEW IN RAKIETA follows HOTTEST GROUPS, and See all is pushed over Home**
([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows screens §1, §5). `HomeScreen`
draws `discovery`'s `NewInRakietaRow` after `HottestGroupsRow` — Same competitive level (#802) will
stand between them — and the pull re-reads it (`rereadDiscovery`). **The shell hands it nothing
else**: accepting a request on FRIEND REQUESTS turns that person's envelope to ✓ on the row because the
row's reads list people (`LISTS_PEOPLE`) and every friend write re-reads those. See all is
`/new-in-rakieta`, in `PUSHED_SCREENS` and `INSIDE_A_TAB` (Home stays lit). The record is
[`discovery.md`](discovery.md).

**Home says what of it is on screen** ([#804](https://github.com/Raketa02/Raketa/issues/804); the
Home rows mechanics §9.2). `HomeScreen` turns on `ShellScreen`'s **`watchesOnScreen`** — forwarded,
not designed, and off on every other shell screen, whose scroller says nothing of where it is. With
it on, the page's scroller hands its rows `shared/ui`'s `PageOnScreen` (`useWatchedPage`): how far
it is scrolled and how tall it shows, sampled every frame and read again where a drag or a fling
comes to rest — and **nothing while Home is not the screen in view**, a screen pushed over it,
another tab, the app in the background (`useFocusEffect` and `useAppInBackground` in a child, so a
shell screen drawn outside a navigator never asks; coming back says the band again). Nothing drawn
changes, and nothing re-renders as the page moves: the band is followed, not state. What a row does
with it is `discovery`'s.

**Every frame, because ten times a second stopped every press on Home on Android** (2026-11-21,
`ON_SCREEN_SAMPLE_MS`). React Native 0.76's Android scroll view throttles _every_ scroll event by the
page's `scrollEventThrottle`, the end of a scroll included, so a scroll that came to rest within 100
ms of the last sample — a FOR YOU line scrolling the page to show itself, always; a fling, now and
then — never said it had. `ScrollView`, having heard the momentum begin and never its end, took
itself for still moving and claimed every touch that started on it: no line header, tile, face,
friend button, pill or link on Home reached its press until the reader dragged the page. On a Galaxy
A32, eleven of eleven presses across the five lines failed at 100 and none at 16, under which
Android throttles nothing. A larger figure here is that bug again.

**Home's header reads envelope, bell, trophy, and what waits on the player is behind the envelope**
([#816](https://github.com/Raketa02/Raketa/issues/816), PRD #810;
[ADR-0205](../../../docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
§1, §2, §4; home refactor 1 and 2). `HomeScreen`'s right slot is `NeedsYourAnswer`, then
`notifications`' `NoticeBell`, then `rankings`' `RankingTrophy` in the corner — the trophy took it from
the bell, so the paragraph on #775 above that says _the bell keeps the corner_ was true until this one.
**The envelope** is an `ink` Feather `mail` in a 44pt target named _Needs your answer_, drawn only
while a friend request or an ask for a level waits; the slot is right-aligned, so without it the bell
and the trophy stay put. **It opens Needs your answer**, `shared/ui`'s `BottomSheet` with
`closesOnSwipe` (✕, the scrim, or a pull down its head), kept mounted so its title takes a screen
reader's focus on opening. It holds `friends`' `FriendRequestsSection` and `LevelAsksSection`, handed
what is other features' as `HomeFriendRows` handed it before: the chip and the record
(`player_record`'s), and the bell's re-read. **Where the sheet stands is `domain/needsYourAnswer`'s**:
closed, open, or aside under a record a face opened — drawn inside the sheet, for iOS's second-window
reason (`discovery`'s vibe sheet) — and up only while something waits. **The last answer closes it for
good** and the envelope goes; something arriving later brings the envelope back and never the sheet.
**Get your level or Carry on closes it for good, then starts**: the start navigates, so the shell runs
`friends`' `useGetAskedLevel` beside the sheet, never in it, and shows the _level asked_ notice's toast
for a start that fails. **Home's body** loses FRIEND REQUESTS and ASKED FOR A LEVEL, and _Get your
level_ is drawn whether or not someone asked (`groups`' rule, [`groups.md`](groups.md)). _TO CONFIRM_
and FRIENDS GAME stay on Home until #817 moves them into the sheet; the envelope's count is #819's.
The walk is `theShell.test.tsx` (_Needs your answer_: the header's order with and without the envelope,
the mark, the title's focus, the sections' order and hidden empties, ✕, the scrim and the pull, the
self-close and what arrives after it). **Not seen on a device**: the header against mock 1, the sheet
against mock 2, the pull and its spring back.

**TO CONFIRM and FRIENDS GAME join the sheet, first and second, and links and notices land on it**
([#817](https://github.com/Raketa02/Raketa/issues/817), ADR-0205 §1; Q14, Q24, Q25, Q32). The sheet
reads **TO CONFIRM · n**, **FRIENDS GAME · n**, then `friends`' two — `proposals`'
`ToConfirmSection` and `FriendsGameSection` above `friends`' sections — and **Home's body is _Get your
level_, _Your games_ and the five rows**. The envelope counts all four off `proposals`'
`useAnswersWaiting`: a read in flight or refused counts nothing, so a failed _To confirm_ read draws
no envelope by itself (ADR-0205 §3). **Home's tab badge is unchanged** — `needing_you`, the payments
to confirm among it.

- **The fill is carried in** (`proposals`' `useSheetFill` / `FillInASheet`): a sheet keeps the root's
  contexts only, and the fill is mounted around the tabs, so the shell reads it beside the sheet and
  hands it in. Its overlays — the confirmation **Confirm** and **Fix** open, the setup an
  invitation's _Accept_ opens, _It's a game!_ — are drawn inside the sheet while it is up, for the
  record's iOS reason.
- **Where the sheet stands grew two states** (`domain/needsYourAnswer`): `underTheFill`, beneath what
  the fill put up — back when it goes if anything still waits, closed with it when nothing does, and
  **closed for good once _It's a game!_ was raised**, whatever still waits; and `asked`.
- **A link or a notice asks for it** (`openNeedsYourAnswer`, `components/needsYourAnswerAsked.ts`):
  Home laid down as `openTab` lays it, and the kept Home's sheet told, by a module-level listener as
  `homeStart`'s landing is. **An ask nobody hears is held** for the next Home to subscribe — a stack
  that began somewhere else gets its Home from `openTab` itself, mounted after the ask — and taken
  once. The sheet hears the fill again as it opens, so one opened over a fill sheet already up
  steps aside under it. **Asked, it waits for the reads behind it** — Home's and the payments to
  confirm, which the link or the notice re-read — and opens once they land if anything waits by then,
  or stays closed: the sheet is never shown empty. Its callers are `links`' friend link and
  `notifications`' `FRIEND_REQUEST` and `FRIENDS_GAME_INVITATION`.

The walks: `theShell.test.tsx` (the four sections' order, the envelope for a payment or an invitation
alone), `proposals`' `friendsGames.test.tsx` and `homeAndBookedGame.test.tsx` (the tiles, answering,
the setup's and the confirmation's hand-back, _It's a game!_ closing the sheet, the badge), and
`links`' and `notifications`' suites for the landings. **Not seen on a device**: the To confirm and
Friends game tiles against mock 2, and every sheet the fill draws over this one — on iOS each is a
native window opened inside the sheet's; nothing in jest can show that it presents.

**The envelope carries the bell's count mark, and closing the sheet records a visit**
([#819](https://github.com/Raketa02/Raketa/issues/819), ADR-0205 §2, §3; home refactor 1). The badge
is `shared/ui`'s `CountBadge`, tone `news`, in ink — **the bell's, unchanged** (design-system 10.3) —
on a glyph box of its own inside the 44pt target, as the bell's is: _99+_ above 99, nothing at
nought (`envelopeFigure`, `shellCopy.ts`). **It counts what arrived since the sheet was last closed**,
as the server counts it on Home's read (`proposals`' `useAnswersWaiting`). Spoken on the envelope's
name, _Needs your answer, 2 new_, exactly above 99 (`envelopeSpoken`), and hidden as a mark. **While
anything waits the envelope stays**, with a count or without.

- **Every way the sheet goes for good is a close** (`wentForGood`, `domain/needsYourAnswer`): from
  open, aside or under the fill to closed — ✕, a swipe, the backdrop, the self-close after the last
  answer, a record or a fill's sheet closing over nothing left, _It's a game!_, and a hand-off to a
  screen — or straight to asked, a link or a notice asking again in the render that closed it.
  Stepping aside is not, since the sheet comes back; nor is a sheet a link or a notice asked for that
  never opened, since nothing was shown. **A sheet a link or a notice opened counts the same.**
  `NeedsYourAnswer` reads the step in an effect, after the reducer has moved, and calls `proposals`'
  `useNeedsYourAnswerVisit`, which owns the watermark, the write and the badge
  ([`proposals.md`](proposals.md)).
- **What the visit says was seen is what the sheet was shown on** (`sheetIsShown`): open with
  something in it. Up beneath a record or a fill's sheet is not shown — their scrim covers it — so a
  read that lands under _It's a game!_, which closes the sheet for good, stays new.
- **The envelope, and so the sheet, are drawn off Home's one read now**, _TO CONFIRM_ included: the
  paragraph on #817 above that says _a failed To confirm read draws no envelope by itself_ and that
  an ask waits for _Home's and the payments to confirm_ was true until this one. A failed Home read
  draws no envelope, and an ask waits for Home's alone.

The walk is `envelopeCount.test.tsx`. **Not seen on a device**: the badge on the envelope against
mock 1, where it sits over the mail mark's corner as the bell's does over the bell.

**The five Home rows fold into FOR YOU, and which line is open is the shell's**
([#820](https://github.com/Raketa02/Raketa/issues/820), ADR-0205 §5, §8; the Home rows screens §1,
§2; home refactor 3–13). Under _Your games_, `ForYou` draws `shared/ui`'s `FoldingLines` — the eyebrow
_FOR YOU_ (`HOME_COPY.forYou`) — and five `FoldingLine`s in ADR-0205 §5's order, each its feature's:
`groups`' `useHottestGroupsLine`, `discovery`'s `useSameLevelLine`, `useNewInRakietaLine` and
`useSameVibeLine`, and `rankings`' `useTopTenLine`. **Each hands its title, what it unfolds and its
footer, or `undefined` while its read is out, empty or failed**, so the shell knows from one call per
line whether to draw it, and **every line's read runs when Home opens**, open or not. With all five
hidden, FOR YOU is not drawn. The paragraphs above that say `HomeScreen` draws `HottestGroupsRow` and
`NewInRakietaRow` were true until this one.

- **A hook that hands back elements**, rather than a component per line, because the shell must know
  which lines are shown — to hide FOR YOU and to close a line that empties — and a component that
  draws `null` cannot say so without a second read of every row or a state copied up through an
  effect. The read, a people line's on-screen reporter and Top 10's pick are held at the line's level,
  which lives while Home does; what the line unfolds is drawn only while it is open.
- **Which line is open is `domain/forYou`** (pure, `forYou.test.ts`) **kept by `useOpenLine`**: a
  press on a closed line opens it; on the open line's header closes it; on another line folds the
  first and unfolds the second once `motion.lineFold` has run, and **whatever is pressed while a line
  folds waits for that fold** — so an unfold never runs beside one — all at once under Reduce motion.
  Which line Home starts on (`lineToStartOn`) and whether FOR YOU is drawn (`forYouShown`) are the
  domain's too. A line
  that stops being shown closes, and comes back closed. **Every line starts closed**, but **for a
  reader in no group Groups heating up opens by itself** once it is shown and until the reader
  presses anything — and stays open when a join from it makes them a member. **Home's own state,
  never a store**: Home is kept under every tab (`TAB_STACK`), so the open line outlives a tab switch
  and a screen pushed over Home, and goes with Home at a restart or a sign-out — never kept.
- **The page shows what opened** (`PageReveal`): `ShellScreen` provides it on a page that watches,
  scrolling just far enough that the unfolding line's foot stands at the page's — at once under
  Reduce motion — from the band it already follows for the on-screen reports. **Only a line the
  reader pressed open asks** (`pressed`, handed down as `reveals`): Groups heating up opening by
  itself for a groupless reader never scrolls Home under them.
- **Every line's content is memoised**: all five hooks run in `ForYou`, so a re-read of one line
  renders the others' frames again, and their cards only if their own data moved.
- **The groupless line** reads _Join a group to get games — see Groups heating up, just below._
  (`GROUPS_COPY.hottest.groupless`).

The walk is `forYou.test.tsx`; each line's own is its feature's suite. **Not seen on a device**: the
fold, the unfold, the switch, the lines sliding and the page easing down, against home refactor 3–13.

**FOR YOU's lines show their counts** ([#822](https://github.com/Raketa02/Raketa/issues/822);
ADR-0205 §5, §6; home refactor 3, 4, 7). A line's parts carry its `count`, and `ForYou` hands it to the
`FoldingLine` as it hands the title — the shell decides nothing about it: what a count counts is each
feature's read, the pill and its _99+_ are `shared/ui`'s. Four lines carry one, Top 10 none.
**Nothing new reads**: the count is on each line's own read, so it moves when that read does — a
return after 30 seconds, foregrounding, Home's pull, a push or a write that re-reads the row. Walked
in `forYou.test.tsx`'s _the counts_: each line's figure, the cap, no pill on Top 10, the pill kept
open, the spoken names, _See all N_ in the people lines' footers, and the pull and a return moving
the figure.

**Play's Explore goes behind the `explore` feature flag, off** ([#826](https://github.com/Raketa02/Raketa/issues/826),
[ADR-0206](../../../docs/adr/0206-a-feature-is-turned-on-by-a-pull-request-again-and-explore-is-the-first.md)
§11). `PlayScreen` asks `useFeatureOnMount('explore')` **once, when it mounts**, and draws one of
two components — the answer cannot change under either, so neither reads what the other reads.
**Off** — the code default, and every environment's value — is the Administrator's Groups tab
exactly: `TopSafeArea` + a pinned `ScreenHeader` titled **Groups** (`PLAY_COPY.title`; an h1, a
header to a listener, no eyebrow, no sub-line, nothing on the right) over `GroupsSection`,
unchanged, with **+ New** and **Join** where they are at the top of the list. No segment is drawn,
and Explore cannot be reached: the remembered segment is the only way in, so the off branch never
calls `usePlaySegment` — it **does not wait on the segment read and never writes it**, and a saved
`explore` stays on the phone, the player's own choice for the day the feature flag comes on. It is
not wrapped in `ShellScreen`, whose scroller would nest the list's. **On** is the paragraph above,
unchanged: the prominent segment, the remembered segment, Groups first. **Anything unknown is off**
— no datafile yet, offline, a host that never answers, a datafile refused for its `schemaVersion`
with none saved, no signed-in player — so the switcher is drawn only on an explicit on, and a
datafile that lands while Play is up changes nothing until Play next mounts: Explore never appears
under the player's thumb. The bottom tab stays **Play**. The walks are
`components/theExploreGate.test.tsx` (nothing served, served off, a saved `explore` read past and
still saved, served on with a saved Explore reopening, a datafile arriving while Play is up, an
unknown `schemaVersion` with and without a saved datafile, and one refused mid-session);
`playSegment.test.tsx`'s walks run with `explore` served on (`launchWithExplore`), and
`theShell.test.tsx` finds Play by its title. **Not seen on a device**: the title over the list, and
the switcher back through a locally served datafile.

**Home shimmers until it is built, then reveals together** ([#871](https://github.com/Raketa02/Raketa/issues/871);
PRD #867; the loading shimmer log §5, §6, Q11–Q16). Home was about ten reads drawn as each landed —
the envelope, the level card, _Your games · 0_ and its sentences, then FOR YOU's lines one by one.
**Now it has two parts, top-down** (`hooks/useHomeParts`), each waiting on its reads:

| Part                                    | Draws                                              | Waits for                                                                                                      |
| --------------------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **1 — your things**                     | the header's numbers, the level card, _Your games_ | Home's own read; the ratings, and your groups where the level card needs them; in-no-group; the bell's notices |
| **2 — FOR YOU**, all its lines together | the heading and whichever lines have content       | Groups heating up; the three people lines; Top 10, behind its opening sport                                    |

- **The skeleton**, while a part waits: _Your games_' heading bar and one game card's block at the
  rail's real card size (`proposals`' `YourGamesSkeleton`), and FOR YOU's heading bar and four closed
  lines at the line's real height (`ForYouSkeleton`) — **no level card and no envelope**, which are
  often absent. Both stand on one `SkeletonGround`, so one band crosses them; it draws itself again
  as it is laid out only while a shape stands, so once Home has revealed a line folding under it
  costs nothing. The heading bars are as wide as their words (`shared/ui`'s `SkeletonWords`, the words
  set unseen in the heading's role, _Your games_' with a one-figure count); the card's block is as
  tall as the rows every card draws, read off its drawing — the tags, three facts, the large button.
  Each part is a `Reveal` **sized by its skeleton** while it waits, since its content is nothing until
  its read lands.
- **The rule** is `shared/ui`'s `useRevealParts`: **before the ceiling, everything together** once both
  parts have finished, on one cross-fade; **at the ceiling, 2.5 s after Home mounts**, the finished
  parts from the top, stopping at the first that is not — never FOR YOU before your things — and then
  each in turn as it finishes. **A read has finished** once it has landed, been refused, paused for a
  connection, or **failed once and started retrying** (`shared/lib/query-client`'s `readHasFinished`),
  read off Query's cache by each feature's own `use…Finished` (the level card's and Top 10's rules
  over those reads are their features' `domain/`'s, `levelCardReadsFinished` and
  `topTenReadFinished`) — `proposals`' `useHomeReadFinished`,
  `groups`' `useLevelCardFinished`, `useInNoGroupFinished` and `useHottestGroupsFinished`,
  `notifications`' `useNoticesFinished`, `discovery`'s `useDiscoveryLinesFinished` and `rankings`'
  `useTopTenFinished` — each drawing `HomeScreen` again only as it turns, so a background re-read
  draws nothing new. **Photo bytes are never waited for.**
- **The header is drawn for real from the start** — the title, the bell, the trophy — and **its
  numbers wait for your things**: the envelope (`showsEnvelope`), the bell's badge (`NoticeBell`'s
  `showsCount`) and the trophy's place (`RankingTrophy`'s `showsPlace`) come with them, or, past the
  ceiling, each as it lands: they sit in the right-aligned slot and push nothing down. Held back, each
  is said nowhere — the bell's and the trophy's names are the bare ones.
- **When**: only if something is unread at the first draw — a Home whose reads are all cached is
  simply drawn, no skeleton and no fade — and **once per mount**: a part shown stays shown, and Home is
  kept, so a return to Home, a pull and a background re-read never shimmer.
- **The ground and each reveal pass on where they stand on the page** (`SectionOnPage`): FOR YOU's
  rows are measured through them, so the on-screen reports and the page showing an unfolding line
  are as they were.

Calls made here, for the user to check:

- **Top 10 does not hold FOR YOU behind a failing read** (`useTopTenFinished`): it cannot set out
  until its opening sport is known — Home's read and the ratings — so one of those failing and
  retrying counts Top 10 as finished too. Otherwise one failing read would hold FOR YOU through its
  whole backoff, which is what the retrying rule is for. Top 10's line then joins FOR YOU, at its
  foot, when it lands.
- **_Your games_ keeps its skeleton while its first read retries** (the code review's catch): Home
  stops waiting for it and reveals around it, and the rail comes in where its skeleton stood when it
  lands or is refused — never drawn in later above FOR YOU, pushing it down. **The level card and a
  FOR YOU line do not**: the card is often absent and draws no skeleton, so a ratings read that lands
  _rated in nothing_ while your groups retry draws it in at the top when they land; and a line whose
  read fails stays out of FOR YOU until it is read, as before.
- **Offline with nothing read, _Your games_ says so** under its heading, in the amber note, with no
  count — as a refusal says it in coral, now with no count either (`proposals`' record).

The walks are `homeReveal.test.tsx`: the skeleton with every read out (one card, four lines, the real
header), no _· 0_ before Home's read, FOR YOU landing first and nothing shown until your things do,
the bell's read and Home's failing once and counting as finished — Top 10 not waited for behind
Home's — from the ceiling your things while FOR YOU shimmers, never FOR YOU first while the header's
numbers come as they land, and no skeleton on a return or a pull. **The harness runs every pending
timer on a navigation, the launch's included, so the ceiling has passed by the time a walk looks, and
a held read is deaf to the client's timeout** (`test-support/transport`'s `deafToAborts`) — else it
would time out under the launch, which is a read failing once. **The sweep costs those suites
nothing**: a shape joins the ground's clock only once it is laid out, and the harness lays nothing
out — before that change Home's skeleton swept through every navigation's minutes of frames, and
through a suite's day-long clock jump, inside an `act` that could not unmount it until the jump
ended. **So the header's numbers held before the ceiling are walked by no suite**: the rule before the ceiling is `Reveal.test.tsx`'s, on the
hook. **Not seen on a device**: the shimmer over Home, the card's block against a real card, the two
fades, and a slow part coming in at the ceiling.

**Home's reads set out while the splash plays** ([#874](https://github.com/Raketa02/Raketa/issues/874);
PRD #867; ADR-0209 §2, amended 2026-11-24; the loading shimmer log §7, Q18). Since the tree mounts
only once the ball is still, Home's own reads set out about 0.2 s before the fade, and a cold open
often faded onto Home's skeleton. **Now a launch step, `hooks/warmHome`, sets them out as soon as the
session is restored**, and on a normal connection the splash fades onto a Home that is already whole:
every part finished at its first draw, so no skeleton and no fade (the rule above).

- **Started, never awaited**: the root layout starts it as it starts the install referrer's read, and
  the splash waits on no read — ADR-0209's fade rule is unchanged, and _ready_ still never means the
  data has arrived.
- **Every read the two parts wait on, under the very definitions their hooks observe** — keys,
  functions and options — so Home finds each fresh under the app's 30 s `staleTime` and sends none
  again. Each feature offers its Home read's prefetch on its public surface and the shell composes
  them: `proposals`' `prefetchHome`, `onboarding`'s `prefetchSkillRatings`, `groups`'
  `prefetchHomeGroups` (Groups heating up and your groups), `discovery`'s `prefetchPeopleLines`,
  `notifications`' `prefetchNotices` and `rankings`' `prefetchTopTen`. **Top 10's chain is included**:
  it sets out Home's read and the deck's two (the ratings and the sport last picked, `groups`'
  `prefetchDeckSport`), works out the opening sport off the cache by the hook's own rule
  (`openingSportIn` over `homeRankingIn` and `deckSportIn`, which ask `rankings`' `openingOf` and
  `groups`' `deckSport` in `domain/`, as the hooks do), waiting for the deck's reads only when
  the trophy names no sport, and then asks the row under the key the hook will look for.
- **Only for an account the entry gate will send to the tabs** — never for one headed for the
  naming, the profile steps, a club's area or _Start playing_. The gate's rule is callable outside its
  hook now, as a rule over the account (`onboarding`'s `entryDestinationOf`, which the gate asks too,
  so the two always agree), and the launch asks it of the account session restore cached
  (`entryDestinationAtLaunch`) — first reading the profile the phone remembers, under the gate's own
  definition, for an account that runs a club's groups (`decidedByTheLastProfile`), whose launch
  waits for it. No account cached — the check failed, was refused, or was never sent — is nothing to
  decide from, and nothing is warmed.
- **Never on a phone that already knows it is offline**, by the launch check's own rule (`auth`'s
  `phoneKnowsItIsOffline`, ADR-0209 §4).
- **Launch only**: after a sign-in Home mounts the moment the session opens, and nothing is warmed.
- **A call, for the user to check: the prefetches keep the hooks' retries** (the code review's
  question). A read still retrying when Home mounts is joined, not sent again; one that has spent
  every retry before Home mounts is asked again by Home's mount, as any failed read is, so a server
  failing all through the splash is asked about twice as often. Without retries, a Home joining a
  read still on its way would inherit none, and show a refusal on a single failure.
- **Not warmed**, because no part waits on them: the faces' photographs, the booking rooms the chat
  button asks after, and the phone's own lists — the games opened and removed, and the Rankings view
  the trophy's place is drawn in — which Home reads itself in milliseconds, under the splash.

The walks are `homeWarmUp.test.tsx`, through the harness's warmed launch (`test-support`'s
`launchWarmed`): the session restored as the launch restores it, then `warmHome` against the
harness's query client before the tree is rendered, its requests handed back as `early`. Home opens
with no skeleton and each of its nine reads sent once, all early; Top 10 on the deck's sport when the
trophy names none, the ratings held until Home's read has landed; an account that also runs a club's
groups and wore Player last is warmed; one headed for the naming, the profile steps, a club's area or
_Start playing_ — or that wore its club's profile last — sends none of Home's reads before its own
screen; and a phone known to be offline sends none early. That the step starts after the session and
is never awaited is `bootstrapApp.test.ts`'s. **Owed to the phone walk (#877)**: the A32's cold-start
trace — frames over 20 ms in the splash's first 2.6 s no more than the amendment's 3–5 — and a look
on a release build.
