/**
 * The **for-fun** candidate card, in the pool — media-top, with fact rows.
 *
 * The second of the three, and the one that settles what a *card* is here: it is drawn from
 * the same parts as the deck's and it is **not the deck's card**.
 *
 * ## It does not float
 *
 * [#219](https://github.com/Raketa02/Raketa/issues/219) B3 named `.pcard` as *"the deck card
 * **and** the social candidate card"* and ruled the family out of
 * [4.3](../../../../../docs/design-system.md#43-elevation)'s *cards never cast a shadow* — but
 * every clause of that argument reaches the deck alone: *"it animates in, and translates and
 * rotates out under the thumb"*, *"a transient object being manipulated"*. **This is a row in
 * a scrolling list.** So the resolution stands with its scope shrunk to the surface its own
 * reasoning covers: radius 13, no shadow, and the deck card is the only user of `deckCard: 18`
 * and the fourth shadow
 * ([`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §3).
 *
 * The consequence is the one worth having: **the pool draws one shape twice.** Competitive and
 * social are the same card at the same radius with different contents, which is what makes
 * three components cheap rather than three near-duplicates.
 *
 * ## What it draws, and therefore what it will not say twice
 *
 * A level row, a *You overlap* row and the meta line's kilometres — so `LEVEL_FIT`,
 * `AVAILABILITY_OVERLAP` and `DISTANCE` are its drawn set. `PREDICTED_BALANCE` is **not**:
 * this card draws no forecast, and a for-fun evening is not the surface a balance bar belongs
 * on, so the forecast reaches it as a reason line instead.
 *
 * ## The kit's tag row is not built here, and that is a decision
 *
 * §B10 laid out the head row as a name with **inline tags** beside it — `.tag.hot`,
 * `.tag.volt`, `.tag.bad` — and the only one of the three with a vocabulary behind it was the
 * volt one, which this ticket turns into a **sentence** (`CardHead`). What is left has no
 * surface asking for it: [`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md)
 * §5's *Draws* column for this card is the level row, the *You overlap* row and the meta
 * line's kilometres, and §20.3 fixes the body's spoken name with no tags in it. Drawing the
 * candidate's own Social tags anyway would put content on the card that the label cannot
 * announce, which is the half of Part 13 a hidden decoration is allowed and a fact is not —
 * and their pairing already reaches this card **as sentences**, through the two tag terms.
 * The surface that draws tags as tags is `SH.playersocial`, and it is out of scope here.
 */

import { StyleSheet, View } from 'react-native';

import { Button, PressableCard, theme } from '@/shared/ui';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Term } from '../../domain/vocabulary';
import { candidateActionLabel, type CandidateAction } from '../accessibilityPresentation';
import {
  CANDIDATE_ACTION_WORD,
  OVERLAP_ROW_LABEL,
  levelRow,
  metaLine,
  overlapRowValue,
} from '../playerCardPresentation';

import { CandidatePhoto } from './CandidatePhoto';
import { CardHead } from './CardHead';
import { FactRow } from './FactRow';
import { ReasonLine } from './ReasonLine';
import { candidateFacts, evidenceOf } from './candidateFacts';

/** See {@link CandidateCard}'s set: exported by the component that draws these rows. */
export const SOCIAL_CARD_DRAWS: readonly Term[] = ['LEVEL_FIT', 'AVAILABILITY_OVERLAP', 'DISTANCE'];

/**
 * The media slot's shape — a **banner**, and the one number this composition owns.
 *
 * A row in a scrolling list is scanned rather than dwelt on, so the photograph is wide and
 * short: at the deck's 3:4 a single card would be most of a phone, and a pool of twenty would
 * be a pool nobody scrolls. It is the card's own value rather than a token, on §1's rule that
 * the design system holds drawn objects and a feature holds the compositions.
 */
const BANNER_ASPECT_RATIO = 2;

export interface CandidateCardSocialProps {
  readonly candidate: Candidate;
  readonly envelope: SearchEnvelope;
  readonly action: CandidateAction;
  readonly onAction: () => void;
  /** The body's own action — *Why 78?*. */
  readonly onWhyFit: () => void;
}

export function CandidateCardSocial({
  candidate,
  envelope,
  action,
  onAction,
  onWhyFit,
}: CandidateCardSocialProps) {
  const facts = candidateFacts(candidate, envelope, SOCIAL_CARD_DRAWS);
  const overlap = evidenceOf(candidate, 'availability_overlap');

  return (
    <PressableCard style={s.card} onPress={onWhyFit} accessibilityLabel={facts.label}>
      <View style={s.media}>
        <CandidatePhoto
          playerId={candidate.playerId}
          photoUrl={candidate.card.photoUrl}
          box={{ kind: 'media' }}
        />
      </View>

      <View style={s.body}>
        <CardHead
          name={facts.name}
          fit={candidate.fit}
          inclusionReason={candidate.inclusionReason}
        />

        <FactRow value={levelRow(facts.level)} />

        {overlap === undefined ? null : (
          <FactRow label={OVERLAP_ROW_LABEL} value={overlapRowValue(overlap)} />
        )}

        {facts.meta === undefined ? null : <FactRow value={metaLine(facts.meta)} />}

        {facts.reasons.map((line, at) => (
          <ReasonLine key={`reason-${at}`} line={line} />
        ))}

        {facts.concerns.map((line, at) => (
          <ReasonLine key={`concern-${at}`} line={line} variant="concern" />
        ))}

        <Button
          label={CANDIDATE_ACTION_WORD[action]}
          accessibilityLabel={candidateActionLabel(action, facts.name)}
          onPress={onAction}
          size="sm"
          style={s.action}
        />
      </View>
    </PressableCard>
  );
}

const s = StyleSheet.create({
  // The card's own padding goes to the body: media that bleeds to the edges cannot be inset
  // by the surface it bleeds to, and the clip is what gives it the card's corners.
  card: { padding: 0, overflow: 'hidden' },
  media: { aspectRatio: BANNER_ASPECT_RATIO },
  body: { padding: theme.space.md, paddingBottom: theme.space.sm, gap: theme.space.xs },
  action: { alignSelf: 'flex-start' },
});
