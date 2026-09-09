/**
 * **The card block** — who is asking, and what this platform makes of playing them.
 *
 * Drawn while the arrangement is being decided and at no other time
 * ([ADR-0143](../../../../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)
 * §8), and **per seat as well as per challenge**: the wire omits the card on your own seat, on
 * an empty one and on a seat that has left, so a doubles court draws one of these per person
 * still in it and a singles challenge draws exactly one.
 *
 * ## It is a fourth card, and it is not one of the three
 *
 * `challenges` spells its own schema and it is **narrower than a `PlayerCard`** (ADR-0143 §5) —
 * no social tags, no run of form, no counted games, no photo verdict, no liveness, no inclusion
 * reason. So this is a fourth composition over the same parts kit, on the same argument that
 * made three of them rather than one with a `surface` prop: the shapes genuinely differ, and one
 * component carrying `surface === …` at nine sites is the sixty-line conditional the split
 * exists to prevent.
 *
 * **Four things the design draws that this does not**, each with its record:
 *
 * 1. **No bio.** `PlayerCardSchema` refuses free text *ever*, and ADR-0143 §5 holds the refusal
 *    is **stronger** here than where it was written: a searcher chose to look, an invitee was put
 *    in front of somebody without asking.
 * 2. **The Player Score is a segment that disappears**, never a row reading `Score 0` — most
 *    people on this platform have no published figure, and a nought for somebody nothing was
 *    watched of is a claim where there is a gap (ADR-0140).
 * 3. **No *Why?* affordance.** The whole breakdown ships inline with the read, so a sheet is
 *    buildable and is not built: what is printed is the top reasons and at most one concern, on
 *    this card's own caps.
 * 4. **No countdown.** The deadline is **stated** by the screen and never obeyed — the client has
 *    never carried it, and a countdown would be this phone's clock deciding what the platform's
 *    clock owns.
 *
 * ## What it draws is what it will not say twice
 *
 * The identity row prints their Level and their distance, and the segment prints their Player
 * Score — so `LEVEL_FIT`, `DISTANCE` and `RELIABILITY` are this card's drawn set and none of the
 * three appears as a reason line
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §10). **The set is
 * exported by the component**, because it is a statement about what this component draws and
 * moving it into the selector is the one place it could go stale silently.
 *
 * **`PREDICTED_BALANCE` is deliberately *not* in it.** The court's own forecast is drawn once by
 * the screen — *the same figure rides on every card, because a forecast is a fact about the game
 * rather than about one person* — so a balance row here would be that number printed once per
 * seat, and putting the term in the drawn set would then silence the one reason line that
 * survives a court with nothing else to say about it.
 *
 * ## It reads no global state
 *
 * `(seat, sportName)` in, and nothing else. The Sport is a property of the **challenge** rather
 * than of the person, so it is a prop for the same reason `sportName` is one on a Play card, and
 * the seat count that decides whether a stake may be printed is the **court's** and arrives the
 * same way.
 *
 * ## One accessibility element, no action of its own
 *
 * §24.3: the card carries no action and the two buttons are beneath it, so the whole block is
 * **one element** with a merged name — and the photograph, which is actionless, merges into it
 * exactly as it does on every other card in this app.
 */

import { StyleSheet, View } from 'react-native';

import {
  CandidatePhoto,
  CardHead,
  FactRow,
  ReasonLine,
  StakeBoxes,
  concernLines,
  reasonLine,
  reasonLines,
  selectReasons,
  stakeOnACard,
  type Term,
} from '@/features/play/types';
import { Card, theme } from '@/shared/ui';

import type { SeatCard } from '../domain/challengeDetail';

import { challengeCardLabel, identityRow } from './challengeDetailPresentation';

/** See the module note. Exported by the component, because it is a claim about this component. */
export const CHALLENGE_CARD_DRAWS: readonly Term[] = ['LEVEL_FIT', 'DISTANCE', 'RELIABILITY'];

export interface ChallengeCardProps {
  /** Whose seat this is — the poster's input, and the reason it survives a reinstall. */
  readonly playerId: string;
  readonly card: SeatCard;
  /**
   * How many seats this court has, for the one rule that reads it.
   *
   * `stakeOnACard` refuses a doubles court: *a win against one named person isn't a thing that
   * exists until the other three seats are known.* It is handed the count rather than deriving
   * one, so this component holds no seat arithmetic to get wrong a second time.
   */
  readonly seats: number;
}

export function ChallengeCard({ playerId, card, seats }: ChallengeCardProps) {
  const { person, pairing } = card;

  // **The de-duplication filter runs before the cap**, and it is the shared rule rather than
  // this card's: the terms this card draws, the terms the engine is concerned about, and the
  // terms whose evidence is not a reason at all all come out before three are taken. A survivor
  // that rendered nothing is the blank row the whole selection exists to prevent.
  const reasons = reasonLines(
    selectReasons({
      drawn: CHALLENGE_CARD_DRAWS,
      terms: pairing.terms,
      concerns: pairing.concerns,
      // A challenge has none, and it is not an omission: `liveness_reasons` answers *why did
      // this person move*, and **that question does not exist when somebody asked you
      // directly** (ADR-0143 §5). There is no list they moved up, so the fallback arm this
      // hands `selectReasons` is one it can never take.
      livenessReasons: [],
      // A row this build cannot read says nothing on a card: §3 drops a code wherever the
      // screen states no total it belongs to, and this card shows three reasons out of eight.
      saysSomething: (row) => row.evidence !== null && reasonLine(row.evidence) !== undefined,
    }),
  );

  // The rule and its sentences are both Play's, and both cross whole: a second spelling of
  // *which concern, written how* is how one card starts drawing a concern the other would have
  // declined to write.
  const concerns = concernLines(pairing);

  const stake = stakeOnACard({
    seats,
    ...(pairing.atStake === undefined ? {} : { atStake: pairing.atStake }),
  });

  return (
    <Card style={s.card}>
      {/* §24.3: **one element, no action.** The card carries no control of its own and the two
          answers are beneath it, so the whole block is `accessible` with one merged name and
          the photograph merges into it rather than announcing itself. */}
      <View
        accessible
        accessibilityLabel={challengeCardLabel({
          person,
          fit: pairing.fit,
          ...(pairing.distanceKm === undefined ? {} : { distanceKm: pairing.distanceKm }),
          reasons,
          concerns,
          ...(stake === undefined ? {} : { atStake: stake }),
        })}
      >
        <View style={s.media}>
          <CandidatePhoto
            playerId={playerId}
            {...(person.photoUrl === undefined ? {} : { photoUrl: person.photoUrl })}
            box={{ kind: 'media' }}
          />
        </View>

        <View style={s.body}>
          {/* No `inclusionReason`: a challenge has no list to have been lifted onto, so the tag
              beside the handle has nothing it could be about. */}
          <CardHead name={person.nickname} fit={pairing.fit} />

          <FactRow
            value={identityRow({
              person,
              ...(pairing.distanceKm === undefined ? {} : { distanceKm: pairing.distanceKm }),
            })}
          />

          <StakeBoxes {...(stake === undefined ? {} : { stake })} />

          {reasons.map((line, at) => (
            <ReasonLine key={`reason-${at}`} line={line} />
          ))}

          {concerns.map((line, at) => (
            <ReasonLine key={`concern-${at}`} line={line} variant="concern" />
          ))}
        </View>
      </View>
    </Card>
  );
}

const s = StyleSheet.create({
  // The media bleeds to the card's own edges and takes its corners, so the card clips rather
  // than the photograph rounding itself: one corner drawn once, at one value.
  card: { padding: 0, overflow: 'hidden' },
  media: { width: '100%' },
  body: { padding: theme.space.md, gap: theme.space.sm },
});
