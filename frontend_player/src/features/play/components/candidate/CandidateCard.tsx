/**
 * The **competitive** candidate card — a photo panel, an identity row, and one head-to-head
 * band ([#309](https://github.com/Raketa02/Raketa/issues/309)).
 *
 * One of three components over one parts kit, and deliberately **not one component with a
 * `surface` prop**: a single card would carry `surface === …` at nine sites, which is §G3
 * #1's complaint (*"sixty lines of interpolation with eight conditional blocks"*) arriving in
 * a new spelling
 * ([`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §3). After #309 the shapes differ further still: this one has a panel with the Level printed
 * on it, its own identity row, and a band; the social and deck cards are media-top with fact
 * rows, and neither is touched.
 *
 * ## It takes `(candidate, envelope)` and reads no global state
 *
 * That is [#233](https://github.com/Raketa02/Raketa/issues/233)'s fix for the why-fit sheet
 * and the same one §G6 #8 asks for here — *"the Why-fit sheet reads the global sport and mode
 * rather than the card's own"*. Passing the **envelope** rather than a `mode` string is what
 * keeps [`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §2's warning
 * intact: `SearchEnvelope.mode` is null on the deck and `IntentAlignmentEvidence.myMode` is
 * not, and they are supposed to disagree there.
 *
 * **`sportName` is the one thing it takes from the screen**, and it is a prop rather than a
 * field for a reason worth keeping: the Sport is a property of the **search**, not of the
 * person, and putting it on `player_card` would be twenty copies of one fact crossing the wire
 * on every response. `origin.sport` is already held one component up.
 *
 * ## What it draws, and therefore what it will not say twice
 *
 * The band prints **both levels** and draws the **forecast**, and the record block prints a
 * **Player Score** — so `LEVEL_FIT`, `PREDICTED_BALANCE` and `RELIABILITY` are this card's
 * drawn set and none of the three appears as a reason line. The third arrived with the block
 * ([#312](https://github.com/Raketa02/Raketa/issues/312)), which is exactly what
 * [`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §5 booked when it
 * wrote *"`RELIABILITY` joins them the day the Player Score block prints and not before"*.
 *
 * **The set is unconditional and the block is not**, and the two read off different fields: the
 * block prints `player_card.player_score`, the **published** figure, where the filtered sentence
 * is written over `ReliabilityEvidence.score`, the engine's. They are the same number by
 * ADR-0140 and they are two reads, deliberately — *"taking the card's figure off the engine's
 * record would make what a player is shown a consequence of whatever the reliability term
 * happens to carry"*. In one request they answer together, so a fired term without a published
 * score is not a state the contract produces; if it ever were, the card would state the fact
 * nought times, and the fix would be the second read rather than a fallback that borrows the
 * engine's number.
 *
 * `DISTANCE` is not in the set — this card draws no distance row, which is why a reason line
 * on it can never come up empty, and the block did not touch that: the surviving set is one
 * term smaller and `DISTANCE` never stands down.
 *
 * **The Level is printed twice**, hugely on the panel and again on the right of the band. That
 * is the designs' choice and it is accepted: the panel's is the card's **identity** — what this
 * person published, drawn whatever fired — and the band's is one side of a **comparison**
 * computed against the other. §10 forbids a reason line restating a value the card renders, and
 * that rule is about the two registers rather than about the pixel count: the fact is **said
 * once**, in `levelRow`, and the reason line for it is filtered off exactly as before.
 *
 * ## Two borders were asked for. One is drawn, and the other is still refused
 *
 * The designs put a **coral** border on every competitive card and a **green** one on *wants
 * to play you*. They are not one question, and they did not get the same answer:
 *
 * - **Coral, on every card — still refused.**
 *   [5.1](../../../../../docs/design-system.md#51-card--the-workhorse) already spends a coral
 *   border on a card: it is the **pressed** state. A permanent one is every row in a scrolling
 *   list drawn as though a finger were on it, and
 *   [1.2](../../../../../docs/design-system.md#12-one-accent-used-sparingly) is *when everything
 *   is accented, nothing is*. Find a game's own entry control refused the same 2pt coral outline for the same
 *   reason one screen earlier.
 * - **Green, on the lifted card — drawn**, in `voltStroke`
 *   ([#310](https://github.com/Raketa02/Raketa/issues/310)). #309 refused it and asked for a
 *   ratify or an overrule; the ordering ticket restates it twice — *"the yellow-green tag and
 *   the green border travel with the card wherever it lands"* — and that is the overrule. What
 *   survives from the refusal is its arithmetic, which was never about whether the border was
 *   wanted: **volt** is 1,25:1 on `surface` and 1,12:1 on `paper`, so a border drawn in it is a
 *   line nobody sees, and the 2026-08-31 amendment refused *"a 2pt border on the interest
 *   card"* on exactly that. So the stroke is volt's **second value** rather than volt — the
 *   relationship `coralInk` has to `coral` — at 4,01 on `surface`, 3,58 on `paper` and 3,07
 *   against the `line` border it replaces, all derived in `Tag.test.tsx`.
 *
 * **Part 13 is discharged by the tag and never by the border.** *"A border carries no word and
 * this signal has one"* was the 2026-08-31 conclusion and it is still true — which is why the
 * outline is bound to `tag?.variant === 'volt'` rather than to `inclusionReason`: the border is
 * the second copy of a cue that is already a word, and it cannot appear where the word does not.
 *
 * ## Three accessibility elements, and the third is the one that became visible
 *
 * §20.3 fixed the card at **two**: the body, whose action is *Why 78?*, and its primary button.
 * The designs draw *Why 78?* as a secondary button beside the primary, so there are three. The
 * body **keeps** its press rather than becoming a labelled group: §20.1's rule is *one element
 * per action*, and a body with no action would be an element that rule cannot account for —
 * where a big target and a small named one for the same act cost nothing but a swipe. What
 * changes is the count, and §20.3 is updated rather than left wrong.
 *
 * ## The buttons know nothing about sending
 *
 * The primary takes `onAction` and a code, which is what lets one shape serve *Add* and
 * *Challenge*. `SH.propose` and the send itself are `features/challenges/`'
 * ([`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §8).
 */

import { StyleSheet, View } from 'react-native';

import { Button, FitPill, PhotoPanel, PressableCard, SocialTagRow, theme } from '@/shared/ui';

import { stakeOnACard } from '../../domain/atStake';
import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Term } from '../../domain/vocabulary';
import {
  candidateActionLabel,
  whyFitControlLabel,
  type CandidateAction,
} from '../accessibilityPresentation';
import { socialTagOverlap } from '../../domain/socialTagOverlap';
import { CANDIDATE_ACTION_WORD, candidateTag } from '../playerCardPresentation';
import { whyFitControlWord } from '../whyFitPresentation';

import { HeadToHeadBand } from './HeadToHeadBand';
import { IdentityRow } from './IdentityRow';
import { ReasonLine } from './ReasonLine';
import { RecordBlocks } from './RecordBlocks';
import { StakeBoxes } from './StakeBoxes';
import { candidateFacts, evidenceOf } from './candidateFacts';

/**
 * What this card draws for itself, and therefore drops from its reason list.
 *
 * **Exported by the component**, because the set is a statement about what this component
 * draws and moving it into the selector is the one place it could go stale silently
 * ([`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §5).
 */
export const COMPETITIVE_CARD_DRAWS: readonly Term[] = [
  'LEVEL_FIT',
  'PREDICTED_BALANCE',
  'RELIABILITY',
];

export interface CandidateCardProps {
  readonly candidate: Candidate;
  readonly envelope: SearchEnvelope;
  /** `sportLabel(origin.sport)` — the search's Sport, drawn on the panel. See the module note. */
  readonly sportName: string;
  /**
   * `courtSeatCount(origin.sport)` — **how many people stand on this court**, and the whole of
   * what decides whether the stake boxes are drawn
   * ([#312](https://github.com/Raketa02/Raketa/issues/312)).
   *
   * The screen's fact rather than the card's, exactly as `sportName` is and off the same Sport:
   * one value for the whole list. It is a seat count and never a `singles` flag, because the
   * count already exists — `Court`'s own coordinates, read by every other singles-or-doubles
   * decision in this feature — and a second answer to a settled question is a second answer
   * that can disagree. The rule over it is `domain/atStake`'s.
   */
  readonly seats: number;
  /** What the primary button does. A code, so a third surface gains a word or does not build. */
  readonly action: CandidateAction;
  readonly onAction: () => void;
  /** The body's own action, and now a button as well — *Why 78?*. */
  readonly onWhyFit: () => void;
  /**
   * Whether this row wears the coral tag.
   *
   * **The ordering rule's answer** ([#310](https://github.com/Raketa02/Raketa/issues/310)),
   * never this card's: exactly one row on screen has the highest Fit, and a component handed
   * one candidate cannot know which. Defaulted to `false` so the card is honest until the rule
   * that decides it is wired — a tag drawn on every card is worse than no tag at all.
   */
  readonly bestMatch?: boolean;
}

export function CandidateCard({
  candidate,
  envelope,
  sportName,
  seats,
  action,
  onAction,
  onWhyFit,
  bestMatch = false,
}: CandidateCardProps) {
  const tags = socialTagOverlap(candidate);
  // Both taken here and handed down twice — once to be drawn and once to be spoken — which is
  // what keeps the two registers reading one value. `player_card` already carries the three
  // record fields, so the card's subject *is* the record block's facts.
  const stake = stakeOnACard({ atStake: candidate.atStake, seats });
  const facts = candidateFacts({
    candidate,
    envelope,
    drawn: COMPETITIVE_CARD_DRAWS,
    socialTags: tags,
    record: candidate.card,
    stake,
    // The panel is this card's alone, so the two fields behind the ON COURT mark are handed
    // over here and declined by the other two cards — `record`'s shape, for `record`'s reason.
    photo: candidate.card,
  });
  const levelFit = evidenceOf(candidate, 'level_fit');
  const balance = evidenceOf(candidate, 'predicted_balance');
  const tag = candidateTag({ inclusionReason: candidate.inclusionReason, bestMatch });

  return (
    /* The border is bound to the **tag it accompanies** rather than to the code beneath it, so
       the two cannot drift: the green outline appears on exactly the card whose handle says
       *Wants to play you*, and it travels with that tag through every re-sort because both are
       read off this one candidate. Part 13 is satisfied by the tag, not by the border — the
       colour is never the cue, it is the second copy of a cue that is already a word. */
    <PressableCard
      style={s.card}
      marked={tag?.variant === 'volt'}
      onPress={onWhyFit}
      accessibilityLabel={facts.label}
    >
      <View style={s.body}>
        <PhotoPanel
          playerId={candidate.playerId}
          photoUrl={candidate.card.photoUrl}
          level={candidate.card.level}
          sportName={sportName}
          onCourt={facts.onCourt}
        />

        <View style={s.column}>
          <IdentityRow name={facts.name} tag={tag} />

          {/* On its own row, under the name. The designs' *"2,95 · 0,24 above you"* beside it
              is struck: the band below prints the gap as two figures over a bar, and the sheet
              behind *Why 78?* is what explains the number the pill carries. */}
          <FitPill fit={candidate.fit} />

          {facts.reasons.map((line, at) => (
            <ReasonLine key={`reason-${at}`} line={line} />
          ))}

          {facts.concerns.map((line, at) => (
            <ReasonLine key={`concern-${at}`} line={line} variant="concern" />
          ))}
        </View>
      </View>

      {/* Full width, under both columns: it is a comparison between two people rather than a
          fact about the one in the panel, and at the column's width the bar's own segment
          labels would not fit — which is the size floor #219 B4 put on `sm`. */}
      <HeadToHeadBand levelFit={levelFit} balance={balance} />

      {/* Three boxes across, then two — what the platform watched this person do, and what a
          counted game against them would move. Each hides itself where its fact is absent, so a
          card for a brand-new player draws neither row and is a correct card. */}
      <RecordBlocks record={candidate.card} />
      <StakeBoxes stake={stake} />

      {/* Full width, under the band, for the band's own reason: six tags do not fit in the
          column beside the photo panel, and a row that wrapped four times there would push the
          card past the height a list of them can be read at. */}
      <SocialTagRow row={tags} />

      <View style={s.actions}>
        <Button
          label={whyFitControlWord(candidate.fit)}
          accessibilityLabel={whyFitControlLabel(facts.name, candidate.fit)}
          onPress={onWhyFit}
          variant="secondary"
          size="sm"
        />

        <Button
          label={CANDIDATE_ACTION_WORD[action]}
          accessibilityLabel={candidateActionLabel(action, facts.name)}
          onPress={onAction}
          size="sm"
        />
      </View>
    </PressableCard>
  );
}

const s = StyleSheet.create({
  // 12 / 12 / 9 — the 3pt grid's reading of the prototype's 11 / 11 / 9 (§G1). The card is a
  // column of three blocks now, so the gap between them is the card's rather than each one's.
  card: { paddingBottom: theme.space.sm, gap: theme.space.sm },
  body: { flexDirection: 'row', gap: theme.space.md },
  column: { flex: 1, gap: theme.space.xs },
  // It wraps, because both labels grow with the OS font setting: *Why 78?* beside *Add to the
  // court* fits the narrowest phone at the system size and not at every size above it, and a
  // row that overflows puts the primary action off the edge of the card.
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: theme.space.xs,
  },
});
