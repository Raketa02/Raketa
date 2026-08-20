# ADR-0043 — Opening a court to strangers is the private path's commitment

- **Status:** Accepted
- **Date:** 2026-08-20
- **Narrows:** [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) — the private path has
  no commitment *deadline*, but it does have a commitment *act*

## Context

[ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) and
[The leaver](https://github.com/Raketa02/Raketa/issues/7) concluded that a private court has no
commitment deadline at all: *"a private court is bought at booking, so that moment has already
passed before the first share is paid."* The reasoning is sound and the conclusion was too
strong. On an open match, commitment is a **clock** — the moment a held court stops being held
and becomes bought. On a private court that moment is behind us. But there is still a moment
after which the owner may not undo what they have done, and it is an **act**: letting a stranger
in.

**One word was doing two jobs, and it hid the shape.** "Private" was being used for two
independent axes:

- **How the court was obtained** — bought outright up front, versus held speculatively by the
  hold ladder and firmed up as the match fills. Fixed at booking.
- **Who may buy in** — the owner's own people, or anyone on Raketa.

Opening a court is a change on the second axis only. It is not a conversion into an open match,
and treating it as one drags the entire open-match rulebook onto a court that rulebook cannot
describe. `3.1` already says so: *"that player's enrolled match is the private court, not an
open match."*

## Decision

**Opening a private court to the marketplace is the private path's commitment event, and it is
one-way.** Two doors shut at two different moments, deliberately:

- **The court can never be closed again**, from the instant it is opened. The owner cannot
  un-open it, cannot withdraw a remaining vacancy once another has sold, and cannot remove
  anyone who joined.
- **The owner's ordinary cancellation right survives until the first stranger pays.** Until then
  the club's own cancellation window applies unchanged and every payer is refunded to their
  original method. The instant a stranger's money lands, that right is gone permanently, and the
  owner is liable for the court whatever happens next.

The moments are split because *"the court can never be closed again"* exists to protect the
people who joined. With nobody joined it protects nobody, and collapsing the two would leave an
owner paying in full for a court that was offered and refused — a purely destructive outcome
that costs the club nothing, the platform nothing, and the owner everything.

**A friend joining does not commit the owner; a stranger does.** The lock protects someone who
trusted the platform rather than the owner. A group of friends who all want to cancel is one
conversation and one decision, which is precisely what a club's cancellation window is for; a
stranger has nobody to have that conversation with. Once a stranger has paid the lock is
permanent in practice as well as in rule, because a stranger on a private court can only
recover their money if someone takes their seat — there is no state in which they all quietly
exit and the owner's freedom returns.

**Before a court may be opened, every seat is either paid or empty.** A held seat — a name with
no money behind it — must be paid for or vacated first. This makes *"who must consent to this"*
a question with an exact answer, since consent counts paid players only, and it stops an owner
selling a seat somebody is still expecting to take.

Four things that follow, each of which a later session would otherwise reach for:

- **The court stays private permanently**, even when every original participant has gone and four
  strangers hold the seats. The open-match rulebook is about a court **nobody has bought**: a
  commitment deadline is the moment a held court becomes a bought one, and the half-price rescue
  fill balances because the newcomer's money *is* the leaver's refund. Neither has anything to
  grip on a court paid for in advance — a 15 zł fill against a 30 zł refund is 15 zł short with
  nobody left to cover it. This is why
  [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) ruled the half-price tier out on
  private courts, and an owner leaving does not change the sum.
- **The platform never discounts a seat on an owner's behalf.** The half-price fill exists to
  stop a court going to waste; on a bought court nothing goes to waste, and the only thing a
  discount would decide is that the owner should recover half of what they might have recovered.
  They cannot refuse.
- **An opened seat enters the same recommendation pool as every other seat, ranked by fit alone.**
  Boosting it means showing a player a match that suits them *less* in order to rescue somebody
  else's money, which ends the one property that makes the Now screen readable. The owner's
  protection is that they were told plainly what they were taking on.
- **A converted court accepts any level, and its owner gets no say over who joins.** Raketa has
  no admission gate anywhere — a **target band** exists but only scores how well a match suits a
  viewer. Giving an opened court's owner a right to turn applicants away hands back, through a
  different door, most of the control this ADR removes: they could not remove a joiner, but they
  could decline every candidate until the seat died.

**Booking with split payment and opening every seat the same afternoon is allowed.** What it
buys is certainty — an open match's court is provisional and may never firm up, and at 14:00 on
a Saturday it very often will not. The owner pays for that certainty with personal liability,
which is the deterrent against treating a private booking as a free speculative open match. The
awkwardness is that we make them claim a group they do not have; that is a naming problem, and
its fix is a third booking option, not a permission.

## Consequences

**Easier**

- *"You own this court to the end"* is one sentence, true from the first stranger's payment
  onward, independent of who is on court and whether the owner plays.
- A joiner's deal never changes after they buy: what they agreed to cannot be improved or
  worsened by a fourth party's later decision.
- The two axes make several questions dissolve rather than need answering — what a court "becomes"
  when its owner leaves, whether open-match refunds follow, who inherits the reservation.
- [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md)'s *"the owner cannot leave"* survives
  intact and reads better: the refusal was never about the seat, it was about the court.

**Harder**

- **An owner who opens a court and is not injured is committed for weeks.** A booking made a
  month out and opened on day one locks at the first payment, and nothing but a club-side failure
  releases it.
- **The owner loses control of a court they are paying for.** They cannot choose their company,
  cannot keep a seat empty, and cannot decline a mismatched applicant — while remaining the only
  person liable. Accepted because every one of those controls is a way to shed the risk onto
  someone who bought a seat in good faith.
- **A permanent, irreversible act sits behind an ordinary-looking button.** The screen has to
  carry the weight the model no longer will, and it is the first place on the player app where
  copy is the only safeguard.
- **The third booking option is named and not built.** Until it exists, the honest use of
  split-and-open is reachable only by misrepresenting why you chose split.
