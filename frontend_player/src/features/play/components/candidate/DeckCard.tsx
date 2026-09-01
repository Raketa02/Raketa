/**
 * The **deck** card — one person at a time, yes or no, and nothing else.
 *
 * The third of the three, and the only one that **floats**. It animates in, and translates and
 * rotates out under the thumb: a transient object being manipulated rather than a surface a
 * finger rests on, which is the whole of [#219](https://github.com/Raketa02/Raketa/issues/219)
 * B3's argument and the reason it is the only user of `radius.deckCard` and the fourth shadow
 * ([4.3](../../../../../docs/design-system.md#43-elevation) is not bent here — a deck card is
 * not a card).
 *
 * ## Its two buttons are Play's, not `challenges`'
 *
 * A deck yes is `POST /interest`, a matchmaking write, and the challenge a mutual yes opens is
 * minted **server-side and inline** through a port — so nothing on this card reaches another
 * person directly. Left unstated the deck lands in `challenges/` because *Let's play* sounds
 * like a send
 * ([`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §8).
 *
 * **The body's action is the long press, and only here.** §20.3 records
 * [#231](https://github.com/Raketa02/Raketa/issues/231) repointing the long press at *Why
 * 78?* when K-7 ruled the record sheets out, and [#270](https://github.com/Raketa02/Raketa/issues/270)
 * asks for it on this surface by name. The pool's two cards reach the same sheet on a plain
 * press, because a card in a list has no other act to spend a tap on and a long press is not
 * an affordance anybody finds; here a tap is what the two buttons below are for.
 *
 * **There is no gesture to announce.** [#231](https://github.com/Raketa02/Raketa/issues/231)
 * §3 decided against a swipe: *Show them again* was struck, leaving a pass suppressed for
 * thirty days with nothing that reverses one, so a swipe would put the cheapest gesture in the
 * app on the most durable act in the feature. The card takes two named buttons, and the
 * leaving animation stays a leaving animation rather than a promise of a drag.
 *
 * ## What it draws, and therefore what it will not say twice
 *
 * The social card's three rows plus the predicted-balance row, so its drawn set is four —
 * every term with a figure on this card. What is left for the reason line is
 * `INTENT_ALIGNMENT`, `PLAYING_STYLE`, `SOCIAL_VIBE` and `RELIABILITY`, all of which can
 * decline, which is exactly why the fallback to a `LivenessReason` exists and why *hidden* is
 * a state rather than a blank row.
 */

import type { RefObject } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { Button, theme } from '@/shared/ui';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Term } from '../../domain/vocabulary';
import { deckAnswerLabels } from '../accessibilityPresentation';
import {
  BALANCE_ROW_LABEL,
  DECK_ANSWER_WORDS,
  OVERLAP_ROW_LABEL,
  balanceRowValue,
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
export const DECK_CARD_DRAWS: readonly Term[] = [
  'LEVEL_FIT',
  'PREDICTED_BALANCE',
  'AVAILABILITY_OVERLAP',
  'DISTANCE',
];

/**
 * The media slot's shape — **portrait**, because on the deck the card is a photograph.
 *
 * 3:4, the same proportion the profile's photo tiles are stored and shown at, so a picture a
 * player composed for their own profile is not re-cropped to a different frame on somebody
 * else's screen.
 */
const PORTRAIT_ASPECT_RATIO = 0.75;

export interface DeckCardProps {
  readonly candidate: Candidate;
  readonly envelope: SearchEnvelope;
  /** `POST /passes` — a statement about this deck, and about nobody. */
  readonly onPass: () => void;
  /** `POST /interest` — a yes that stands on its own even if they never see it. */
  readonly onAccept: () => void;
  /** The body's own action, reached by a long press. */
  readonly onWhyFit: () => void;
  /**
   * A handle on the body, so the deck can move accessibility focus **onto the card that
   * arrives**.
   *
   * §E3's first finding is that focus is destroyed on every render and nothing restores it,
   * so a listener who answers a card is dropped at the root with no idea what happened. The
   * toast announces the act and this is where focus goes — and it is the *body*, because the
   * body is the element that says who this is (§20.5). The screen owns the moving; the card
   * owns which element is worth moving to, which is why this is a prop and not a rule.
   *
   * A `View` ref rather than `overlay.tsx`'s `FocusTarget`, which is the wider
   * `View | null` shape a `useRef(null)` produces: `Pressable` takes the narrower one, and
   * `moveAccessibilityFocus` accepts this without widening anything.
   */
  readonly bodyRef?: RefObject<View>;
  /**
   * Whether an answer is already on its way — **the two buttons lock until the card has
   * left**.
   *
   * Not a `busy` state: nothing is loading, and the answer is optimistic, so the card is
   * already travelling. What this prevents is the second press landing on a person who has
   * been answered and is still on screen, which would record two acts about one card. It is
   * the courtesy; the correctness is that the screen's handler refuses the same thing.
   */
  readonly answering?: boolean;
}

export function DeckCard({
  candidate,
  envelope,
  onPass,
  onAccept,
  onWhyFit,
  bodyRef,
  answering = false,
}: DeckCardProps) {
  const facts = candidateFacts(candidate, envelope, DECK_CARD_DRAWS);
  const balance = evidenceOf(candidate, 'predicted_balance');
  const overlap = evidenceOf(candidate, 'availability_overlap');
  const answers = deckAnswerLabels(facts.name);

  return (
    <View style={s.card}>
      {/* The clip is a second view rather than a style on the card, because a shadow and an
          `overflow: hidden` on one layer are a shadow drawn against a clipped bound — the
          same reason the sheet and the toast keep their own. */}
      <Pressable
        ref={bodyRef}
        style={s.clip}
        accessibilityRole="button"
        accessibilityLabel={facts.label}
        onLongPress={onWhyFit}
      >
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

          {balance === undefined ? null : (
            <FactRow label={BALANCE_ROW_LABEL} value={balanceRowValue(balance)} />
          )}

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
        </View>
      </Pressable>

      {/* Outside the body, because the body is one accessibility element and these are two
          more: §20.1's one element per action, and the deck has three. */}
      <View style={s.answers}>
        <Button
          label={DECK_ANSWER_WORDS.pass}
          accessibilityLabel={answers.pass}
          onPress={onPass}
          disabled={answering}
          variant="secondary"
          style={s.answer}
        />
        <Button
          label={DECK_ANSWER_WORDS.accept}
          accessibilityLabel={answers.accept}
          onPress={onAccept}
          disabled={answering}
          style={s.answer}
        />
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  card: {
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.deckCard,
    ...theme.shadow.deckCard,
  },
  // Media bleeds to the corners, and this is what gives it the card's radius rather than a
  // second one of its own.
  clip: {
    borderTopLeftRadius: theme.radius.deckCard,
    borderTopRightRadius: theme.radius.deckCard,
    overflow: 'hidden',
  },
  media: { aspectRatio: PORTRAIT_ASPECT_RATIO },
  body: { padding: theme.space.md, gap: theme.space.xs },
  // 0 / 12 / 12 — the body above already paid the top gap (§G1).
  answers: {
    flexDirection: 'row',
    gap: theme.space.sm,
    paddingHorizontal: theme.space.md,
    paddingBottom: theme.space.md,
  },
  answer: { flex: 1 },
});
