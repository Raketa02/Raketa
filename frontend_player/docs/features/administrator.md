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
group** (`…/new-group`) and **a group's page** (`…/group/<id>`) pushed over Groups, and the group's
**Members** (`…/group/<id>/members`) over its page. **The club is in
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

**The Groups tab is _Groups_ over club 8–9's cards, with + New official group floating** (stories
122–124). The title alone: PRD #500 overrides club 8–9's name-and-chip header by name, the switcher
chip is the You tab's, and the _OGRODY 33 · ADMINISTRATOR_ eyebrow club 17 draws over it went at the
product owner's ask (#529) — the Groups · You bar under the screen already says whose area it is,
and the You tab keeps the eyebrow, where it names whose profile it is. **+ New official group floats
over the page's bottom corner**, at the gutter, in every state — Fill in's _+ Post a game_ precedent
(play 46), so the button stays put however long the list grows (#529; it was the first thing in the
list, pushed off by a scroll). Under it, the groups this Administrator runs at the club, newest
created first: the tile, the name with an
amber **_N waiting_** tag beside it — amber is _not yet answered_, and the tag carries the word — the
dots and _N members_, the home club, a chevron; the whole card is one element and opens the page.
Before the first group, **one dark card**: _No official groups yet_ and _Make one for each WhatsApp
group you run, then post its link there._ — the mock's card and the ticket's words, where 10.1's
empty state is one `tiny` line (design-system Part 16, #512's precedent). A failed read says why and
offers the retry where one can help, with the button still there to press. **A pull reads the list
again** (#529, the product owner's ask, 2026-10-02), drawn as the player's Groups list draws its
pull and with `groups`' own `usePull`: a request left or a player arrived on another phone is on the
cards when the spinner stops, where it had waited for a return to the app after the thirty-second
read went stale.

**New official group is five cards and a button, and the form is the screen's own state** (club 10
plus a Sports card; stories 125–126). _Name_ is New group's card with _Same name as the WhatsApp
group_; **the home club is the club, fixed**, a mint tag rather than a field; _Who can join_ is New
group's card **without** its _no sport to pick_ note, which is false of a group that declares its
sports; the **group size** — the domain's WhatsApp group size, labelled **_Group size_** since #529,
because the link goes out through any app and the form no longer names one — is **required** and
2–1024 — club 10 draws it _optional_, and PRD #500 overrides it by name — and says _A whole number
from 2 to 1024_ on the field the moment what is
typed is not one; **Sports** is a chip per sport **the club offers**, any number ticked, and sent in
the registry's order whatever order they were ticked in. The club's sports are the Groups tab's read
(`club.sports`), so the form offers exactly what may be declared. One Zod schema answers the group
(`newOfficialGroupFrom`, the player group's `GroupNameSchema` for the name), and **Create the group**
is pressable exactly when it does, busy while the create is in flight — two creates are two groups,
so it is never retried. Success seeds the page's read, **replaces** the form with the page and says
_Group created_; _back_ from a new group is the list. **A refusal is said on the field it names**
(`details.field`: `name`, `whatsapp_size`, `sports`) and forgotten the moment any field changes;
anything the form cannot name goes under the button.

**The page is the link card, the queue and the members card, and nothing to delete or leave**
(club 11, 18, 19; stories 126–130, 137). Headed by the group's name and a back arrow, and nothing
over it: club 11's _OGRODY 33 · OFFICIAL_ eyebrow went at the product owner's ask (#529,
2026-10-02), as the Groups tab's had, since every group in this area is the club's and official. **The
link card** (`ShareLinkCard`) is the link in mono cut in the middle, then **Share link** (volt) and
**Copy link** (`onDark`) of one width — with no _posted_ tag and no _Post again_, which PRD #500
overrides by name. **Want to join · N** is club 20's card, `groups`' `RequestRow`, only while
somebody waits. Then **the members card** (`MembersCard`): Info's members row's drawing — up to five
stacked faces, newest first, _+N_ for the rest of the member count, _N members_ and a chevron — with
**a ring of how much of the group has arrived** on the right, and **a tap opens Members**. There is
no door out of the group: running it is not membership, and only the club moves it (ADR-0183
§7–§8); its settings are the You tab's ([#517](https://github.com/Raketa02/Raketa/issues/517)). **A pull reads
the page again** (#529, 2026-10-02), as the Groups tab's does, so somebody who asked or arrived on
another phone is on it when the spinner stops, where they waited for a return to it.

**Share link hands the phone's share sheet the group's sentence** — _Join Ogrody 33 Club on Raketa:
<link>_, the group page's own — so the link goes out through whatever the Administrator's crowd
gathers in, a WhatsApp group among them (#529). It was club 11's _Post this in the WhatsApp group.
Everybody who taps it lands here._ over **Post to WhatsApp**, which opened WhatsApp by its scheme
(`whatsapp://send?text=`) and fell back to the sheet on a phone without it (story 128); the product
owner retired the line and the button together, since the group is no longer tied to one app. With no
caller left, the share port's `openWhatsApp` went too ([`_shared.md`](_shared.md)).

**The members card is the door to Members, and the ring is the share** (#529, the product owner's
ask). The card was one element that opened nothing, with club 11's line under the count — _you
approve joins · 6% of the WhatsApp group_ — and every player listed under it, newest first, with the
day they joined (_this week_, or _7 Sep_). **A tap now opens Members** — the member's own screen,
its rows, score tags and record sheet, the pill listing the group's declared sports
([`groups.md`](groups.md)) — so the Administrator sees who is in by sport and Level rather than by
date, and the list and its _this week_ rule went. **The ring** (`ArrivedRing`) replaced the line: an
empty circle whose stroke fills clockwise as players arrive, round the percentage it stands for —
the member count over the group size, `formatPercent`'s whole number. A `line2` track, a `mint` arc
from 12 o'clock with butt caps — the confidence ring's geometry on a light card, and the club
website's green bar for the same share — and the figure in `num.xs` inside. **The arc stops at full
and the figure does not**: the size limits nothing (ADR-0183 §3), so a crowd past it reads _117%_
round a closed ring. The card is spoken whole — _3 members, 6% of the group size_ — and the rule half
of the old line is the settings' to say. The faces are the five newest and _+N_ the rest **of the
group's count** (`playersStack`), so a player a block hides is counted all the same.

**The card says _members_, as Info's does** (#529, the product owner's ask, 2026-10-02). It said _N
players_, club 18–19's word, where a member opening the same group's Info reads _N members_ on
the same drawing — and the people in an official group are its members exactly as a player group's
are. The count is now `groups`' own `membersLine`, so the two cards cannot drift, and the card took
the name with it: `PlayersCard` is `MembersCard`, its faces `members-face-`. The read's `players`
and `playersStack` keep the wire's word.

**Members is read by whoever runs the group** ([#566](https://github.com/Raketa02/Raketa/issues/566),
`bf6822ac`). The members read (`GET /groups/{id}/members`) and the record route admitted a group's
members only, so an Administrator who had not joined as a player — Marta Wójcik, administrator-only,
on _Ogrody 33 Club_ — met a refusal; the backend now admits the account running an official group to
both, read live, so a removal or a handover takes it on the next read. **A refused list says so in
this area's words** — _This isn't a group you run any more._ — where it had fallen through to the
recovery's _Something went wrong at our end_: with the runner admitted, a refusal means the group was
handed on or the Administrator removed, which is what the sentence says.

**An answer takes its row at once, as an Owner's does** (`useAnswerAsAdministrator`, #514's
`useAnswerRequest` for the Administrator's routes). **✕** and **Approve** each end the request
whatever the server then does, so the row leaves on the tap and comes back — that row alone, where it
stood — only if the tap is refused, with a toast. The group is re-read once the last answer in flight
has landed, which is what puts an approved player's face first on the members card; the Groups tab is
re-read with it, since _N waiting_ and _N members_ have moved. The queue rides on the group's own
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

**The name stands alone, and _Sign out_ is pinned** (#529, the product owner's asks, 2026-10-02).
Club 8's _OGRODY 33 · ADMINISTRATOR_ over the name went, as the Groups tab's had: the switcher chip
beside the name and the area's own bar say whose profile it is, and `administratorEyebrow` and the
copy's `role` went with it. _Sign out_ left the end of the scroll for a foot pinned under it — the
player shell's `action` slot's measures — so it is in one place however many groups are listed over
it; the player's You tab pins it the same way ([`shell.md`](shell.md)).

**A group's settings are New official group's four cards over Edit group's _Save_** (story 131;
`GroupSettingsScreen`, pushed over You at `…/you/settings/<group>`, so the You column stays lit and a
press on You lays the tab's root down). No mock draws it. The **name** (_Same name as the WhatsApp
group_), **who can join**, the **group size** (2–1024, the rule said on the field the moment
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

**Switching to Anyone is asked first, as an Owner is asked** (#529, the product owner's ask,
2026-10-02): a save that turns _People I approve_ into _Anyone_ opens `groups`' own sheet
(`OpenToAnyoneSheet`, lent from its `types.ts`, the one Edit group opens) — _Let anyone join?_ and
_Selecting Anyone allows anyone to join the group, including players with pending requests._ — and only
its _Save_ sends the form; _Keep People I approve_ keeps it as it is, unsaved. Any other save goes at
once.

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
its tile (`GroupMonogram`), its dots, the group forms' two cards, the request row, a failed read, the
row face and the shared words (_N members_, _Want to join · N_, the share sentence, the link as drawn)
and the stacked faces (`FaceStack`) are `groups`' own, exported from its `types.ts` for this caller
([`groups.md`](groups.md)). The answer hook stays this feature's: it writes the group's own read, not
a queue of its own, and answers through the Administrator's routes — #514's handover asked for exactly
that. The
dependency points one way: `administrator` reads `groups`, never the reverse. Cross-feature values are
read inside functions and components, never at module load, because the feature barrels form a cycle.

**Calls made without the product owner, open for a ruling.** The Groups tab draws **`users`** on the
bar, the glyph Players draws on the player's; the two bars are never on screen together. The empty
state is **the mocks' dark card**, not 10.1's line. **Create the group** is New group's coral `xl`, where
club 10 draws it dark. The Sports card's line — _The sports Ogrody 33 offers. Players see this group's
games in them._ — was no mock's, and went at the product owner's ask (#529, 2026-10-02), from New
official group and the settings both, since they draw one card. The removal is **a toast over the sign-in screen**, not a sheet to
acknowledge. Names are whole, as everywhere since #505.

**#517's calls, open for a ruling** — no mock draws any of its screens. **The You tab's header was club
8's**, the name under _OGRODY 33 · ADMINISTRATOR_, until #529 took the eyebrow off (above). **A group's row says its sports**, the
one setting the Groups tab's read carries, with the `sliders` glyph, under a group titled _Group
settings_; _Start playing_ sits under _Playing_ with `play-circle` and the line _Get a Skill rating,
then find people to play with_. **Start playing is shown while the account does not act as a player**
(`actsAsPlayer`, the switcher's sense of the word), not while it has no committed Player profile — an
account that attested and left the setup half done is sent back into it by the gate. **The settings
screen is titled _Group settings_**, not the group's name, and draws no home club. **The attestation
step is pushed inside the area**, so the Groups · You bar stays under it. The sub-lines on the
attestation and on the nickname-only naming are new words. The attestation's next-steps line under the
box (_Next, a nickname, then a few questions to find your level._) was taken off at the #529 QA walk's ask.

**An administrator-only account the club removed** holds no profile at all; since #517 the gate sends
it to _Start playing_'s Adult attestation on its next launch or sign-in (ADR-0185 §3), with no way back
to an area it no longer has — and, because a person who does not want to play must not be stuck
there, **_Sign out_ under _Continue_** ([`auth.md`](auth.md)).

**Left open.** Offline, the area reads what is cached and the create and the
answers pause and resume, as the player's do — and the settings save with them; nothing says so beside
them yet. **Nothing here has been seen on a device** — the bar's two columns, the card's tag beside a
long name, the two equal doors on the link card, the You tab's header and rows, the settings form
with the keyboard up, and the attestation step over the bar are asked for a look; so are #529's
floating _+ New official group_ over a long list and the members card's ring at _117%_.

**The invitation sheet offers an account that already exists a club's administrator profile, on
launch** ([#518](https://github.com/Raketa02/Raketa/issues/518), PRD #500 stories 117–119, club 5–6;
`InvitationSheet`). It is offered **whenever the signed-in account's own read lists an invitation this
launch has not set aside** — `/users/me` carries the ones addressed to its email, and the server stops
listing one once it is accepted, removed or past its 72 hours, so _it stops appearing once the invitation
expires_ is the read's, never the phone's clock. It is mounted **over each profile's home** — by
`(app)/_layout` over the player's app, and by the area over its own screens, so another club's invitation
reaches an administrator who does not play — and **never inside onboarding**: an invitation waits until
the account is in. Club 5 is drawn with `BottomSheet`'s new **`mark` head**: the club's tile over _Ogrody
33 wants to make you an administrator_, centred, then what accepting does — _next to your player
profile_, or _next to Bonarka Arena_ for an account that does not play — and **Accept** (`dark`) over
**Not now** (`secondary`). **Accept adds the profile and the same sheet becomes club 6's profile
list**, Player ticked: one modal changing its content, never a second presented as the first leaves. A
row there switches at once; the close keeps what is worn. **Accepting is not switching**: the sheet keeps
the worn profile as the remembered one, so no choice left on the phone from an earlier time the account
held that club can move it. **_Not now_ — and the close, _Decide later_ — set it aside until the next
launch** (`useInvitationsSetAside`, memory only, `onboarding`'s set-aside runs' shape): the next launch
offers it again. An invitation that ran out while the sheet was up is said — _This invitation has
expired. Ask Ogrody 33 to send a new one._ — with nothing left to accept and _OK_ to close; a failure to
reach the server keeps Accept to press again.

**The handover sheet tells an administrator a club handed them a group** (#529 N5–N7, the product
owner's ask, 2026-10-04; [ADR-0192](../../../docs/adr/0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md);
`HandoverSheet`). `/users/me` now lists **`handovers`**: every group a club handed this account's active
administratorship that it has not been told about, oldest first, recorded on the group (`handover_seen`)
so every phone agrees. The sheet is mounted where the invitation sheet is, and **waits while an
invitation is on offer**, because that one asks and this one only tells. **One club at a time, with
every group that club handed** (`nextHandoverNotice`): _Ogrody 33 made you the administrator of Ogrody 33
Club_ under the club's tile, what running it means now, and the queue it came with (_2 people are waiting
for your answer._). Several at once are one sheet: _… of 2 groups_, their names in the body. **Nothing is
asked, so nothing can be declined**: **Open the group** (`dark`) goes to its page, or **See your groups**
to the Groups tab for several, switching to that club's profile first if the person wears another. **Got
it** (`secondary`) and the close, **Dismiss**, stay where the person is. **Every way out says it was
seen** (`useNoteHandoversSeen`, `POST …/handovers/seen`): the groups leave the cached account at once, and
the write is retried because the route steps over anything it has already applied. If it never lands,
this launch has still closed them (`useHandoversClosed`, memory only), and the next launch tells them
again. **It appears without the app going to the background**: `useFollowedAccount` re-reads `/users/me`
every 30 s in the foreground, **only while the account administers a club**. So a handover, an invitation
or a removal reaches an administrator within half a minute on whatever screen they are on, and a player
who runs nothing costs the server nothing while the app sits open. It is not instant: no push channel
exists on this branch. When the sheet appears, that club's Groups tab is re-read, so the handed group's
card is there.

**The profile switcher is a chip on each You tab and a sheet of profiles** (#518, stories 134–135 and
138, club 6–7; `ProfileChip`, `ProfileRows`). The chip sits in the header's right slot on the player's
You tab and on this area's — ADR-0185 §3 amends ADR-0179 §1's locked header by exactly this element —
and holds the worn profile's face beside a drawn ⇅: the player's own photograph or poster
(`player_record`'s `useOwnFace`, read only where Player is drawn), or **the club's tile** (`ClubTile`,
7.20's drawing on `night` with two letters taken from the name, since a club is served neither). The
tile is `groups`' since #529, lent from its `types.ts`, because Members draws it too, beside whoever
runs an official group ([`groups.md`](groups.md)).
**The chip is slim** (the product owner's mock, 2026-10-01): a 22 face (`monogram.chip`) about three
quarters of a 30 pill, the ⇅ in a 14 box about two fifths of the face, `hit.chip` lifting the target
past 44 — it had drawn a 28 face in a 36 pill, which read as a second avatar rather than a control.
**It is not drawn for an account with one profile** (`switcherShown`). The sheet lists Player first,
when the account plays, then one administrator profile per club in the server's order
(`profileOptions`), the worn one ticked and `selected`. **A row switches at once and costs nothing on
the wire** (`useSwitchProfile`, beside the area's other moves in `areaNavigation`): the phone keeps the
choice — the cache first, so the gate agrees in the next instant — and the app goes to that profile's
home, `/` for Player, where the gate lays the player's app down, or the club's Groups tab. Switching is
client state because the administrator's authority is never in the token (ADR-0185 §6). **The phone
remembers it** ([`onboarding.md`](onboarding.md), [`auth.md`](auth.md)), so the app reopens in the
profile worn last, and opens in Player when nothing was chosen or the club it remembers has let the
account go.

**A removal is a switch now, and kept as one** (#518). `useLeaveOnRemoval` moves an account that also
plays, or runs another club, through `useSwitchProfile`: the remembered profile was the removed club's,
and a gate reading it before the profile read caught up — or at the next launch — would have opened that
area again. So a removed administrator who plays is told, lands in Player, and reopens there.

**#518's calls, open for a ruling.** The switcher sheet is titled **_Your profiles_** with the close
**_Keep this profile_**; club 6 draws neither, and a real modal needs a heading for focus. Names are
**whole** — _Tomek Kowal_ where club 6 draws _Tomek K._ — as everywhere since #505. **No initials over
the face** in the chip, where club 7 draws _TK_ (#513's call, ADR-0167 §3). **A club's letters are the
app's own cut** (_O3_ from _Ogrody 33_), since clubs serve no monogram. **Switching lands on the
profile's home**, not on its You tab where the chip was pressed. The invitation's body for an account
that does not play, and the sheet's close _Decide later_ and _OK_ once the invitation is gone, are new
words. **Not seen on a device**: the chip in both headers, the ⇅ at 16pt, the sheet's two states, and
the club tile on `night`.

**A link answered over the area, too** (#520). The area's route layout mounts `links`' `IncomingLinks`
beside the area — composed there because `links` reads this feature (`useSwitchProfile`,
`useOfferInvitationsAgain`) and the area may not read it back. **An invitation's link opened by the
account it was sent to has the invitation sheet offer that club's invitation again** even if _Not now_
set it aside this launch — that club's only, the set-aside store's `takeBack` — and the app's bare
address, the existing-account email's button, takes back all of them; `/users/me` is re-read either way
(`useOfferInvitationsAgain`); **a group link switches an account that
plays to Player**, where Join a group is, and waits for one that does not. The rest is
[`links.md`](links.md)'s.
