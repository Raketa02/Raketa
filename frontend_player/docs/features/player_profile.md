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
response said nothing_, which is not `allowed` — the mapper collapses it toward silence, and a
verdict this build has no words for is collapsed the same way.

**The gender step says what narrowing costs, at the moment of the press.** The preference
is a **mutual** gate: setting _Women only_ does not only filter what a player sees, it hides
them from every man — including men who searched for anybody. That half is the one nobody
would guess, and **learning it from an empty inbox is not acceptable**, so the note is
rendered the instant a narrowing option is chosen and goes away when it is widened again.
The rule that decides whether there is a cost is `gender.reachOf`; the sentence is
`genderPresentation`'s. The answer about the player is **required and never pre-selected** —
_Prefer not to say_ is a choice somebody makes, not a default given on their behalf — while
the preference beside it opens at _Anyone_, which is the value every profile already
carries. **Neither value ever comes back out of the API** (ADR-0096 §6), so this step is the
only surface in the app either one is ever seen on.

**The consent step's copy is frozen and versioned.** `optInPresentation.ts` owns every
sentence the Proposals opt-in card shows, together with the `copy_version` stamped beside
the answer in the draft — consent gathered against one sentence is not consent to a
different one, so re-wording that card is a **new version with the old one retained**,
never an edit. It is the only file in this app whose strings are evidence. It stands at
**`proposals-opt-in.v3`**, which rewrote two of the three promises and the scope note and
moved that note above the card; `v2` dropped the line under the title, and both it and `v1`
are retired and kept in the same file, because a version identifier with no record of what it
named evidences nothing.

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
an OS prompt. **A blank availability grid**: the week has a floor of one cell since
ADR-0102, so silence about when somebody plays is asked for rather than scored as a zero —
step four already refuses to continue on one, and this is the same rule read at the end.
**A photo still going up**: uploads outlive the step that started them, and the
body names photos by the ids the server gave back, so committing mid-upload would silently
drop a picture the player watched arrive. That one asks for nothing and opens itself.

A failed commit whose `code` names an answer — `availability_grid_empty` today — is drawn as
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
way back and says `OUT_OF_DATE_GAP`. Nothing is editable after the commit — the intro follows
the tags and the photo, and becomes editable the day all three do (ADR-0170 §5). **Not seen on a
device**: whether four lines is the right ceiling for the box, whether the counter sits right
under it, and whether the action bar rises cleanly over the iOS keyboard, are the author's to
check.

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
makes the next launch a cold start. **Nothing resets**: the deck's held deal stands, the radar's
held reading refetches on its own rule, and the profile surface is invalidated so _In your area_
follows the projection the moment a surface reads it; a failed write is silence, and the next
cold start writes again. A player still in onboarding is never refreshed — the location step is
where their area is being asked for, with a prompt and a sentence, and the step's own read and
tests are untouched. **You** carries the one written trace, `AreaUpdatesNote` — `the-words.md`
§26's _Your area updates each time you open Raketa; it is never finer than about a kilometre._,
static, `tiny` in `muted`, under the profile block and above the account panel — because silent
motion with no written trace is the one thing that would surprise a careful player, and the
kilometre in the same breath is what keeps _updates each time you open_ from reading as
tracking. **Not seen on a device**: the read on a real cold start against the OS, and the
sentence's fit on the tab, are the author's to check.
