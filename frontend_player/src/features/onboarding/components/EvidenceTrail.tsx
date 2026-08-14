/**
 * The evidence trail — the lower half of the result screen, and the point of it.
 *
 * The verdict alone is a number without an account of itself, and a rating is never only a
 * number. **The trail is two lists and they stay apart**, because they answer different
 * questions: what moved the Level, and what widened the range. Nothing appears in both, and
 * **the second list has no direction** — something that widened the range did not move the
 * Level, and drawing it with an arrow would describe a different rating than the one
 * produced.
 *
 * One card with a fold between the halves, not two cards: it is one account.
 *
 * **Every word below the headings is the server's.** Labels, details and the confidence
 * sentence are authored there so they can be corrected without an App Store release, and
 * directions are computed by the engine rather than derived here. What this file owns is
 * where a row sits and what shape it takes — including the fallback that keeps a key this
 * build has never seen on the screen instead of dropping it.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Card, Hairline, Note, Row, theme } from '@/shared/ui';

import type { EvidenceContribution, RangeWidener } from '../domain/AssessmentResult';

import { directionMark, widenerVariant } from './evidencePresentation';
import { formatLevel, formatSigma } from './ratingFormat';

export interface EvidenceTrailProps {
  readonly contributions: readonly EvidenceContribution[];
  readonly wideners: readonly RangeWidener[];
}

export function EvidenceTrail({ contributions, wideners }: EvidenceTrailProps) {
  // A run can produce one and not the other — a beginner's single answer moves the Level
  // and widens nothing — so each half appears only when it has something to say.
  if (contributions.length === 0 && wideners.length === 0) return null;

  return (
    <Card>
      {contributions.length > 0 ? (
        <View>
          <Text style={s.heading}>What moved your level</Text>
          {contributions.map((contribution, index) => (
            <ContributionRow
              key={contribution.key}
              contribution={contribution}
              divided={index > 0}
            />
          ))}
        </View>
      ) : null}

      {wideners.length > 0 ? (
        <Hairline style={contributions.length === 0 ? s.unfolded : undefined}>
          <Text style={s.heading}>What widened your range</Text>
          <View style={s.wideners}>
            {wideners.map((widener) => (
              <WidenerNote key={widener.key} widener={widener} />
            ))}
          </View>
        </Hairline>
      ) : null}
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

/**
 * One thing that widened the range, with how much uncertainty it actually added.
 *
 * A note rather than a row, because a widener carries a sentence and a row is a line. The
 * emphasis comes from the key where this build recognises it and from the default where it
 * does not — **an unknown key renders, it never vanishes.**
 */
function WidenerNote({ widener }: { readonly widener: RangeWidener }) {
  const added = formatSigma(widener.sigmaAdded);

  return (
    <Note variant={widenerVariant(widener.key)} title={widener.label}>
      <View style={s.widener}>
        <Text style={s.detail}>{widener.detail}</Text>
        <Text style={s.added} accessibilityLabel={`Widened your range by ${added}`}>
          {`+${added}`}
        </Text>
      </View>
    </Note>
  );
}

const s = StyleSheet.create({
  heading: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
    marginBottom: theme.space.xxs,
  },
  // Where there is no first half, the fold has nothing to fold away from.
  unfolded: { borderTopWidth: 0, marginTop: 0, paddingTop: 0 },
  wideners: { gap: theme.space.xs },
  direction: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  glyph: { ...theme.type.tag, color: theme.color.muted },
  word: { ...theme.type.rlValue, color: theme.color.muted },
  level: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
  widener: { flexDirection: 'row', alignItems: 'flex-start', gap: theme.space.sm },
  detail: { ...theme.type.tiny, color: theme.color.ink, flex: 1 },
  added: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
});
