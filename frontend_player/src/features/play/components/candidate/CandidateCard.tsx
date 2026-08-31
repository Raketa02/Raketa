/**
 * The **competitive** candidate card — photo-left, with a head-to-head row.
 *
 * One of three components over one parts kit, and deliberately **not one component with a
 * `surface` prop**: a single card would carry `surface === …` at nine sites, which is §G3
 * #1's complaint (*"sixty lines of interpolation with eight conditional blocks"*) arriving in
 * a new spelling
 * ([`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §3). After Decision 3 the shapes genuinely differ: this one is photo-left with a
 * head-to-head row, and the social and deck cards are media-top with fact rows.
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
 * ## What it draws, and therefore what it will not say twice
 *
 * The head-to-head row prints **both levels** and the balance bar draws the **forecast**, so
 * `LEVEL_FIT` and `PREDICTED_BALANCE` are this card's drawn set and neither appears as a
 * reason line. `RELIABILITY` joins them the day the Player Score block prints and not before.
 * `DISTANCE` is not in the set — this card draws no distance row, which is why a reason line
 * on it can never come up empty.
 *
 * ## The button knows nothing about sending
 *
 * It takes `onAction` and a code, which is what lets one shape serve *Add* and *Challenge*.
 * `SH.propose` and the send itself are `features/challenges/`'
 * ([`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §8). The **body's** own action is *Why 78?*, which is where
 * [#231](https://github.com/Raketa02/Raketa/issues/231) repointed the long press when K-7
 * ruled the record sheets out — so the card is two accessibility elements and not one.
 */

import { StyleSheet, Text, View } from 'react-native';

import { playerName } from '@/shared/formatting/playerName';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import { BalanceBar, Button, PressableCard, theme } from '@/shared/ui';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Term } from '../../domain/vocabulary';
import { candidateActionLabel, type CandidateAction } from '../accessibilityPresentation';
import { balanceLabel, balanceReading, balanceTone } from '../balancePresentation';
import { BALANCE_ROW_LABEL, CANDIDATE_ACTION_WORD } from '../playerCardPresentation';

import { CandidatePhoto } from './CandidatePhoto';
import { CardHead } from './CardHead';
import { FactRow } from './FactRow';
import { ReasonLine } from './ReasonLine';
import { candidateFacts, evidenceOf } from './candidateFacts';

/**
 * What this card draws for itself, and therefore drops from its reason list.
 *
 * **Exported by the component**, because the set is a statement about what this component
 * draws and moving it into the selector is the one place it could go stale silently
 * ([`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §5).
 */
export const COMPETITIVE_CARD_DRAWS: readonly Term[] = ['LEVEL_FIT', 'PREDICTED_BALANCE'];

export interface CandidateCardProps {
  readonly candidate: Candidate;
  readonly envelope: SearchEnvelope;
  /** What the primary button does. A code, so a third surface gains a word or does not build. */
  readonly action: CandidateAction;
  readonly onAction: () => void;
  /** The body's own action — *Why 78?*. */
  readonly onWhyFit: () => void;
}

export function CandidateCard({
  candidate,
  envelope,
  action,
  onAction,
  onWhyFit,
}: CandidateCardProps) {
  const facts = candidateFacts(candidate, envelope, COMPETITIVE_CARD_DRAWS);
  const levelFit = evidenceOf(candidate, 'level_fit');
  const balance = evidenceOf(candidate, 'predicted_balance');

  return (
    <PressableCard style={s.card} onPress={onWhyFit} accessibilityLabel={facts.label}>
      <View style={s.body}>
        <CandidatePhoto
          playerId={candidate.playerId}
          photoUrl={candidate.card.photoUrl}
          box={{ kind: 'thumb' }}
        />

        <View style={s.column}>
          <CardHead
            name={facts.name}
            fit={candidate.fit}
            inclusionReason={candidate.inclusionReason}
          />

          {/* Both levels, side by side — the row this card draws instead of a level row, and
              the reason `LEVEL_FIT` is in its drawn set. Absent where the term stood down:
              there is no second source for the searcher's own μ, and inventing one would be
              the client computing a level. */}
          {levelFit === undefined ? null : (
            <View style={s.headToHead}>
              <Side name={playerName({ kind: 'you' })} level={levelFit.myMu} />
              <Side name={facts.name} level={levelFit.theirMu} />
            </View>
          )}

          {/* The bar says WHICH side, the printed percentage says HOW even, and they are two
              different facts — so the bar takes the level advantage and never the forecast.
              At `sm` there are no segment labels, and the head-to-head row above has already
              named both sides. */}
          {/* The bar is hidden and the row below carries it. §20.1 merges an actionless
              element into the nearest action above it, and §20.3 counts the card as two
              elements — the body and its button — so a bar announcing itself inside the body
              would be a third. Its own `image` role and name are §20.4's, and §20.4 is about
              the court, where the bar sits on a screen rather than inside a button. */}
          {levelFit === undefined || balance === undefined ? null : (
            <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
              <BalanceBar
                advantage={levelFit.myMu - levelFit.theirMu}
                tone={balanceTone(balance.pct)}
                size="sm"
                accessibilityLabel={balanceLabel(balance.pct)}
              />
            </View>
          )}

          {/* The word and the figure the bar's tint stands for. Part 13's *never colour
              alone*, and what makes `PREDICTED_BALANCE` a term this card renders a VALUE for
              rather than one it tints — which is what its presence in the drawn set claims.
              It is drawn whenever the term fired, because the bar needs a level advantage as
              well and the forecast is a fact on its own; `candidateFacts` speaks the same
              reading, so the listener and the reader get it exactly once each. */}
          {balance === undefined ? null : (
            <FactRow label={BALANCE_ROW_LABEL} value={balanceReading(balance.pct)} />
          )}

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
      </View>
    </PressableCard>
  );
}

/**
 * One half of the head-to-head row: who, and what they are rated.
 *
 * Two elements rather than one interpolated string, because the level is a **figure** — mono
 * and tabular, so twenty cards scrolling past one another keep their columns — and a figure
 * inside a sentence is a figure in the sentence's font.
 */
function Side({ name, level }: { readonly name: string; readonly level: number }) {
  return (
    <View style={s.side}>
      <Text style={s.sideName} numberOfLines={1}>
        {name}
      </Text>
      <Text style={s.sideLevel}>{formatLevel(level)}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  // 12 / 12 / 9 — the 3pt grid's reading of the prototype's 11 / 11 / 9 (§G1).
  card: { paddingBottom: theme.space.sm },
  body: { flexDirection: 'row', gap: theme.space.md },
  column: { flex: 1, gap: theme.space.xs },
  headToHead: { flexDirection: 'row', justifyContent: 'space-between', gap: theme.space.sm },
  side: { flexDirection: 'row', alignItems: 'baseline', gap: theme.space.xxs, flexShrink: 1 },
  sideName: { ...theme.type.rlLabel, color: theme.color.muted, flexShrink: 1 },
  sideLevel: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
  action: { alignSelf: 'flex-start' },
});
