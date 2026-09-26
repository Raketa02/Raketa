# administrator — the administrator area: Groups · You, New official group, an official group's page, its settings and Start playing

> The design record for `src/features/administrator/` — what the feature does and the reasons the
> shape is what it is, one paragraph per decision. **Append here** when a ticket changes what this
> feature does. Index: [`README.md`](README.md).

**The administrator is a second profile inside this app, and its area is its own group of screens**
([#516](https://github.com/Raketa02/Raketa/issues/516), PRD
[#500](https://github.com/Raketa02/Raketa/issues/500) stories 122–137, ADR-0184, ADR-0185). An
account a club named as its **Administrator** runs that club's **Official groups** from here: it
makes one per WhatsApp group the club keeps and posts its link there. The area is
`src/app/(administrator)/`, a **sibling of `(app)`** for onboarding's reason — the entry gate
redirects into it, so it cannot sit behind the gate — with its own session guard, and one area per
club at `/administrator/<club>`: the Groups tab at the root, **You** at `…/you`, and **New official
group** (`…/new-group`) and **a group's page** (`…/group/<id>`) pushed over Groups. **The club is in
the path** because every screen is one Administrator's at one club, and a person running two clubs'
groups is two Administrators (ADR-0184 §1). The words are club 8–11 and 17–20's, with _Rakieta_
read as Raketa, in `components/administratorCopy.ts` and `administratorPresentation.ts`; the mocks
live in [`docs/specs/play-groups/`](../../../docs/specs/play-groups/README.md).

**The gate sends an account that only administers straight to its area, and never into
onboarding** (ADR-0185 §3). `GET /users/me` now answers the account's **profiles** — whether it acts
as a player, and each club it administers — and `auth` carries them on the signed-in player
([`auth.md`](auth.md)). The gate reads them **first**, ahead of the naming
([`onboarding.md`](onboarding.md)): an account that does not act as a player and administers a club
has not asked to play, so its name without a nickname, its ratings and its runs are no questions it
owes an answer to. The gate answers from the player read alone and never waits on the two player
reads, and once the player read says so they are not asked at all. **The area opens on the first
club the server lists**; which club a person running two opens on, and the last-used profile of an
account that holds both, are the switcher's ([#518](https://github.com/Raketa02/Raketa/issues/518)).
An account that also plays opens in Player, as ADR-0185 §3 defaults, and never reaches the area in
this ticket.

**The area's door is the account's profiles, and its lock is the server's** (`useAreaAccess`). An area
for a club this account does not administer — a stale link, a removal already read — draws nothing
and hands the person to `/`, where the gate decides. The club's name every header says comes from
the same read, so no header waits on a request of its own. Every administrator route asks again
whether the account still runs the club.

**One stack and one bar, the player shell's arrangement a second time** (`AdministratorArea`,
`areaNavigation`). The bar is mounted once below the navigator, so it owns the bottom inset and
never slides in with a screen; **a tab press lays that tab's root down**, so Groups from a group's
page lands on the list and never on the page, and pressing the tab already at its root does nothing.
The lit column is read off the path. The bar is `shared/ui`'s `AdministratorTabBar` — **Groups ·
You**, club 17, a second fixed inventory beside the player's five ([`_shared.md`](_shared.md),
design-system Part 16).

**The Groups tab is club 17's header over club 8–9's button and card** (stories 122–124).
_OGRODY 33 · ADMINISTRATOR_ over _Groups_ — PRD #500 overrides club 8–9's name-and-chip header by
name, and the switcher chip is the You tab's. **+ New official group** first, in every state, then
the groups this Administrator runs at the club, newest created first: the tile, the name with an
amber **_N waiting_** tag beside it — amber is _not yet answered_, and the tag carries the word — the
dots and _N members_, the home club, a chevron; the whole card is one element and opens the page.
Before the first group, **one dark card**: _No official groups yet_ and _Make one for each WhatsApp
group you run, then post its link there._ — the mock's card and the ticket's words, where 10.1's
empty state is one `tiny` line (design-system Part 16, #512's precedent). A failed read says why and
offers the retry where one can help, under the button that still works.

**New official group is five cards and a button, and the form is the screen's own state** (club 10
plus a Sports card; stories 125–126). _Name_ is New group's card with _Same name as the WhatsApp
group_; **the home club is the club, fixed**, a mint tag rather than a field; _Who can join_ is New
group's card **without** its _no sport to pick_ note, which is false of a group that declares its
sports; the **WhatsApp group size** is **required** and 2–1024 — club 10 draws it _optional_, and PRD
#500 overrides it by name — and says _A whole number from 2 to 1024_ on the field the moment what is
typed is not one; **Sports** is a chip per sport **the club offers**, any number ticked, and sent in
the registry's order whatever order they were ticked in. The club's sports are the Groups tab's read
(`club.sports`), so the form offers exactly what may be declared. One Zod schema answers the group
(`newOfficialGroupFrom`, the player group's `GroupNameSchema` for the name), and **Create the group**
is pressable exactly when it does, busy while the create is in flight — two creates are two groups,
so it is never retried. Success seeds the page's read, **replaces** the form with the page and says
_Group created_; _back_ from a new group is the list. **A refusal is said on the field it names**
(`details.field`: `name`, `whatsapp_size`, `sports`) and forgotten the moment any field changes;
anything the form cannot name goes under the button.

**The page is the link card, the queue and the players, and nothing to delete or leave** (club 11, 18,
19; stories 126–130, 137). Headed _OGRODY 33 · OFFICIAL_ over the group's name. **The link card is
club 11's, always** — _Post this in the WhatsApp group. Everybody who taps it lands here._, the link in
mono cut in the middle, **Post to WhatsApp** (volt) and **Copy link** (`onDark`) of one width — with
no _posted_ tag and no _Post again_, which PRD #500 overrides by name. **Want to join · N** is club
20's card, `groups`' `RequestRow`, only while somebody waits. Then **the players card** — up to five
stacked faces, newest first, _+N_ for the rest of the member count, _N players_, and club 11's line
under it: who gets in (_anyone with the link joins_, _you approve joins_) and **how much of the
WhatsApp group has arrived**, which passes 100% when it has — and **the list**, every player newest
first with the day they joined: _this week_ within seven days, otherwise _7 Sep_, in mono. Rows open
nothing and nobody can be removed. There is no door out of the group: running it is not membership,
and only the club moves it (ADR-0183 §7–§8); its settings are the You tab's
([#517](https://github.com/Raketa02/Raketa/issues/517)).

**Post to WhatsApp opens WhatsApp with the sentence typed, and the share sheet on a phone without
it** (story 128). The sentence is the group page's share sentence — _Join Ogrody 33 Club on Raketa:
<link>_ — and the share port gained the verb that opens it (`openWhatsApp`, `whatsapp://send?text=`),
which answers whether WhatsApp took it. **The fallback is this feature's, not the port's**
(`PostLinkCard`): a `false` opens the sheet with the same sentence, so the tap never dead-ends, and a
suite watches the decision with WhatsApp and the sheet both faked at the platform edge. No native
setting was needed and no new build: `openURL` needs neither `LSApplicationQueriesSchemes` nor
Android's `<queries>`, which only `canOpenURL` reads.

**_This week_ is rolling, and judged against the read** (`domain/officialGroupRules.ts`). Seven times
twenty-four hours back from when the group was read (the query's `dataUpdatedAt`), as the club
website's _this week_ is (#523), so the two surfaces never disagree about one player; a moment the
phone's clock has not reached yet is _this week_. **The date is the day in the platform's zone**
(`platformDay`), never the phone's. The phone's clock decides only which of two labels a row wears —
the contract serves no read instant to judge it by — and never anything anybody can act on. The share
of the WhatsApp group is the member count over the size, `formatPercent`'s whole number. The card's
faces are the five newest and _+N_ the rest **of the group's count** (`playersStack`), so a player a
block hides is counted all the same.

**An answer takes its row at once, as an Owner's does** (`useAnswerAsAdministrator`, #514's
`useAnswerRequest` for the Administrator's routes). **✕** and **Approve** each end the request
whatever the server then does, so the row leaves on the tap and comes back — that row alone, where it
stood — only if the tap is refused, with a toast. The group is re-read once the last answer in flight
has landed, which is what puts an approved player at the top of the list, _this week_; the Groups tab
is re-read with it, since _N waiting_ and _N members_ have moved. The queue rides on the group's own
read (`requests`), so there is no second request and nothing draws before the page does.

**Removed while here: the area hears it two ways and answers it once** (story 136, ADR-0184 §7).
**A refused request** — every administrator route answers a removed Administrator
`403 not_an_administrator`, so `useRemovalWatch` listens to **every query and mutation under this
feature's keys**, not to one of them: a cache subscription, because queries have no `onError` here
and a rule restated on each hook is the one the next hook forgets. **Or the profile read** — `/users/me`,
re-read on focus, no longer lists the club; the You tab asks no administrator route, so there this is
the only way it is heard. The area remembers the club it opened on, so a read without it is a removal,
**never a fall-through to `/`**, which would take an account with nothing left through the gate into the
player's setup unannounced. Where it goes is a pure rule (`afterRemoval`, the profiles **without the
club that removed it**, since the read may not have caught up): an account with nothing left is **told
and signed out** — a `base` toast, _Ogrody 33 removed you as an administrator. You're signed out._,
raised before the sign-out so it is read over the sign-in screen, through `auth`'s own `useSignOut`,
now public for this caller; one that also plays is told and moved to its player side, and one that
runs another club's groups to that club's area — the switcher's moves
([#518](https://github.com/Raketa02/Raketa/issues/518)), drawn here so a player is never signed out
for losing a hat. A refused answer adds no toast of its own, and signing out on purpose is not a
removal.

**The You tab is the account's: its name, each group's settings, _Start playing_ and the way out**
([#517](https://github.com/Raketa02/Raketa/issues/517), stories 131–133; `AdministratorYouScreen`). No
mock draws it, so it is the player You tab's arrangement (ADR-0179 §1) with the administrator's rows:
**club 8's header** — _OGRODY 33 · ADMINISTRATOR_ over the account's name — which PRD #500 took off the
Groups tab and which belongs on the tab about the account; then **GROUP SETTINGS**, one door row per
official group she runs, in the Groups tab's order, each saying its sports, and none before the first
group, since a card of settings for nothing is nothing; then **PLAYING** with _Start playing_, only
while the account does not act as a player; then _Sign out_ (`AccountPanel`), which an account that only
administers has on no other screen. The rows ride on the Groups tab's read, whose card carries the
sports and nothing else of the settings, so the tab asks nothing of its own; a failed read says why
under the group title. #518 puts the switcher chip in the header.

**A group's settings are New official group's four cards over Edit group's _Save_** (story 131;
`GroupSettingsScreen`, pushed over You at `…/you/settings/<group>`, so the You column stays lit and a
press on You lays the tab's root down). No mock draws it. The **name** (_Same name as the WhatsApp
group_), **who can join**, the **WhatsApp group size** (2–1024, the rule said on the field the moment
what is typed is not one) and the **sports**, one chip per sport the club offers — the group's own read
serves the club's sports, so the form offers exactly what may be declared. The home club and the link
are not there: neither ever changes. The form is **one schema with New official group's**
(`officialGroupSettingsFrom`; the shape is `OfficialGroupSettings`, create and save alike), and the size
and sports cards are **one drawing with it** (`OfficialGroupFormCards`). **Save is Edit group's**:
_Save_ while the form makes settings that differ from the group's, **_Saved_, settled, while they are
the group's** (`settingsUnchanged`, the four fields with the sports in registry order) — so a save that
would record nothing is never a round trip — busy in flight, never retried, and the screen stays; the
name field takes the name as the server recorded it. The answer is written under the page's key, and
the Groups tab is re-read, since a card's name, sports and counts may have moved.

**Switching to Anyone shows who it admitted** (`PUT …/settings` answers `admitted`): everybody waiting
is in at once, and `groups`' _LET IN · N_ card (`AdmittedCard`, Edit group's) says who, in the order
they asked, under the button until the next save. **A refusal is said on the field it names** —
`name`, `whatsapp_size`, `sports` — and forgotten the moment any field changes; `group_not_found` and
anything else no field owns goes under the button. A removed Administrator's save is refused
`not_an_administrator` like every other administrator route, and the removal watch answers it — the
save is keyed under this feature (`administratorKeys.settings`), and the form says nothing of its own.

**_Start playing_ makes this account a player too, in the gate's three steps** (story 133, ADR-0185
§4). The row pushes **the Adult attestation** — `auth`'s `StartPlayingScreen` ([`auth.md`](auth.md)) —
**inside the area**, at `…/you/start-playing`, so _back_ is the You tab: the root is a `Slot`, and a
push out of the area unmounts it and loses the stack under it, so a back from outside landed on
Groups. Once attested the screen hands the rest to the entry gate: the account acts as a player, is
not named in full, and goes to **the naming, which asks only for the nickname** because the club gave
the name; then welcome, the questionnaire and the social steps, as for anybody
([`onboarding.md`](onboarding.md)). Afterwards the account holds both profiles: it opens in Player, as
ADR-0185 §3 defaults, the area still opens for it, and its You tab no longer offers _Start playing_.
Reaching the area again from the player side is the switcher's
([#518](https://github.com/Raketa02/Raketa/issues/518)).

**What `groups` lends, and why it is lent rather than drawn again.** An official group is a Group, so
its tile (`GroupMonogram`), its dots, New group's two form cards, the request row, a failed read, the
row face and the shared words (_N members_, _Want to join · N_, the share sentence, the link as drawn)
and the stacked faces (`FaceStack`) are `groups`' own, exported from its `types.ts` for this caller
([`groups.md`](groups.md)). The answer hook stays this feature's: it writes the group's own read, not
a queue of its own, and answers through the Administrator's routes — #514's handover asked for exactly
that. The
dependency points one way: `administrator` reads `groups`, never the reverse. Cross-feature values are
read inside functions and components, never at module load, because the feature barrels form a cycle.

**Calls made without the product owner, open for a ruling.** The Groups tab draws **`users`** on the
bar, the glyph Players draws on the player's; the two bars are never on screen together. The empty
state is **the mocks' dark card**, not 10.1's line. **The players card carries club 11's line in every
state**, where club 18–19 draw the count alone. **Create the group** is New group's coral `xl`, where
club 10 draws it dark. The Sports card's line — _The sports Ogrody 33 offers. Players see this group's
games in them._ — is no mock's. The removal is **a toast over the sign-in screen**, not a sheet to
acknowledge. Names are whole, as everywhere since #505.

**#517's calls, open for a ruling** — no mock draws any of its screens. **The You tab's header is club
8's**, the name under _OGRODY 33 · ADMINISTRATOR_, where the story says the role line sits _under_ the
name; the ticket calls it the eyebrow, and an eyebrow sits above. **A group's row says its sports**, the
one setting the Groups tab's read carries, with the `sliders` glyph, under a group titled _Group
settings_; _Start playing_ sits under _Playing_ with `play-circle` and the line _Get a Skill rating,
then find people to play with_. **Start playing is shown while the account does not act as a player**
(`actsAsPlayer`, the switcher's sense of the word), not while it has no committed Player profile — an
account that attested and left the setup half done is sent back into it by the gate. **The settings
screen is titled _Group settings_**, not the group's name, and draws no home club. **The attestation
step is pushed inside the area**, so the Groups · You bar stays under it. The sub-lines on the
attestation and on the nickname-only naming, and the attestation's next-steps line, are new words.

**An administrator-only account the club removed** holds no profile at all; since #517 the gate sends
it to _Start playing_'s Adult attestation on its next launch or sign-in (ADR-0185 §3), with no way back
to an area it no longer has — and, because a person who does not want to play must not be stuck
there, **_Sign out_ under _Continue_** ([`auth.md`](auth.md)).

**Left open.** Offline, the area reads what is cached and the create and the
answers pause and resume, as the player's do — and the settings save with them; nothing says so beside
them yet. **Nothing here has been seen on a device** — the bar's two columns, the card's tag beside a
long name, the two equal doors on the link card, WhatsApp opening on both platforms, the You tab's
header and rows, the settings form with the keyboard up, and the attestation step over the bar are
asked for a look.
