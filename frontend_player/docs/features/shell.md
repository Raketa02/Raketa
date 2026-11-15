# shell — three tabs over one stack

> The design record for `src/features/shell/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**The shell is three tabs over one stack, and it remembers nothing.** `TabShell` mounts the
`TabBar` once, below the navigator, and reads the active column off the current path —
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
down. **No sentence the shell writes says "nothing is happening"** — it began as Now's refusal,
because Now is where a game lands and asserting emptiness would be a lie one tap after one did, and
it governs every empty state the shell writes. `shellCopy.test.ts` holds that refusal, and it
**moved with the copy** rather than being deleted when the placeholder it was written for died.
The bar's **transitions** follow the two moves: `none` by default, because a replace that slid in
from the right would read as going deeper on the gesture whose meaning is that nothing was kept,
and the push kept for the screens pushed over a tab, which genuinely are ones.

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

**NEW IN RAKETA follows HOTTEST GROUPS, and See all is pushed over Home**
([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows screens §1, §5). `HomeScreen`
draws `discovery`'s `NewInRaketaRow` after `HottestGroupsRow` — Same competitive level (#802) will
stand between them — and the pull re-reads it (`rereadDiscovery`). **The shell hands it nothing
else**: accepting a request on FRIEND REQUESTS turns that person's envelope to ✓ on the row because the
row's reads list people (`LISTS_PEOPLE`) and every friend write re-reads those. See all is
`/new-in-raketa`, in `PUSHED_SCREENS` and `INSIDE_A_TAB` (Home stays lit). The record is
[`discovery.md`](discovery.md).

**Home says what of it is on screen** ([#804](https://github.com/Raketa02/Raketa/issues/804); the
Home rows mechanics §9.2). `HomeScreen` turns on `ShellScreen`'s **`watchesOnScreen`** — forwarded,
not designed, and off on every other shell screen, whose scroller says nothing of where it is. With
it on, the page's scroller hands its rows `shared/ui`'s `PageOnScreen` (`useWatchedPage`): how far
it is scrolled and how tall it shows, sampled ten times a second and read again where a drag or a
fling comes to rest — and **nothing while Home is not the screen in view**, a screen pushed over it,
another tab, the app in the background (`useFocusEffect` and `useAppInBackground` in a child, so a
shell screen drawn outside a navigator never asks; coming back says the band again). Nothing drawn
changes, and nothing re-renders as the page moves: the band is followed, not state. What a row does
with it is `discovery`'s.
