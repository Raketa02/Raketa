# ADR-0198 — The player app is not built for screen readers, for now

- **Status:** Accepted — **§1 narrowed 2026-11-16 by
  [ADR-0205](0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)**
  §8 (PRD [#810](https://github.com/Raketa02/Raketa/issues/810)), for three things the product owner
  asked for by name: Home's FOR YOU lines open and close at once under *Reduce motion*, *Needs your
  answer*'s title takes the screen reader's focus, and each line says whether it is open. A dated
  note marks §1.
- **Date:** 2026-10-25
- **Amends [ADR-0012](0012-player-app-design-system.md)'s *Consequences*.** Its line *"The app is
  AA-conformant, thumb-reachable and screen-reader navigable from its first screen"* now holds for
  contrast and touch only. **For now the app is not built for screen readers**, or for the phone's
  accessibility settings. The rest of ADR-0012 stands.
- **Pauses, for new work, the rules that ask for screen-reader or accessibility-setting support:**
  the player design system's §0.4 *Screen readers* requirement, Part 13's rules of that kind
  (*every toast announces* by name), the *Accessibility* paragraph of the player app's
  [`docs/architecture.md`](../../frontend_player/docs/architecture.md), and
  [`the-words.md`](../specs/matchmaking/the-words.md) §20's live regions and announcements. Their
  text stays where it is, marked paused, so it can come back as written.
- Ruled by the product owner on 2026-10-25 from story S-16A,
  [#713](https://github.com/Raketa02/Raketa/issues/713#issuecomment-6400470479): F-FILL-1.2
  (*Keep*) and F-FILL-64.1 (*Defer*). Settles [#718](https://github.com/Raketa02/Raketa/issues/718).

## Context

Story S-16A walks Marta's *Book it now*. She swipes, *Booking in 10 s · Undo* counts down, and at
zero four 40 zł holds land on four cards. Two of its findings were about players who use the phone
through a screen reader:

- **F-FILL-1.2: the ten seconds are fixed.** Nerea uses TalkBack and reads slowly. By the time she
  has found *Undo*, the court is booked and four shares are held. W3C's *Timing Adjustable*
  (WCAG 2.2.1, level A) asks that a person can turn a time limit off, lengthen it or adjust it,
  unless another way does the same thing. A free leave before the cut-off doesn't, because by then
  the court is booked and the others are told. Android has a *Time to take action* setting that
  Google's own Undo messages follow, and the two money apps found that hold a payment behind an Undo
  default to 15 seconds and let the person change it or turn it off (Monzo up to 60):
  [Monzo](https://monzo.com/blog/undo-payments) and
  [Wealthsimple](https://help.wealthsimple.com/hc/en-ca/articles/49925420385307-Undo-an-Interac-e-Transfer). The options were to follow the phone's setting, to
  let a player lengthen the ten seconds, or to keep them.
- **F-FILL-64.1: Undo is never spoken.** When the count starts, the app announces *"Booking in 10
  seconds. You can undo it."* Pressing *Undo* says nothing. A VoiceOver user can't tell a booking
  taken back from one still on its way until *It's a game!* does or doesn't come. It was filed as a
  fix, settled by W3C's *Status Messages* (WCAG 4.1.3).

The product owner ruled both from one premise: **the app is used through ordinary touch.** The ten
seconds stay fixed for everyone (fifteen was also rejected), and *Undo* stays silent.

That premise contradicts ADR-0012, which promised an app *"screen-reader navigable from its first
screen"*. It also contradicts the design system built on that promise. §0.4 calls screen readers
non-negotiable, because *"VoiceOver and TalkBack are the only way some players use the app"*, and
Part 13 has every toast announce. Left standing beside the ruling, those lines would make the
instruction files disagree with the decision. An agent would pick one at random, and the next
story's fix prompt would again call a spoken line settled.

**What exists today**, built under ADR-0012:

- Every pressable primitive in `shared/ui/` requires a name as a prop, and lint rejects an unnamed
  `Pressable` in games and proposals (`pnpm test:labels` proves the rule still fires). The tests
  find controls by those names: `getByLabelText` appears 888 times in 73 test files.
- Every toast announces itself, and a few components announce a change of their own, the count's
  start among them.
- Sheets are modal to a screen reader. The three buttons under the deck's card do what a swipe does,
  so a screen reader, which consumes the drag, can still answer a card. Reduced motion is
  honoured, and text scales with the phone's size setting.
- Contrast is AA or better at every size used (design system §2.5), and every target is at least
  44 × 44 pt.

**Rejected on the way:**

- **Keep ADR-0012, and build both fixes.** The product owner chose not to. The deck stays simple,
  and nothing is built for a way of using the app it isn't designed around now.
- **Remove what exists.** Taking names off pressables or deleting the announcements would cost work
  and buy nothing. The names also carry the test suite, and they are what makes support possible
  to bring back.
- **Rule each finding alone, with no record.** A *Keep* on one finding and a *Defer* on the other
  would leave ADR-0012's line standing, and every later story would raise the same findings again.

## Decision

### 1. For now, nothing new is built for screen readers or the phone's accessibility settings

No new work is done for VoiceOver, TalkBack or a phone accessibility setting: Android's *Time to
take action*, reduced motion, text size and the like. This holds for new screens and for changes
to existing ones. No new announcement, no spoken
confirmation, no timing that follows a setting, and no screen-reader test is asked of them.

A new screen built from the existing primitives keeps whatever those already do: a name on each
pressable, modal sheets, reduced motion and scaled text. Nobody adds to it.

**Contrast (AA) and touch targets (44 × 44 pt) are not part of this pause.** They serve everyone who
looks at and touches the phone, and stay in force.

> **Narrowed 2026-11-16 by [ADR-0205](0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md) §8**, for three things the Home refactor
> grilling ruled by name (Q11, Q39), and only these: **FOR YOU's lines open and close at once** under
> the phone's *Reduce motion*; **Needs your answer's title takes the screen reader's focus** when the
> sheet opens; and **each line says its title, its count and whether it is open**. No announcement,
> no spoken confirmation and no other setting is added, and the rest of the pause stands.

### 2. Nothing already built is removed

The names on pressables, the announcement *"Booking in 10 seconds. You can undo it."* and the app's
other announcements stay. So do the buttons a screen reader answers a card with, the modal
semantics, and the honouring of reduced motion and text size. The paused design-system rules
stay in place, marked paused.

### 3. Every pressable still carries a name

The rule that every pressable primitive requires a name stays, lint included, and a new pressable
gets a name like any other. It costs one prop, the tests find controls by it, and it is the floor
the day support returns.

### 4. The ten seconds of Undo stay fixed for everyone, and Undo stays silent

Every action that moves money waits ten seconds behind *Undo*, the same for every player and every
phone. It does not follow *Time to take action*, and no player can lengthen it or turn it off.
Pressing *Undo* says nothing.

### 5. What comes back when support returns

Support returns through a later record, not a code change. When it does, these come back with it:
F-FILL-1.2's options (follow the phone's *Time to take action*, or let a player lengthen or turn off
the ten seconds), F-FILL-64.1's spoken *Undo*, and the two paused design-system rules, as written.

## Consequences

**Easier**

- Story grillings stop offering VoiceOver, TalkBack or *Time to take action* options, and the deck
  stays as simple as the product owner wants it.
- A new screen costs less: no announcement queue to reason about and no spoken line to test.
- The decision, ADR-0012, the design system and the app's agent instructions say the same thing.

**Harder**

- **W3C's timing rule (WCAG 2.2.1, level A) is knowingly not met.** The ten fixed seconds sit on the
  one action that moves money. A slow screen-reader user can book a court and hold four shares
  before reaching *Undo*, and the only way back is a leave, which is not the same act: the court is
  booked and the others are told.
- **The European accessibility law reaches the app once Raketa stops being a microenterprise.**
  Directive (EU) 2019/882 covers e-commerce services, mobile apps included, from 28 June 2025.
  Poland's act (Dz.U. 2024 poz. 731) does the same and asks for compatibility with assistive tools.
  Both exempt a microenterprise's services: fewer than 10 staff, and at most €2 million in annual
  turnover or balance sheet. Above that, a player app that takes a consumer's payment for a seat is
  an e-commerce service. A provider that doesn't meet the requirements can be fined up to ten times
  the average monthly wage, capped at 10 % of the previous year's turnover (art. 73). This deadline
  arrives through headcount or revenue, not a ticket, so whoever grows the company has to reopen
  this record before it passes either line.
- **A player who uses a screen reader is on their own.** The names still reach them, but nothing
  new is checked with a screen reader, so a new screen may be unusable with one, and nobody will
  notice because no test asks.
- **Coming back costs more the longer the pause lasts.** Every screen built in the meantime is a
  screen to audit later. The paused rules stay written, which helps, but the debt grows with every
  screen.

**Neutral**

- **The day support returns, two findings come back with it** (§5): F-FILL-1.2's options for the
  ten seconds, and F-FILL-64.1's spoken *Undo*. They are deferred, not dropped.
- This record is about the player app. The club website and the public site have their own
  standards ([ADR-0187](0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
  §6) and are not touched by it.
- The rest of ADR-0012 stands: AA contrast, 44 × 44 pt targets, *never colour alone*, and a name on
  everything tappable. This record narrows one line of it. It doesn't reverse the system.
