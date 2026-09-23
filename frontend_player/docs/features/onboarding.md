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
is result → **done** → the eight steps → the commit → data → the app. The _pass_ routes as far
as the summary and no further (`nextDestination`: _is there anything to account for_), and
the **done screen** reads whether a Player profile is still owed and either enters the second
part or continues to the data screen — one fact, read once, on the screen that acts on it. A
player who is already set up — one resuming a run they left behind — passes straight through.
The summary comes before the eight steps rather than after the commit, because it is what a
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
