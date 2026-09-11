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
once more with the way back one press away rather than trapping a player on step four behind
an OS prompt. **A blank availability grid**: the week has a floor of one cell since
ADR-0102, so silence about when somebody plays is asked for rather than scored as a zero —
step three already refuses to continue on one, and this is the same rule read at the end.
**A photo still going up**: uploads outlive the step that started them, and the
body names photos by the ids the server gave back, so committing mid-upload would silently
drop a picture the player watched arrive. That one asks for nothing and opens itself.

A failed commit whose `code` names an answer — `availability_grid_empty` today — is drawn as
that answer rather than as _try again_, with the control back to the step that takes it: the
commit re-validates every rule a picker enforced, and re-sending the identical body would
fail identically.
