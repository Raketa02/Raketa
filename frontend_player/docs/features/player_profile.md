# player_profile — the second part of onboarding and the Profile surface

> The design record for `src/features/player_profile/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**A flagged photo is warned about and never taken away**
([ADR-0133](../../../docs/adr/0133-the-verdict-crosses-on-the-upload-and-the-warning-may-be-wrong.md)).
Every upload is scored server-side against _shows a racket sport on a court_, and the answer
comes back on the upload response as a code — `allowed` or `flagged`, never a sentence, and
never the evidence it was taken from. The step is what writes the sentence, in
`photoStepPresentation`. **The check is wrong about some unknown share of what it flags**, so
the copy reports _we could not see a court_ rather than accusing anybody, says nobody has
looked because nothing reviews a flagged photo a second time, says nothing is blocked because
the photo is stored and committed like any other, and offers keeping it before swapping it.
The photo keeps its place, keeps the lead if it had it, is in `photo_ids`, and `Continue` is
not touched. The step does **not** announce the check up front: that is small print to the
majority whose photo is fine and reads as a threat to the rest. `null` on the wire means _this
response said nothing_, which is not `allowed` — the mapper carries it as **no verdict**
(`UploadedPhoto.review` absent, since #471; it folded to `allowed` before the You tab needed
the difference), and a verdict this build has no words for is carried the same way: the step
warns about neither, and the tab's row says _on court_ of neither.

**The gender step says what narrowing costs, at the moment of the press.** The preference
is a **mutual** gate: setting _Women only_ does not only filter what a player sees, it hides
them from every man — including men who searched for anybody. That half is the one nobody
would guess, and **learning it from an empty inbox is not acceptable**, so the note is
rendered the instant a narrowing option is chosen and goes away when it is widened again.
The rule that decides whether there is a cost is `gender.reachOf`; the sentence is
`genderPresentation`'s. The answer about the player is **required and never pre-selected** —
_Prefer not to say_ is a choice somebody makes, not a default given on their behalf — while
the preference beside it opens at _Anyone_, which is the value every profile already
carries. **Neither value ever reaches anybody else** (ADR-0096 §6): no response that describes
one player to another carries either. The one shape that does is the owner's own profile read
(ADR-0179 §4, since #472), so the You tab's _Who you play with_ can open on the answer already
given — the second surface either value is seen on, and both to its owner only.

**The commit is the one mutation in this app a retry may repeat.** Its **commit key** is
minted when the part is entered and lives exactly as long as the draft, so a double tap and a
retry after a failure both carry the key the first attempt carried — the disabled control is
the courtesy, the key is the defence. `Idempotency-Key` is set by `shared/lib/http` for any
request that names one, including the replay a 401 rotation makes. A failed commit keeps the
draft, keeps the player on the step, offers the control that failed as the retry, and claims
nothing. `commitStanding` and `mayFinish` own when the finish opens — a rule, not a
`disabled={…}` expression — and `readyToCommit` under them is what makes a partial commit
unrepresentable. Three things hold the finish shut. **No Location area**: location is a core
requirement for discovery, `CommitPlayerProfileRequest` requires it, and the last step asks
once more with the way back one press away rather than trapping a player on step five behind
an OS prompt. **A blank week**: the week has a floor of one hour since
ADR-0102, so silence about when somebody plays is asked for rather than scored as a zero —
step four already refuses to continue on one, and this is the same rule read at the end.
**A photo still going up**: uploads outlive the step that started them, and the
body names photos by the ids the server gave back, so committing mid-upload would silently
drop a picture the player watched arrive. That one asks for nothing and opens itself.

A failed commit whose `code` names an answer — `weekly_hours_empty` today — is drawn as
that answer rather than as _try again_, with the control back to the step that takes it: the
commit re-validates every rule a picker enforced, and re-sending the identical body would
fail identically.

**The intro — one line, a visible Skip, and the fence said before it is met**
([#445](https://github.com/Raketa02/Raketa/issues/445),
[ADR-0170](../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)).
`SOCIAL_STEPS` gained `intro` between `tags` and `photos` — _you've picked your tags; now say it
in your own words_ — so the part is eight steps and the opt-in is still last. The step is one
`TextField` that grows to a few lines, a counter to 100 in the number role — **the design
system's first**, admitted by a §6.13 amendment (Part 16, 2026-09-15) on one condition: a
counter is drawn only on a field whose cap is a refusal rather than a `maxLength` — a line of
small print, and _Next_ over _Skip_. **The cap is drawn as a refusal rather than as a `maxLength`**,
which is `WhereField`'s argument carried over: a `maxLength` swallows the tail of a paste, and a
shortened line is one the person who typed it believes they wrote whole, in front of every
stranger who reads it. So the box takes everything, the counter keeps counting past a hundred,
the refusal's own sentence appears under the box and _Next_ is shut until it is not — with the
sentence as its hint, because a blocked control names what is wrong. **Two of the three refusals
are shape and the client sees them coming**: `domain/intro` reads `too_long` and `multiline` off
the draft in the same three-member vocabulary the wire's `intro_not_admitted` carries, counting
in **code points** as the server's `len` does so a hundred emoji are a hundred and not two
hundred, and trimming first so a return after the last word is not a second line. **The counter
counts the same trimmed line**, not the raw box, so it can never read `104 / 100` beside an open
_Next_ — the spaces around a line are not part of it, and a counter that counted them would be
arguing with the rule it is there to show. The return key dismisses the keyboard rather than
breaking the line (`submitBehavior`), because the ordinary way of producing the second refusal
should not produce it. And because this is the first step of the part that types,
`SocialStepLayout` now wraps the scroller and the pinned action bar in `KeyboardAvoidingView`
under `KEYBOARD_AVOIDANCE` — the value the sign-in, sign-up and conversation screens already
use — so _Next_, _Skip_, the counter and the refusal are not under the keyboard on iOS while
the line is being written; on the seven steps with no keyboard it does nothing. `contains_contact` is the
server's pattern and is deliberately not restated on the client — a copy would be a staler one
on every phone the day it is tuned from a refusal — so it lands at the commit, six screens
later, and that is why **the rule is said up front**, under the box, in the refusal's own words:
the opposite of the photos step's silence about its check, for the opposite reason. The check on
a photo is wrong about some share of what it flags; the rule on a line is never wrong about a
phone number. **Skip is visible whatever is in the box, and it clears**: _skip_ means _no
intro_, a skip that sent what happened to be typed would be the one thing the word does not
say, and walking back after one finds the box empty. _Next_ on an empty box carries the same
nothing. The draft holds the line **as typed**, untrimmed, so a round trip finds the box as it
was left; the commit carries `introToSend`'s reading — trimmed, or **no field at all**, never
`''` or `null`, because the wire reads all three as one answer and the body sends the one that
cannot be read as a line. `stepTheCommitRefused` replaced `answerTheCommitRefused`: a refusal
that names a step is one shape for two kinds — an answer the server found missing, and a line
it would not admit — and the intro's is the one this screen will actually meet. It is drawn as
the reason's sentence in the failure note, never _try again_, with _Change your intro_ under it
back to `/intro` and the line still in the box; a reason this build has no words for keeps the
way back and says `OUT_OF_DATE_GAP`. The intro became editable with the tags and the photos, as
one piece of work, on the You tab (#471, ADR-0179 §6 — the day ADR-0170 §5 named); the paragraph
below says how. **Not seen on a device**: whether four lines is the right ceiling for the box,
whether the counter sits right under it, and whether the action bar rises cleanly over the iOS
keyboard, are the author's to check.

**The location moves on a cold start — silently, after a day in the background, never on a
plain foreground, and You says so** ([#462](https://github.com/Raketa02/Raketa/issues/462),
[ADR-0174](../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §6).
A location was written once, at the end of onboarding, and nothing moved it — a radar that
draws people where onboarding left them draws a city as it was. `useLocationRefresh` is the
first writer of `change_location` after the commit: called by the `(app)` layout with the entry
gate's own answer, because that is the one site that knows a player is signed in and past
onboarding, it reads one fix through the same `LocationPort` the location step uses —
foreground only, balanced accuracy — coarsens it on arrival with `areaAround`, and `PUT
/players/me/location` carries the **cell**, never the fix, exactly as the commit does. **It
never asks**: `getPermission()` only, so a permission revoked in Settings means no prompt, no
request and no sentence, and the stored cell stays. **Once on the mount, then only after a
day**: `foregroundRefreshDue` in `domain/locationRefresh` is the whole rule — a return from the
background reads again when more than 24 h have passed since the last _attempt_, whatever came
of it, and a plain foreground reads nothing, which the author refused as tracking. The instant
is a `ref`, a per-device convenience nothing else reads, gone with the process — which is what
makes the next launch a cold start; the tree also mounts on the way out of onboarding, and that
third read of the cell the commit stored seconds earlier is left alone rather than special-cased
— same cell, no event, `204`. **Nothing resets**: the deck's held deal stands, and its cards' _In
your area_ is the envelope's own `my_area_code` until the next hand; the radar's held reading
refetches on its own rule; the profile surface is invalidated — it carries no area today, and
the invalidation is what makes it follow the day the read grows the field. The write is a
`useMutation` like the feature's three others, for the query client's own reason: paused
offline and resumed on reconnect, so a cold start on a dead connection lands when the phone
does; a failed write is silence, and the next cold start writes again. A player still in
onboarding is never refreshed — the location step is where their area is being asked for, with
a prompt and a sentence, and the step's own read, its re-read on foreground and its tests are
untouched. **You** carries the one written trace, `AreaUpdatesNote` — `the-words.md`
§26's _Your area updates each time you open Raketa; it is never finer than about a kilometre._,
static, `tiny` in `muted`, under the profile block and above the account panel — because silent
motion with no written trace is the one thing that would surprise a careful player, and the
kilometre in the same breath is what keeps _updates each time you open_ from reading as
tracking. **Not seen on a device**: the read on a real cold start against the OS, and the
sentence's fit on the tab, are the author's to check.

**The profile's declarations on the You tab — each row a step's control under the tab's chrome,
and a draft until _Save_** ([#469](https://github.com/Raketa02/Raketa/issues/469),
[ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
§2). **The refactor came first**: each step this ticket reuses separates _the control_ from _the
onboarding around it_. `WeekGrid` is the availability grid drawn from a week — the step's own
mapping, with the footnote slot the step leaves empty and the tab fills; `SearchRadiusControl`
is the slider wired to `searchRadius` and `radiusPresentation`, with what a move does left to
the caller (the step writes the draft, the tab holds one); `useLocationCapture` is the press
alone — ask at the press, read one fix, coarsen it, hand the cell on — and `useLocationStep`
composes it with the step's two own rules, the draft and the unasked re-reads on arrival and
foreground. `locationPresentation` splits each refusal into `ACCESS_HOW_TO` (how to allow it,
true on every screen) and the step's cost clause about finishing setting up, which the tab does
not cite because it is not true of anybody on it. The steps' behaviour, copy and suites are
unchanged. **The rows** (`YouRows.tsx`) read their fact off `GET /players/me/profile` or
`GET /ratings` and say it through `youProfilePresentation` — _10 hours ticked_, _12 km · Across
your town_, _Padel Competitive · Squash not set_, the area's one static line — and `liveLine`
says the recovery sentence where a read failed rather than going quiet. **Your week** is
`WeekGrid` as the step draws it plus the footnote, a draft until _Save your week_, _Clear all_
offered, an empty week saved as a legal value (the commit's floor binds the answer a player is
asked for, not one they change later — ADR-0102); the draft is dropped the moment the save lands
so the grid draws **the route's answer** — collapsed, re-ordered — and the row's line follows
the cache. `sameWeek` in `domain/availabilityWeek` is what shuts the button while nothing has
changed, by cell and never by order. **How far to look** is `SearchRadiusControl` with a
_Save_, and **nothing writes on release** — the one behavioural difference from Find a game,
where the radius reaches the server as the first half of pressing the card; the write path
re-snaps and the slider then shows the radius as held. **Where you play** is _Your area is set_
in mint with `AreaUpdatesNote` under it — the note moved here from the tab's foot, and the
row's live line is the short form — and _Read my area again_ through `useReadAreaAgain`: the
step's press ending in `PUT /players/me/location`, the cold start's route called by a person
(ADR-0174 §6), in the step's three permission states, nothing read unasked, and the control
turning `settled` with _Location saved_ once the cell is put. **What kind of game** is
`PlayIntentsSection` as built, behind a row and under one line — _This changes how people find
you_ — which replaced the section's heading and body (retired, §9; the undeclared footnote
stays). **Two rows land with their contract**: Who you play with and Game suggestions (#472)
read fields the profile read grows on #466 and this client does not read yet; each row draws a
line naming what it is and the screen behind it says in one `tiny` line what it is and that the
edit lands with the read that carries the fact (`DEFERRED_ROW`, keyed so a row and its screen
cannot come apart) — 10.1's rule, never _coming soon_. Photos, Tags and Intro stood there too
until #471 (below). The gender and opt-in steps are **not** refactored on this ticket: their
second caller is the ticket that draws them, and a control separated with no caller to say its
shape would be a guess. **Not seen on a device**: the grid's footnote under a saved week, the
slider's _Saved_ after a re-snap, and the area screen's notes.

**Photos, tags and intro edited from You — the three onboarding steps as they are, one piece of
work** ([#471](https://github.com/Raketa02/Raketa/issues/471),
[ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
§2, §6, §8 — the day [ADR-0170](../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)
§5 named, when no field is editable while the two beside it are frozen). **The contract came
first**: `make gen-api` pulled three backend tickets' drift at once, and the read grew
`socialTagIds`, `photos` (the pairs, id and verdict) and `intro` on `PlayerProfileSurface` (#466);
the opt-in and the owner's own gender and preference are on the same response and are #472's to
read. #468's drift came with it — `sportsmanship_band` is off the wire — so `playerRecordMappers`
reads the one `sportsmanship` field for every reader; the band's words, its arm and the row that
draws it are #473's to retire. **The refactor came second**, as #469's did: `CourtPhotos` is the
photos step's body and its hold-for-options sheet with the chrome handed back as a render prop
(the sheet must be a sibling of whatever carries `behindOverlay`); `SocialTagPicker` and
`useSocialTagPicker` are the three groups of chips and the press that obeys the served bounds;
`IntroField` is the box with its counter, hint, rule and the refusal under it. The three steps
are those components under their own chrome, and their suites are unchanged. **The photo
workbench has two homes.** `useProfilePhotos` takes a `PhotoBench` — the photos, the photos _as
they are right now_ for the upload queue that runs between renders, and one change function —
and the step hands it the draft's (`useDraftPhotoBench`), whose every change derives
`draft.photoIds`. The tab hands it `useOwnPhotos`'s: a bench in a ref mirrored to state, seeded
**once** from the profile as first read (`heldPhotos`, each tile drawn from the signed address
`GET /photos/{id}` answers — `usePhotoAddresses`, read once per open, because a restored photo
has no device copy), whose every change that moves the **ids** sends `PUT /players/me/photos`
with the ids in order — a promotion, a removal, an upload that landed; a progress tick or a
failure moves no id and sends nothing. **A replacement stands in for the photo it replaced
until it has arrived** (`ProfilePhoto.replacing`, read by `standingPhotos`): the profile still
holds the old picture in that slot, so nothing is written while the new one is on its way and
nothing drops the old one if it fails — the review caught a first cut that wrote the row
without it the moment the picker answered. Writes are serialised, latest list wins: one in flight,
the bench read again when it settles, so two rearrangements cannot land out of order and a
`concurrent_modification` never refuses one of our own. There is **no _Save_**, because the step
never had one and the row is the state; a refused write keeps the row, says why under it, and
offers _Try again_, which sends the row as it then stands. `mutateAsync` rather than `mutate`
with callbacks, so an upload that lands after the player has left the screen is still written —
the step's _an upload outlives the screen_, kept. **The verdict has three states now.**
`UploadedPhoto.review` is optional: `allowed`, `flagged`, or absent for _nobody looked_
(ADR-0138), off both the upload (`null`) and the read (omitted); the row's live line says
_profile photo on court_ only of a photo the check passed, and the flagged notice warns only of a
flag. **Tags** is the picker under _On your card · Pick 2 to 6_ with the step's question as the
title, a draft until _Save_ — shut under the floor in the step's own words with the verb changed
(`socialTagsSaveLabel`, _Pick 1 more tag to save_), shut while the draft is the selection held
**by membership** (`sameSelection`, because the profile holds tags in the vocabulary's order
whatever order they were pressed in), the ceiling note pinned above the button; the write
answers in the vocabulary's order and the picker then draws that. **Intro** is `IntroField`
under _On your card_, a draft until _Save_ with _Remove intro_ beside it, offered only while a
line is held: the two shape refusals shut _Save_ before a send, drawn under the box in the
step's sentences; `contains_contact` lands on the reply and is drawn **in the same place from
the same table** (`introRefusalSentence`) — one press away here where it was six screens away
on the step — and clears on the next keystroke; a blank box shuts _Save_, because the way to no
intro is the control that says so, never a save of nothing; the route answers `204`, so the
cache holds the trimmed line sent (the same trim the server keeps) or none. **The three writes
invalidate the player's own record**: the header card draws the face, the intro and the tags
off `GET /players/me/record`, another feature's read of the same facts, and a tab that read the
old line after _Save_ would be the one screen the edit was made on saying it did not land —
invalidated through `playerRecordKeys`, never patched. The live lines are `photosLine`,
`tagsLine` (against the **served** ceiling, so the row reads the options too) and `introLine`.
**Not seen on a device**: the row drawn from signed addresses, the sheet over the tab's chrome,
the write failure pinned under the row, and the intro's action bar over the keyboard.

**Who you play with and Game suggestions — the gender step's two groups each under a _Save_,
and the opt-in answered again from You** ([#472](https://github.com/Raketa02/Raketa/issues/472),
[ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
§2, §4, §8). **The read came first**: `PlayerProfileSurface` grew `gender` (absent on a profile
committed before the question existed — never `prefer-not-to-say`, which is an answer somebody
gives), `genderPreference`, and `proposalsOptIn` as a `RecordedProposalsOptIn` — the draft's
pair with its moment and its surface, the surface spelled in `domain/proposalsOptIn` as this
app's own `ConsentSurface` because the screen keys a sentence by it, and held to the wire's by
the mapper's table. The two gender tables gained their inbound halves; the mapper's _neither
comes back_ became _both come back, on exactly one shape_. **The refactor came second**, as
#469's and #471's did: `GenderControls` is the step's two radio groups — _About you_ with the
cost line, _Who we should match you with_ with the reach sentence at the press — and
`OptInPromises` is the card the answer is given against; the two steps are those under their
own chrome, their suites unchanged. **Who you play with** is the two groups each in a card of
its own with its own _Save_ (`SavedGroup`), because each is its own fact with its own route —
`PUT /players/me/gender` and `PUT /players/me/gender-preference`, both `204`, both held in the
cache as the value sent for the intro write's reason — pre-selected from the read, _Save_ shut
while a group's draft is the answer held, the two _Save_s told apart for a listener by a spoken
name carrying the group (`groupSaveLabel`, _Save — About you_; a name and not a hint, because a
hint can be switched off); the step's scope note and durable-setting line are not drawn (§9). The reach sentence is `reachNote`'s, drawn by the control on both screens, so the
second surface that takes the value says it without either screen having to remember to. **The
row says _Matched with …_ and never the gender**, and the header card and the record draw
neither, as before. **Game suggestions** is `OptInPromises` with `OPT_IN_PROMISES_ON_PROFILE`
— the step's three with the third reading _any time, from here_, built from the step's list so
a reword there cannot leave this card behind, and **not a fourth copy version**: the identifier
names the promise, and the one word that differs is where the reader stands, so a press here
stamps `proposals-opt-in.v3` like the step does — the scope line above it, and an answer card:
_Your answer_ with `Yes`/`No` as a `Tag` (`ok` for a yes), the evidence line _Given 12 Aug,
against these words (proposals-opt-in.v3), from setting up_ (`answerGivenLine`, the day in the
platform's zone through `platformDay` + `dayDate`), and the two answers in the copy's order
(_No_ first, `OPT_IN_ANSWERS` — the prototype drew _Yes_ first, and the copy's rule that a
screen mapping its own list could reverse it unnoticed is exactly what that constant exists
for). **Every press sends** `PUT /players/me/proposals-opt-in` with the version on screen, the
standing answer included, and **the card follows the reply**: the route answers with the record
it made — the server's clock, the route's `PROFILE` — and `useAnswerProposalsOptIn` writes that
into the cache, never the press; there is no _Save_ and no draft, and the pressed answer is busy
under its own label — the press is the answer, and there is no other word for what it is doing.
The step's _never pre-ticked_ line and its eyebrow are not drawn: here the answer **is**
pre-selected, because it was given.
The live lines are `whoYouPlayWithLine` (the preference only) and `gameSuggestionsLine`
(_Yes — since 12 Aug_). `DEFERRED_ROW` and `DeferredYouScreens` are gone with the last two rows
they stood in for. **Two calls for the author**: that a press from the profile stamps the step's
version while the third promise reads differently — the argument is above and in
`optInPresentation`, and the review named it a ruling rather than a violation; and the answers'
order, which follows the copy over the prototype. **Not seen on a device**: the two cards'
rhythm under the tab's chrome, the tag beside _Your answer_, and the busy state on a pressed
answer.

**A _Save_ with nothing to send is green and says so, and turns green as the save lands**
(2026-09-18; design-system [6.1](../design-system.md#61-button) as amended that day). The seven
_Save_s behind the tab's rows — the week, the radius, the two gender groups, the tags, the
intro, and auth's name — said `Saved` while the draft was the profile's own and were drawn as a
`primary` at the disabled 40%: a coral saying _done_ at less than half strength. Each is now
`variant={dirty ? 'primary' : 'settled'}` and nothing else about it changed — the labels, the
disabled state and its spoken name are as they were — and the two things that make that a
picture are the button's own: a shut `settled` keeps its fill, and **arriving at `settled`
cross-fades the coral into the mint over one `fade`**, under the label, once, never on the way
back, skipped under reduced motion. So a screen opened with nothing to save is simply green,
and a save that lands turns green under the word as the draft is dropped. **Two are not
green**: the tags' _Pick 1 more tag to save_, an ask shut under the floor, and the intro's
_Save_ over a refused or blank line — nothing about either is settled, so both stay a dimmed
`primary` (`standing.kind !== 'ready'` and `line === undefined` respectively, which is what the
disabled condition already said). The location step's `SettlingControl` — the whole control
fading in on arrival at _Location saved_ — retires, because the button now does the same thing
to the fill alone and two fades on one arrival read as neither. `Photos`, `Game suggestions`
and `What kind of game` have no _Save_ and are untouched; `Where you play`'s _Location saved_
gains the arrival fade for free. The four You suites read the fill beside the word through
`test-support/drawn.ts`, and `Button.test.tsx` pins the fade's shape on a fake clock. **Not
seen on a device**: the cross-fade's length against the busy dim it follows — `Saving…` is
dimmed coral and `Saved` is whole mint, and the jump in opacity lands on the same frame the
fade starts.

**Your week is a week of hours: seven days across, sixteen hours down, a tap toggling one hour and
a press and drag painting a run** ([#551](https://github.com/Raketa02/Raketa/issues/551),
[ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §5, the
mechanics §4.2, the screens A6, mock 36). One grid serves the availability step and You's _Your
week_ — `WeekGrid`, now `MON … SUN` across and `07:00 … 22:00` down, over design-system 6.8 as
amended the same day. **A drag is a paint, not a toggle of a run**: the hour it began on decides
what it does — it ticks, or it clears if that hour was ticked — and every hour the finger then
crosses gets the same, the ones a fast finger jumped between two samples included. The grid
reports **the run so far, whole, on every move**, and `paintCells` in `shared/vocabulary/week` is
idempotent, so a screen a render behind the finger still lands every hour: the step answers
`paintCells(week, run, on)` into the draft, and _Your week_ paints onto its draft through a
functional update. **The floor is unchanged and still one**: the step will not continue on an
empty week, whether the last hour came off by a tap or by a drag, and its eyebrow and control say
_Pick at least one hour_; the tab still saves an empty week as a legal value. **The wire moved
with #534**: `PUT /players/me/weekly-hours` and `weekly_hours` on the commit, its response and
the read, the refusal `weekly_hours_empty`; the draft's and the commit's field is `weeklyHours`,
the cell is the glossary's **Weekly hour** (`WeeklyHour`, `{ day, hour }`, replacing `WeekCell`
and the `AvailabilitySlot` alias the glossary now avoids), and the mapper drops an hour outside
07–22 as it drops a day outside 1–7. A cell is named _Monday 19:00_ and counted in hours —
_2 hours ticked_. The grid's own decisions — the gesture, the geometry, the cell under 44pt — are
[`_shared.md`](_shared.md)'s. The router suites drive the drag through `test-support/weekGridTouch`, which
lays the paint field out and fires the pan with samples hours apart. **Not seen on a device**:
that a drag down a column paints rather than scrolls the page on both platforms, the 20pt cell
under a thumb, and the tick at that size — the three things this change could not prove in Jest.

**Setting up ends on _Who you play with_, and You loses _How far to look_ and _Game
suggestions_** ([#582](https://github.com/Raketa02/Raketa/issues/582), PRD
[#569](https://github.com/Raketa02/Raketa/issues/569)). The Search radius and the Proposals
opt-in were read only by the old loop's ranking, and both left the server with it (#581), so a
player who answered either changed nothing they would ever see. `SOCIAL_STEPS` is **six** —
tags, intro, photos, availability, location, gender — and `/radius` and `/opt-in` are gone, with
`search_radius_km` and `proposals_opt_in` off the commit body. **The finish moved onto the gender
step whole**: it is `ProfileFinish`, which the opt-in step used to draw inline — the failure
note, an answer still wanted and the way back to it, a refusal that names a step, the photo
still arriving, and the busy finish under the part's one key, their sentences unchanged — handed
the step's own hint for the one answer asked on that screen (`GENDER_FINISH_BLOCKED_HINT`,
_Choose an answer about you to finish_). The gender answer is that screen's question now, as the
opt-in was (`ASKED_ON_THE_LAST_STEP` in `domain/profileCommit`, held to the step order by a
test), so `answerStillWanted` leaves it out and `MISSING_ANSWER_COPY` lost its entry along with
the radius's. **The control says _Finish_**: _Finish — show me players_ named a Players deck
that no longer exists, and what follows the commit is _What Raketa keeps_ and then the app. **The consent
copy went with the question** — `optInPresentation` and its three versions, `OptInPromises`,
`domain/proposalsOptIn` (`ConsentSurface`, `RecordedProposalsOptIn`), `useAnswerProposalsOptIn`
— and so did the radius's pieces: `domain/searchRadius`, `radiusPresentation`,
`SearchRadiusControl`, `useChangeSearchRadius`. `GET /player-profile/options` serves the tags
alone and the profile read lost both fields. Onboarding's _What Raketa keeps_ lost _how far you
will travel_ and its card about suggestions, and **does not list the gender answer in their
place**: its card says what lets another player see who they would be playing, and the gender
step promises that answer is never shown or shared. The paragraph that stood near the top of this
record — _the consent step's copy is frozen and versioned_ — is gone with the file it described.
**Left for a design-system ticket**: `RadiusSlider` (6.10) and `theme.size.radiusSlider` have no
caller. **Not seen on a device**: the finish's notes stacked under the gender step's two groups.

**_Finish_ lands on Home** ([#730](https://github.com/Raketa02/Raketa/issues/730), ADR-0200 §1).
`ProfileFinish`'s `AFTER_THE_PART` is `/`: _What Raketa keeps_ recorded nothing and went, and the
commit marks the profile on the player read, so the gate lets her through to the app's root. The
six steps are all of onboarding after the naming now — the questionnaire left it — so step one is
entered straight from _How should people see you?_, and no rating is read on the way.

**The intro takes 250 characters and says its rule only when it is broken**
([#733](https://github.com/Raketa02/Raketa/issues/733), ADR-0200 §9). `INTRO_CAP` is 250, so the
counter reads _n / 250_ and _Keep it under 250 characters._ is the length refusal — on the step
and on You's _Intro_, which draw the same `IntroField`. **The paragraph of rules under the box is
gone** (`INTRO_RULE`): it argued, above, that the contact refusal lands six screens later and so
had to be said up front, and ADR-0200 §9 ruled the other way — small print to everybody who would
never type a phone number, on the screen meant to be the part's shortest. The rule stands, and
its sentence is unchanged: _Leave out phone numbers, emails, links and handles — people reach you
in the chat._ is said only to a line that breaks it, at the commit (with _Change your intro_) or
under You's box on the save. The box grows to **nine** lines rather than four, by the arithmetic
its note already made: a hundred characters was three lines at the value role, so 250 is eight to
read back whole, and one more is room for the overrun. **Not seen on a device**: nine lines over
the keyboard on a small phone.

**_Where do you play?_ tells the truth, waits for an area, and answers a refusal with a club**
([#733](https://github.com/Raketa02/Raketa/issues/733), ADR-0200 §10, Apple 5.1.1(iv)). The
note is ADR-0200 §10's sentence — _Raketa shows how far each club is and lists the nearest first.
Your area is rounded to about a kilometre and never shown to other players._ — and every line
about nearby players or matching went: _Continue without matching_, the cost clause about
finishing without an area, and the commit's _Finding players near you…_. **_Continue_ is drawn
only once there is an area**, plain and `primary`, because the finish never could go without one
and a step that let a player past what the end refused was the contradiction the ADR names; the
finish's _We still need the area you play in_ stays, in truthful words, for a draft that arrives
without one, and now also answers `location_club_unknown` with the way back to the step rather
than _try again_. **After a refusal** — denied, blocked, or no fix — every note names the other
way (`ACCESS_HOW_TO`, `NO_FIX_BODY`; the step's and the tab's sentences are one now, since both
offer it) and `AreaClubPicker` is drawn under it: _Pick a club near where you play_, one field
over **groups' home-club search** (`useHomeClubSearch`, `ClubCard` with a _Pick_ pill, exported
from `groups/types` for this third caller), A–Z with no distance while the player has no area,
nearest first once she has; no groups drawn under a club; _More clubs_ as a control, since neither
host's scroller is the picker's. **The draft's area is a `LocationSource`** — `{ kind: 'reading',
area }` or `{ kind: 'club', club }`, the backend's pair — and `toWireLocation` is the one mapping
both writes use: a reading is its two numbers, a club is `{ club_id }` alone, never a key from the
other (each side of the server's union forbids extras). The picked club keeps its name and
district in the draft for the chosen card, on `mintSoft` with _Change_, which lets go of it; the
picker stays drawn while a club is the answer, so walking back finds it. _Use my location_ steps
back to `secondary` while a club is the area, says _Location saved_ only of the phone's own
reading, and **a reading replaces a club**: the step's foreground re-read after the permission was
allowed in Settings, as the cold-start refresh does once she is in the app (it sends
`{ kind: 'reading' }` only, and is otherwise unchanged). **You › _Where you play_ offers both ways, always** — `useReadAreaAgain` became
`useChangeArea`, one mutation for both writes, which reads off it everything the screen draws: a
pick shows chosen with _Change_ saying _Saving…_ on the ordinary surface while it goes and on mint
once it lands, a reading after it takes it off the screen as it takes it off the server, and a
refused pick is let go of under the coral reason — `location_club_unknown` in its own sentence
(`AREA_WRITE_REFUSAL`, through `codeMessage`). **Every write of the area joins one mutation
`scope`** (`LOCATION_WRITES`, the cold start's too), so a pick and a reading pressed one after the
other land in that order. Its
control is _Use my location_ — _Read my area again_ retired — and its eyebrow is _Your games_
(shell's rename). **Calls made here, not in the ADR**: the field drawn at once rather than behind
a button; _Pick_ as the pill's word; _More clubs_; the step keeps the refusal note up after a pick;
the tab's _Your area updates each time you open Raketa_ is kept although a club-picked area does
not move until the phone may be read. **Not seen on a device**: the picker on the step under the
keyboard, and the chosen card beside _Use my location_.

**_What kind of game_ says what a change costs, counted across the groups**
([#742](https://github.com/Raketa02/Raketa/issues/742),
[ADR-0201](../../../docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
§6, the You screen 3.3, the words §27's rows marked _(ADR-0201)_). Opening a **declared** sport's
row reads `GET /players/me/deck-counts?sport=` (`useDeckCounts`; which sport is
`domain/intentChangeCost`'s `sportToCount`), and a line in `tiny` `muted` is drawn under each
answer that changes something, below its gloss, which stays. **Which line goes where is
`intentChangeCost`'s**, in the deck's own `GameKind` (a Mode, never a Play intent with a value
taken out — the glossary keeps them separate types): to a single kind, from the other or from
_Either suits me_, the other kind goes and is counted — _Your 7 competitive cards in your groups
go. Games you’re In on stay._, _Your 1 … card in your groups goes._, and at zero _Raketa stops
dealing you competitive games._; to _Either suits me_, _Keep your competitive cards and get
for-fun ones too._, with no count. The answer held, and every answer to an undeclared sport, says
nothing, and the undeclared footnote stays. **A count not in hand is not zero**: while it loads,
and after it fails, the line keeps its plural shape without the number (_Your competitive cards in
your groups go._), no alert is drawn, and the answers press as before — still
`PUT /play-intents/{sport}` on `PROFILE_SCREEN`. The panel's _competitive_ / _for-fun_ before a
noun is spelled again in `playIntentsPresentation` rather than shared: this is its second caller.
**A count lives as long as the opening that read it** (`staleTime: 0`, `gcTime: 0`): the jobs, the
deck and the group page's door all change it unseen, so closing the row drops it and the next
opening says no number until its own read lands — never the last opening's, never one from before
a change of intent, and a failed read leaves no older number behind. That is why no sport is
`skipToken` under a key of its own rather than `enabled: false` on a borrowed sport's, which would
keep that sport's count alive. The router harness runs fake timers, so a suite that reopens a row
steps the clock past the close. The wire types were already regenerated by #741. **Not seen on a
device**: the line under each glossed answer, and the row's height with three answers and two
lines open.

**_Show me in General_ — the one row on the tab that is a switch**
([#778](https://github.com/Raketa02/Raketa/issues/778),
[ADR-0203](../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §7, the You screen
3.14, the words §27's row marked _(ADR-0203)_). The last row of _On your card_, after _Nickname_:
6.12's switch in a card of door rows — the door row's lead square (Feather `eye`), the title _Show me
in General_, the line _Players who don't know you can see your place, open your record and send you a
request._ under it, the track where a chevron stands (`ShowMeInGeneralRow`). It reads the profile
read's `ranking_visibility` (`showMeInGeneral`: on is `SHOWN`, through a table so a third value fails
to compile) and **is drawn only once that read has landed** — there is no switch to draw on a guess,
and the rows above it already say a failed read's recovery sentence. **It writes at once**, with no
_Save_ — `PUT /players/me/ranking-visibility` (`useShowMeInGeneral`): while the write is out the
switch stands where it was pressed — the mutation's own value, never a store — and once it lands the
profile read holds it (the route answers `204`, so the value sent). A refused write puts it back and
says why in a coral note under the row; nothing was patched, so nothing rolls back. **One queue holds
every write of it** (`RANKING_VISIBILITY_WRITES`), the You row's and Rankings' hidden card's, so two
presses reach the server in order and this app never sends the two concurrent writes the route
refuses as `concurrent_modification`. **Both hooks are exported**, with the title as the switch's
name: `rankings` draws the same switch on the hidden card (`useShowMeInGeneral`), and its General
page follows the value the profile holds (`useShownInGeneral`, a read that turns nothing)
([`rankings.md`](rankings.md)).
The wire types were already regenerated by #775. **Not seen on a device**: the row's lead and track
under the door rows, and the note under it.
