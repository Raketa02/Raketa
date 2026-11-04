# onboarding — the two parts and the entry gate

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
lays the You tab down with the passport pushed over it, the shell's own move, so _back_ from the
passport goes where it came from. The gate's _resume_ branch is unchanged, so a run begun from
the passport and deferred is resumed on the next cold launch as a welcome pass and ends the way
any resumed run does — ADR-0179 names that as a consequence. **Not seen on a device**: the frame
between the gate mounting the Now tab and its effect laying the You stack down, and whether the
passport's push animates in over the tab.

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
`rated`; none when nothing was). `(app)/_layout` lays Play down and pushes `groups`'
`groupReturnRoute`, so _back_ is the Groups list; the page opens on that tab and stands on that
sport the way a notice's card does, never saving it as a pick. **_Your rating_'s words moved to
`resultPresentation`**: mid-pass _Rate {next}_ and _Done for now_, unchanged; on the last sport
_Back to {group name}_ for a group pass and _See your ratings_ for the rest. The result **route**
asks for the name — `useReturningGroup`, then `groups`' `useGroupName`, the page's own read under
its key — and hands it in; while it is unread the control says _Back to the group_. **Two doors
begin a group pass.** `useAddASport(from)` takes its origin: the passport hands
`FROM_THE_PASSPORT`, and the official group's card (`AddSportCard`) its group and the tab to come
back to — the page its own, _Post a game_ Fill in (where it turns the page under it, and where every
way back from it lands), Members the tab the page beneath it is on. And **the picker takes one from
its route**: `/sports?groupId=…&tab=…`, checked by `groups`' `parseGroupPlace`, anything else being
onboarding's own picker. Nothing in the app opens it yet; it is the seam #730's door calls. The
picker now begins its pass **on the start's success**, as the chip does, so a failed start from
inside the app leaves no pass behind. **The card's buttons say _Rate Padel_**, as the issue, the
PRD and ADR-0200 §3 quote them and as the passport's chip says it; _Add Padel_ was the wording of
a pass that ended on the passport. **Calls made here**: a pass from Members returns to the page,
not to Members; a pass from _Post a game_ returns to Fill in, not to _Post a game_. **Not seen on a
device**: the frame between the gate mounting Home and the group's page pushed over Play.
