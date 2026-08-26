/**
 * The evidence trail — the lower half of the result screen, and the point of it.
 *
 * The verdict alone is a number without an account of itself, and a rating is never only a
 * number. **The trail is one list: what moved the Level.**
 *
 * **What widened the range is no longer drawn.** The engine still sends it and the mapper
 * still reads it — `AssessmentResult.wideners` is the contract and nothing here narrows it
 * — but a player meeting their first rating does not need σ arithmetic itemised at them.
 * The range itself is on the verdict above, the note beside it says the estimate is
 * provisional, and that is the whole of what the widening means to somebody who has not
 * played a match yet. Restoring the list is a rendering decision, not a data one.
 *
 * **Every word below the heading is the server's.** Labels and details are authored there
 * so they can be corrected without an App Store release, and directions are computed by the
 * engine rather than derived here. What this file owns is where a row sits and what shape
 * it takes.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Card, Row, theme } from '@/shared/ui';

import type { EvidenceContribution } from '../domain/AssessmentResult';

import { directionMark } from './evidencePresentation';
import { formatLevel } from './ratingFormat';

export interface EvidenceTrailProps {
  readonly contributions: readonly EvidenceContribution[];
}

export function EvidenceTrail({ contributions }: EvidenceTrailProps) {
  // A run with nothing to account for draws nothing at all, rather than an empty card
  // under a heading promising an account.
  if (contributions.length === 0) return null;

  return (
    <Card>
      <View>
        <Text style={s.heading}>What moved your level</Text>
        {contributions.map((contribution, index) => (
          <ContributionRow key={contribution.key} contribution={contribution} divided={index > 0} />
        ))}
      </View>
    </Card>
  );
}

/**
 * One evidence category: what it said on its own, and where that sits relative to the
 * estimate the player was given.
 *
 * The direction is **a shape and a word**, never colour — and where this build cannot read
 * the direction it draws neither, rather than guessing one. The row still carries the
 * category and its level, which is the part the client did not invent.
 */
function ContributionRow({
  contribution,
  divided,
}: {
  readonly contribution: EvidenceContribution;
  readonly divided: boolean;
}) {
  const mark = directionMark(contribution.direction);
  const level = formatLevel(contribution.level);

  return (
    <Row
      label={contribution.label}
      divided={divided}
      accessibilityLabel={
        mark === undefined
          ? `${contribution.label}: ${level}`
          : `${contribution.label}: ${mark.spoken}, ${level}`
      }
      value={
        <View style={s.direction}>
          {mark === undefined ? null : (
            <>
              <Text style={s.glyph}>{mark.glyph}</Text>
              <Text style={s.word}>{mark.word}</Text>
            </>
          )}
          <Text style={s.level}>{level}</Text>
        </View>
      }
    />
  );
}

const s = StyleSheet.create({
  heading: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
    marginBottom: theme.space.xxs,
  },
  direction: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  glyph: { ...theme.type.tag, color: theme.color.muted },
  word: { ...theme.type.rlValue, color: theme.color.muted },
  level: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
});
