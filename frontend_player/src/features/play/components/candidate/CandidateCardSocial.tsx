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
 * ## The two interest tags are drawn here as they are on the competitive card
 *
 * §B10 laid out the head row as a name with **inline tags** beside it — `.tag.hot`,
 * `.tag.volt`, `.tag.bad` — and the only one of the three with a vocabulary behind it was the
 * volt one, which this card turned into a **sentence** under the name until
 * [ADR-0169](../../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8 put the two-word tag back where the sentence stood: *Wants to play you* off the admitting
 * code, and *You said yes* off the reader's own list, **both tags on both card styles**. The
 * words and the precedence are `candidateTag`'s, and the green border travels with *Wants to
 * play you* onto this card too — it is the tag's second copy, and it goes where the tag goes.
 * What this card still does not draw is the coral *best match*: that is a fact about a list,
 * and a for-fun pool has never claimed one ([#310](https://github.com/Raketa02/Raketa/issues/310)).
 *
 * ## This card draws no Social tag row, and the competitive one does
 *
 * The candidate's own Social tags were refused here on an argument that has since been
 * answered rather than overturned:
 * drawing them *"would put content on the card that the label cannot announce"*, which is the
 * half of Part 13 a hidden decoration is allowed and a fact is not.
 * [#311](https://github.com/Raketa02/Raketa/issues/311) answers it by **announcing them** —
 * `candidateCardLabel` carries the row's clauses, and the rule that comes with it is *do not
 * draw a tag the label does not speak*.
 *
 * **So the reason this card still has none is a different one, and it is about this card.**
 * A tag row wants the card's full width, and this one is media-top: its content column is the
 * whole card and its rows are already a level row, a *You overlap* row and a meta line, which
 * is [`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §5's *Draws*
 * column for it. The competitive card earns the row because it is the surface where **who
 * somebody is** is the question — a game for fun asks *are these two free at the same time*,
 * and the pairing already reaches this card as sentences through the two tag terms. Those
 * sentences are also why adding a row here would cost something: on the card that draws the
 * row, the `Both of you: …` line is filtered as §10's *said once*, and this card would lose a
 * sentence to gain chips it has no width for.
 *
 * The surface that draws tags as tags **in full** is still `SH.playersocial`, and it is still
 * out of scope here.
 */

import { StyleSheet, View } from 'react-native';

import { Button, PlayerPhoto, PressableCard, theme } from '@/shared/ui';
import { levelRow } from '@/shared/formatting/levelRow';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Term } from '../../domain/vocabulary';
import { candidateActionLabel, type CandidateAction } from '../accessibilityPresentation';
import {
  CANDIDATE_ACTION_WORD,
  OVERLAP_ROW_LABEL,
  candidateTag,
  metaLine,
  overlapRowValue,
} from '../playerCardPresentation';

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
  /** Dead where there is no seat left to add anybody to — `CandidateCard`'s prop, same rule. */
  readonly actionDisabled?: boolean;
  /** The body's own action — *Why 78?*. */
  readonly onWhyFit: () => void;
  /**
   * Whether the reader has a live yes towards this person in the search's sport — **the
   * reader's own list's answer** (`saidYesTo`), never this card's. Defaulted to `false` so the
   * card is honest until the screen that holds the list is wired.
   */
  readonly saidYes?: boolean;
}

export function CandidateCardSocial({
  candidate,
  envelope,
  action,
  onAction,
  actionDisabled = false,
  onWhyFit,
  saidYes = false,
}: CandidateCardSocialProps) {
  const facts = candidateFacts({ candidate, envelope, drawn: SOCIAL_CARD_DRAWS });
  const overlap = evidenceOf(candidate, 'availability_overlap');
  // No *best match* on a for-fun pool — see the module note. The two interest tags are drawn.
  const tag = candidateTag({
    inclusionReason: candidate.inclusionReason,
    saidYes,
    bestMatch: false,
  });

  return (
    /* The border is the tag's second copy and goes where the tag goes: bound to the **fact**
       and never to the colour, so *You said yes* — a plain tag — draws no outline. */
    <PressableCard
      style={s.card}
      marked={tag?.kind === 'wants-to-play-you'}
      onPress={onWhyFit}
      accessibilityLabel={facts.label}
    >
      <View style={s.media}>
        <PlayerPhoto
          playerId={candidate.playerId}
          photoUrl={candidate.card.photoUrl}
          box={{ kind: 'media' }}
        />
      </View>

      <View style={s.body}>
        <CardHead name={facts.name} fit={candidate.fit} tag={tag} />

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
          disabled={actionDisabled}
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
