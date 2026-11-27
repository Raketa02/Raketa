# onboarding — the entry gate, and the rating pass where play begins

> The design record for `src/features/onboarding/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**Onboarding is two parts, and the part is the checkpoint unit**
([ADR-0090](../../../docs/adr/0090-onboarding-per-player-checkpoint.md)). Part one is the Skill
rating and resumes mid-run; part two writes nothing until one commit at the end, so leaving
it restarts at step one. The entry gate reads three facts and has four destinations — resume
· welcome · the social steps · the app — and the second part's screens live in
`player_profile/` rather than in `onboarding/` because the profile screen will later edit the
same values against the same rules
([ADR-0089](../../../docs/adr/0089-player-profile-context-event-sourced.md)).

**The device's back button is the screen's own back control, and where a screen draws none the
press is claimed and nothing happens.** Every screen in onboarding is reached by `replace`, so
the group holds one history entry per push and the thing under it is whatever was on screen
before the part began — welcome, one push behind the sport picker. Unclaimed, Android's back
popped to exactly there: out of the part, past the control the screen does draw, and into a
screen whose only way forward is to rate another sport. ADR-0090 forbids it in as many words —
_"Back and forward move freely inside each part and never cross between them"_ — and the
restart that ADR describes is what a **new launch** does through the entry gate, which a
gesture is not. So a social step goes back a step, a question goes back a question, and the
review, the result, the ratings summary and the data screen refuse: `stepBefore` and
`questionNavigation`'s floor have already said there is nothing behind a first step, and a
press that walks out anyway is a second, louder answer to a question the screen has answered.
The mechanism is `useHardwareBack` in `shared/lib/platform`, subscribed **only while the screen
is focused** — a stack keeps the screens under the top one mounted, and handlers run in reverse
registration order, so a plain effect would let a question screen sitting under the result go
on answering for it. Welcome and the sport picker are deliberately left alone: welcome is the
app's root for a new player and back there should leave the app, and the picker is the one pop
of a genuine push.

**The ratings summary ends the first part, and it is the door into the second.** The order
is result → **done** → the six steps → the commit → data → the app. The _pass_ routes as far
as the summary and no further (`nextDestination`: _is there anything to account for_), and
the **done screen** reads whether a Player profile is still owed and either enters the second
part or continues to the data screen — one fact, read once, on the screen that acts on it. A
player who is already set up — one resuming a run they left behind — passes straight through.
The summary comes before the six steps rather than after the commit, because it is what a
player just earned and the second part was otherwise standing between them and it; a Skill
rating is written when the questionnaire completes, not when a profile is committed, so
nothing on that screen was ever waiting on the commit to be true. Entered with no pass
running, it has nothing of its own to show and says so.

**The entry gate reads the name before anything else, and the naming step is the first screen
after sign-up** ([#451](https://github.com/Raketa02/Raketa/issues/451),
[ADR-0171](../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
§3). The gate has five destinations now — _no name → the naming step_ · resume · welcome · the
social steps · the app — and the new one goes **first**, because every destination after it says
the player's name: the questionnaire may address them by it and every surface inside the app
does. It is read off `GET /users/me`'s `name`, which rides on the read the gate already makes for
`has_player_profile` and is served from the `User`'s own stream for the same reason — the moment
after the naming is exactly when a lagging read model would send a player back to the step they
just finished. It passes the glossary's test the way the profile flag did: a name has no sport
dimension, so _does this player have a name_ is a per-player question with a per-player answer.
The gate routes every shape, including the ones the flow cannot produce — an unnamed account
holding a run or a rating is still sent to the naming step, on the fourth destination's own
lesson that a shape the gate does not route is a loop. The step itself is `features/auth/`'s
(its record says why), reached at `/name` through `NAMING_STEP` as the social steps are through
`SOCIAL_STEPS_ENTRY`; it claims the hardware back like every first step does, and after the
naming it hands the next destination back to this gate rather than naming welcome itself.

**`Verdict` is the result card, extracted** ([#469](https://github.com/Raketa02/Raketa/issues/469),
[ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
§2). The dark card the result screen draws — _Your level_, the figure, the likely range, the
confidence ring, the on-dark level bar with its legend, _Band_ and _Rating status_ as rows, and
the three information marks — is a component of its own now, because the Skill passport draws
it once per rating and a player who met their rating on this card recognises it there. It takes
**a rating** (the fields a finished run and a rating read back both carry), a `top` slot the
passport fills with the sport tag and a status chip, and the _Questions asked_ row only where
the caller hands one — the run's own fact, not the passport's. **The marks' popover moved to the
screen**: the card holds its three refs and hands the pressed one up as `Explaining`, and the
screen draws one popover as a sibling of its root, so a screen with several cards draws one for
all of them. `explainers` travels with it, built per rating because the one number in it is the
served ceiling — and a card whose rating carries none says nothing about a ceiling and draws no
tick, which is what every passport card does today. The band card under the verdict stayed with
the result screen (`BandCard`): it is the run's, and the passport draws the ladder instead.
`useSports` and `ratingStatusLabel` are exported for the passport's _Add a sport_ chips and its
status chip.

**A pass has an origin, and a pass may begin at the Skill passport**
([#470](https://github.com/Raketa02/Raketa/issues/470),
[ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
§3). The glossary's _there is no re-take from inside the app_ narrowed to _a pass has an origin_:
`begin` takes it — `welcome` for the picker's queue and for a run the gate resumes with no picker
in between, `passport` for the passport's _Add a sport_ — and **where a pass ends is read off
it**. `stopDestination` answers `passport` for a passport-begun pass whatever it produced, so the
result's _See your ratings_, the leave sheet's _continue later_ and its _abandon_ all land back on
the passport, never on the done screen, the data screen or the social steps, because a Player
profile exists and those screens are onboarding's. The chip's act is `useAddASport`, exported for
`player_record`: the picker's own start (a sport with an unfinished run gets that run back), a
pass of exactly that sport begun **on success** rather than on press — the player is in the app,
and between passes there is no pass, so a failed start leaves no pass lying around — and a
`replace` to the question route. Everything between the two ends is untouched: the question
screens, revision, the review, the calculating screen, the result card, the admission rule (a
passport pass admits exactly its one sport; a link naming another is still sent to welcome). **The
landing is the gate's.** The three exits of a passport pass leave to `/` exactly as a welcome
pass does — `useAdvanceThroughPass` spells no route it does not own — and the gate's app branch,
the one site that ends a pass, is handed the ended pass's origin (`end` now _returns_ it rather
than the hook subscribing to the store, which would end the pass the chip has just begun) and
lays the You tab down with the passport over it, so _back_ from the passport goes where it came
from. The gate's _resume_ branch is unchanged, so a run begun from
the passport and deferred is resumed on the next cold launch as a welcome pass and ends the way
any resumed run does — ADR-0179 names that as a consequence. The frame between the gate mounting
the first tab and its effect laying the stack down was seen on a device in the end, as a blink on
a group pass's way back, and no longer exists — see the landing paragraph at the end.

**The gate reads the account's profiles first** ([#516](https://github.com/Raketa02/Raketa/issues/516),
ADR-0185 §3). `entryDestination` has a sixth destination, **the administrator area**, ahead of the
naming: an account that does not act as a player and administers a club goes to that club's area
(`administratorArea`, the first club the server lists) and is never sent into onboarding — it has not
asked to play, and a name without a nickname, no ratings and no run are no questions it owes. The hook
answers it **from the player read alone**, the moment that read answers, without waiting on the
ratings or the run — and once the player read says so, those two reads are not asked at all. An
account that also plays falls through to the five destinations as before and opens in Player; the
last-used profile is #518's. The redirect is `(app)/_layout`'s, to the route the `administrator`
feature names (`administratorHome`).

**No profile at all goes to _Start playing_, and named in full is a name and a nickname**
([#517](https://github.com/Raketa02/Raketa/issues/517), ADR-0185 §3–§4). The gate's first read is
`profileDestination` now: the administrator area for an account that only administers, and **a
seventh destination, `start-playing`**, for one that holds no profile at all — an administrator-only
account its club removed — which the layout redirects to `auth`'s `START_PLAYING_STEP`, the Adult
attestation, ahead of the naming and of anything a player owes; like the area, it is answered from the
player read alone. Past that read the first destination is **not named in full** (`namedInFull`: a
name _and_ a nickname), because an account an Invitation opened carries the club's name and no
nickname: once it attests, it acts as a player and the naming is still owed — asking only for the
nickname ([`auth.md`](auth.md)). For every account sign-up creates this is the same destination as
before, since it holds neither until the naming.

**Named is holding a nickname** ([#728](https://github.com/Raketa02/Raketa/issues/728),
[ADR-0199](../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3, amending the two
paragraphs above where they speak of a name). The gate's first player destination reads **no
nickname**: `EntryInput.named`, from `auth`'s `named`, off `GET /users/me`'s `nickname` — the
same read, served from the `User`'s own stream for the same reason. `/users/me` no longer serves a
name, and an account an Invitation opened holds none (§4), so _named in full_ and `namedInFull` are
gone: such an account, once it attests, is sent to the naming like any account sign-up created,
and the step tells it what the nickname is for ([`auth.md`](auth.md)). The order is unchanged.

**An account with two profiles opens in the one it wore last** ([#518](https://github.com/Raketa02/Raketa/issues/518),
ADR-0185 §3, ADR-0188 §2). `profileDestination` takes **the profile the phone remembers** (`auth`'s
`useLastProfile`) ahead of everything: an administrator profile the account still holds opens that
club's area — ahead of the naming and of anything the player side still owes, because choosing that
profile was choosing not to be asked those now, and switching to Player is where they are asked. A
remembered club the account no longer holds is no choice (ADR-0188 §4): the account opens as if it had
chosen nothing — **Player** for an account that plays, its first club for one that does not. **The gate
waits for that local read only for an account that runs a club**, and for no other launch; but the read
is made for every account, so that one gaining a club under a mounted gate — an invitation accepted
from the sheet over the app — finds it long settled. A read that began only then sent the gate back to
_pending_ and unmounted the app it was drawing, the sheet with it, which the invitation suite caught. An
account that does not play never asks the player's reads, whichever club it opens on.

**_What Raketa keeps_ lost the radius and the suggestions consent**
([#582](https://github.com/Raketa02/Raketa/issues/582)): setting up stopped asking either, so the
screen keeps no account of them. Why the gender answer did not take the radius's place on the
card is in [`player_profile.md`](player_profile.md).

**A pass begun on a group returns to it** ([#729](https://github.com/Raketa02/Raketa/issues/729),
[ADR-0200](../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §3, §5, amending the
passport paragraph above). The origin is a union now — `welcome`, `passport`, or `group` with the
group's id and **the tab it began on** (`fromAGroup`), identifiers only, since the group's name is
Query's. The tab is `groups`' word, imported as a type only: `groups` imports this feature at
runtime, so a value import back would be a cycle through the two barrels. `stopDestination` answers
`group` whatever the pass produced, so every way out — the last result, _Done for now_, _continue
later_, _abandon_ — replaces to `/` as a passport pass's does, and the gate's landing is handed
`returnOf(pass)`: the passport, or the group, its tab and **the sport rated last** (the last of
`rated`; none when nothing was). `(app)/_layout` lays Play down with `groups`'
`groupReturnRoute` over it, so _back_ is the Groups list; the page opens on that tab and stands on that
sport the way a notice's card does, never saving it as a pick. **_Your rating_'s words moved to
`resultPresentation`**: mid-pass _Rate {next}_ and _Done for now_, unchanged; on the last sport
_Back to {group name}_ for a group pass and _See your ratings_ for the rest. The result **route**
asks for the name — `useReturningGroup`, then `groups`' `useGroupName`, the page's own read under
its key — and hands it in; while it is unread the control says _Back to the group_. **Two doors
begin a group pass.** `useAddASport(from)` takes its origin: the passport hands
`FROM_THE_PASSPORT`, and the official group's card (`AddSportCard`) its group and the tab to come
back to — the page its own, _Post a game_ You’re in (where its button lives and a post lands,
whichever tab it was opened from — #848; Fill in until #847), Members the tab the page beneath it is
on. And **the picker takes one from
its route**: `/sports?groupId=…&tab=…`, checked by `groups`' `parseGroupPlace`, anything else being
onboarding's own picker. Nothing in the app opens it yet; it is the seam #730's door calls. The
picker now begins its pass **on the start's success**, as the chip does, so a failed start from
inside the app leaves no pass behind. **The card's buttons say _Rate Padel_**, as the issue, the
PRD and ADR-0200 §3 quote them and as the passport's chip says it; _Add Padel_ was the wording of
a pass that ended on the passport. **Calls made here**: a pass from Members returns to the page,
not to Members; a pass from _Post a game_ returns to You’re in (Fill in until #847), not to _Post a
game_ — and not to the tab _Post a game_ was opened from, which only a back-out returns to (#848):
opened over Games, the pass still ends on You’re in. **A group's fourth tab** (#847): You’re in is a pass's origin like any tab, and the route
names it `youreIn`. A tab this build does not know is still dropped: the picker reads it as no
group (`parseGroupPlace`), and a page route opens on Games (`parseGroupRouteParams`). **Not seen on a
device**: the frame between the gate mounting Home and the group's page pushed over Play.

**Onboarding is a nickname and a profile, and a level is asked where play begins**
([#730](https://github.com/Raketa02/Raketa/issues/730),
[ADR-0200](../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §1–§6, amending every
paragraph above that speaks of welcome, the summary, the data screen, _resume_ or a deferral).
**The gate reads the player and nothing else**: profiles → _no nickname_ → the naming →
_no Player profile_ → the six steps from step one → the app. `entryDestination` lost its
`ratings`, `runInProgress` and `deferredRunIds` inputs and its `welcome` and `resume`
destinations, and `useEntryDecision` its two parallel reads, so a cold launch waits on
`/users/me` alone; the _stale at mount, not yet answered since_ bound now guards that one read.
A sign-up is eight screens — sign-up, _How should people see you?_, the six steps, Home — and
the naming's _Continue_ hint says _Next, what kind of player you are_. **Deleted with their
routes and copy**: _Let's set you up_ (`WelcomeScreen`, `/welcome`), _Your starting ratings_
(`DoneScreen`, `/done`, with `useRunResults`) and _What Raketa keeps_ (`DataScreen`, `/data`);
`ProfileFinish` replaces to `/`, so _Finish_ lands on Home. **The pass's origins are Home, the
passport and a group** — `welcome` became `home` (`FROM_HOME`): the picker opened with no group,
and a run reached by a link with no pass running. A pass ends where it began whatever it
produced (`stopDestination`), so `closing` and `app` left `PassDestination` for `home`, every way
out of a pass replaces to `/`, and the last _Your rating_ says _Back to {group}_, _Back to Home_
or the passport's _See your ratings_ (`lastControlLabel`). A link outside the running pass goes
to `/` rather than welcome; with no _resume_ there is no loop to fear, and the gate ends the pass
it interrupted where it began. **The deferral went**: `deferredRuns.store` existed only so the
gate's _resume_ would leave a run set aside alone, and _continue later_ now just leaves.
**The level door** (`LevelDoor`, exported with `DoorOrigin`) is the one dark card a player rated
in nothing meets in a player group, on Games, Fill in, You’re in, Friends, _Post a game_ and Members —
drawn by `groups` where its `needsALevel` says so, with the pass returning to the tab it stood
on (_Post a game_'s to You’re in, whichever tab it was opened from — #848; Fill in until #847 —
Members' to the page's tab, as #729's card does). `levelDoor`
is its rule: no run → _Get your level — Pick the sports you play, a few questions each._ with
_Pick your sports_, opening `/sports?groupId&tab` (`sportsPickerRoute`); a run left halfway →
_Carry on with your padel questions — You're on question 5._ with _Carry on_, beginning a pass
of that sport and replacing to its question. The number is the run's own count — answered plus
the one outstanding, or the last answered for a run stopped at its review — so the door reads
the run's step as well as the list (`useRunInProgress`, the gate's old read, then
`assessmentQuery`); nothing is drawn until both answer, a failed read offers the picker,
since starting a sport with an unfinished run hands that run back, and a read paused offline
with nothing cached draws the amber _You're offline_ note instead. **The picker has a way
back**: the door reaches it by `replace`, so its header _Back_ and the device's back **turn
back** — a pass over no sport (`turnBack`), which the gate lands at its origin. **_+ Post a
game_ still floats over the door on You’re in** (Fill in's until #847), as the screens A3 has it, and _Post a game_ draws the
same door. **Calls made here**: the door's two lines are the spec's sentence split at its dash,
and its buttons _Pick your sports_ and _Carry on_ are this ticket's words; a run stopped at its
review reads _question {last answered}_; the picker's back control. **A player rated in some
sport with another sport's run left halfway sees no _Carry on_** — the door is for the unrated —
and gets the run back from the passport's chip or #731's _+ Another sport_, whose start hands an
unfinished run back. **Not seen on a device**: the door's card, and the frame
between the gate mounting Home and the group pushed back over Play.

**Two more doors into the picker, and one narrows it**
([#731](https://github.com/Raketa02/Raketa/issues/731),
[ADR-0200](../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §4, §5, §7). **The picker
takes an offer**: `/sports?…&offer=tennis,squash`, read by `parsePickerOffer` (one param, the sports
joined by commas, so the route is a plain string however expo-router serialises a list) and drawn
through `sportsOnOffer` — the served sports, in the server's order, narrowed to those offered. An
offer that is not one is no narrowing: the list is longer, and the server's start still refuses a
sport already rated. `sportsPickerRoute(from, offer?)` moved out of `useLevelDoor` and is exported,
because `groups`' _+ Another sport_ opens the picker too, over what it offers; the door and the Home
card offer every sport and carry none. **`LevelDoor` is Home's card as well**, `from` `FROM_HOME`:
only its line under _Get your level_ differs by where it stands (`LEVEL_DOOR_COPY.line`, keyed by
the origin's kind) — _Pick the sports you play, a few questions each._ on a group's tab, _Your groups
can't deal you games until you have one._ on Home — and its pass ends on Home, whose last control
#730 already said _Back to Home_. Whether the card is drawn is `groups`' rule
([`groups.md`](groups.md)). **Calls made here**: the Home line is the spec's sentence split at its
dash, as the door's is; the offer travels in the route rather than being read again by the picker.
**Not seen on a device**: the card on Home.

**The first _Your rating_ a phone shows an account runs a guide over the verdict**
([#732](https://github.com/Raketa02/Raketa/issues/732),
[ADR-0200](../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §8). The screen dims and
`shared/ui`'s `Guide` (design-system 9.4) cuts out **the level** with its head, then **the likely
range**, then **the confidence ring** — _1 of 3_ to _3 of 3_, _Next_ and _Skip_, _Got it_ last —
in the ⓘ marks' own words (`explainers`), so bubble 3 keeps _"The questionnaire can provide up to
{ceiling}% confidence."_ A tap on the dim is _Next_, the device's back is _Skip_, and **nothing
beneath answers**: the screen's root takes `pointerEvents: 'none'` while the guide is up, beside the
`behindOverlay` the popover already asks of it. `Verdict` gained an optional `spotlit` — from
`useVerdictSpotlights`, each figure with its mark, because the hole needs the figure and the arrow
the mark — and `verdictGuide` is the steps; **the passport passes none, which is how its cards never
run it**. **Whether it runs** is `ratingGuideIsDue` (a rating on the screen, and the phone has
answered _never_ — not yet read is not never), whatever the pass's origin; `useRatingGuide` holds the
account's flag in Query under `phonePreferenceKeys.flag` and, on any ending, writes `true` to the cache
(so the next sport in the pass shows none) and raises `ratingGuideShown` in the phone-preferences
store, **per account and kept at sign-out** (per phone until 2026-11-04 — below). The marks and their popovers are unchanged. Suites that
land on _Your rating_ for another reason start from `ratingGuideAlreadyShown()`; the walk is
`theGuideOnYourRating.test`. **Calls made here**: the flag is set when the guide ends rather than
when it opens, so a guide the app was killed under shows again; a tap in the hole counts as _Next_,
as the dim does; _Skip_ is named _Skip the guide_; the bubble takes the content's width. **Per ADR-0198 §1 the guide
adds no screen-reader work**: it moves no focus and its fade does not follow reduced motion — the
review caught a first cut that copied the popover's focus moves. **Not seen
on a device**: the hole's fit around each figure and the bubble's place, on either platform.

**Seen on an iPhone, and fixed (2026-11-04):** the hole was cut a status bar above the level — a
white patch of undimmed paper behind the card, and the bubble over the number it explains — and
the level's and the range's arrows pointed at empty card right of their ⓘ. The first because the
guide measures on the frame it opens on and _Your rating_ wore the native `SafeAreaView`, which has
no inset on its first frame (`TopSafeArea` says why): **the screen now pads both insets from the
provider**, and the guide's suite holds it there. The second because the arrow pointed at the hole's
middle and both figures stretched across their column: **`spotlit` now carries each figure's mark
beside the figure** (`useVerdictSpotlights`, the popover's mark refs when it is handed in), a guide
step's `pointAt` aims the arrow at it, and the level and the range hug their content so each hole
fits its figure. Seen fixed on the user's iPhone the same day.

**The landing draws nothing on the way (2026-11-04, seen on an iPhone).** _Back to {group name}_
showed Home for a frame and then slid the group in over it. The questions are a sibling of the app
under the root's `Slot`, so every way out of a pass mounts the app afresh at `/` — Home — and the
gate's landing, a passive effect calling the shell's tab press and a push, ran only after Home had
been drawn. Now `useEndOnboardingPass` **returns whether a landing is due**, read once from the
pass as the gate mounts (a pass begun with the gate up, at a group's door, is one leaving and lands
nothing), ends the pass in a **layout effect**, and the gate draws nothing of the app while a
landing is due. The landing itself is the shell's `useShellLanding`: **one reset of the navigation
state at the root**, `(app)` › `(tabs)` › the tab's start and the screen on top, made before the
shell is mounted, so the app's first frame is the group — or the passport — with Play or You
beneath it and nothing animating. The reset drops the `(app)` route's params, which held the way
in's nested _go to Home_ and would otherwise pop the new stack straight back to it.
`aPassFromAGroup.test` watches Home for being drawn as the screen on top between the press and the
group. **Not seen on a device yet**: the fix.

**Once per account on a phone, not once per phone (2026-11-04, ruled in-session).** A new account
on the user's iPhone was shown no guide — exactly what ADR-0200 §8 ruled (_a second account on the
same phone never sees it_), and the user ruled it the other way: a new player is shown it once of
their own. The flag keeps its two other properties: **kept at sign-out**, so the same account
signing in again is not shown it twice, and **per phone**, so a new phone shows it again.
`readPhoneFlag`/`raisePhoneFlag` take the account, its key is `raketa.phone-flags.{account}.{flag}`,
and `phonePreferenceKeys.flag(account, flag)` carries it in memory. `useRatingGuide` **observes**
`/users/me` (never stale) for the account rather than reading it once from the cache as the other
preferences do: the questions are up with nothing else holding it, and can outlast the cache's five
minutes. The old key named no account and nothing reads it now, so every account on a phone that
raised it is shown the guide once more. `ratingGuideAlreadyShown(account?)` raises it for the gate's
player. **Owed from a root session**: ADR-0200 §8's _per phone, not per account_ and its
consequences line, and ADR-0188's table note.

**The level's bubble stands beside it (2026-11-04, the user's call from an iPhone screenshot).**
After the arrow was aimed at each ⓘ, the level's step still read wrong: its ⓘ is at the top of the
head, over _3,39_, and the range line sits three points under the number — the bubble under the
hole cut that line in half, and its arrow, under the ⓘ's column, landed between _4,26_ and _likely
range_. An arrow close to the ⓘ from below would cover the number, and over the hole there is no
room under the status bar. **`verdictGuide` marks the level's step `besideMark`**: the bubble stands
right of the hole out to the gutter, over the ring (the third step's, dimmed), its arrow on its left
edge level with the ⓘ, and the count over _Skip_ / _Next_ because it is narrow. Under
`size.guideBesideMin` (180) of room — a phone under about 355pt wide — it stands under the hole as before. The
range and the ring keep their bubbles under them. `verdictGuide.test` holds which step asks.
Seen working on the user's iPhone the same day.

**A notice is a third door into a pass of one sport** ([#758](https://github.com/Raketa02/Raketa/issues/758)):
_Level asked_ — a friend wants to play the sport with you — opens its questionnaire through
`useAddASport(FROM_HOME)`, held by `notifications`' `useOpenNotice`. Home is the origin because a
notice names no group to go back to, so every way out of the pass lands on Home, the pass's usual
return for a run reached with no group ([`notifications.md`](notifications.md)). **`rate` takes an
`onError`**: the passport and a group's card draw the hook's `error` beside their chips, and a notice
has nowhere to draw it, so it is told of a failed start — `sport_already_rated` among them, for a
player who got the Level since the ask — and says so as a toast.

**Once the gate's read has failed, the gate is never blank until one is answered** (2026-11-07).
_Pending_ draws nothing, which is right for the moment one read takes and wrong for anything
longer — and Query reports a read with no data that starts again as _pending_ with no error, so
the gate drew nothing through every automatic retry and through the attempt _Try again_ started.
On the harness's clock a server that never answers left the screen empty for 49 seconds — three
fifteen-second timeouts and the backoff between them — after a fifteen-second splash. Now
`useEntryDecision` keeps the read's last failure until an answer arrives (adjusted while
rendering, and seeded from the cache, so the launch's own failure — which `auth`'s
`fetchCurrentUserAtLaunch` leaves there — is the gate's first answer), and `failed` carries
**`trying`**, an attempt in flight, which `EntryUnavailableScreen` draws as a busy _Trying again…_
that takes no second press. A failed attempt says so at once rather than after the retries.
**Offline still comes first**: a read that failed and is now paused for the connection resumes
by itself, so it says _Waiting for a connection_, amber, with no button. A launch on a dead
connection is now at most five seconds of splash and then this screen. **Not seen on a device.**

## A friend's ask for a level on Home (#765)

**A pass that rated a sport tells the gate which.** [#765](https://github.com/Raketa02/Raketa/issues/765)
gives `useEndOnboardingPass` a third argument, `onRated`, called in the same layout effect that ends the
pass — before the shell is drawn — with the sports the ended pass rated (`rated` on the pass, recorded
by the result screen), whatever its origin. Every level is got inside a pass and every pass ends at
the gate, so that is where a level got reaches reads this feature cannot name: the gate hands the
sports to the shell, which drops Home's ask cards in them and re-reads Home and the bell.

**A door about one sport asks whether that sport's run is left halfway** (`useQuestionLeftAt`): every
unfinished run (`onboardingKeys.runsInProgress`, a key **under** `runInProgress`, so every start,
answer that ends a run, completion and abandonment reaches it by prefix — `findRunsInProgress`, the
same one request) and that run's own step, counted as `levelDoor` counts it. Home's ask card reads it
for **Carry on** and _You're on question 5._ It is `undefined` until a run is known — none, in flight,
or unreadable — because that door's start and its Carry on are one act (`useAddASport`, which hands an
unfinished run back), so unlike the level door it draws its start at once.

## Rankings' Get your level (#775)

**A pass has a fourth origin, Rankings** ([#775](https://github.com/Raketa02/Raketa/issues/775); the
rankings mechanics §9; ADR-0200 §5's _a pass ends where it began_). `PassOrigin` gained
`{ kind: 'rankings', sport }` (`fromRankings`), begun by the page's _Get your {sport} level_ through
`useAddASport` like the passport's chip — one sport, at its question route. `stopDestination` answers
`rankings` whatever the pass produced, the last _Your rating_ says **_Back to Rankings_** (a call:
§30 writes nothing for it), and `returnOf` hands the gate `{ kind: 'rankings', sport }` — the sport
the page was on, rated or not — which `(app)/_layout` lands as Rankings on that sport with Home
beneath. `DoorOrigin` is now _Home or a group_ by inclusion rather than _not the passport_: Rankings
opens no picker, so `LEVEL_DOOR_COPY` owes it no line. **Not seen on a device**: the landing.
