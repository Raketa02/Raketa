/**
 * The evidence trail — the lower half of the result screen, and the point of it.
 *
 * The verdict alone is a number without an account of itself, and a rating is never only a
 * number. **The trail is one list: what each part of the player's game said on its own.**
 *
 * ## The rows are drawn against the Level, because otherwise they are four bare numbers
 *
 * They used to be printed as a label, a direction word and a figure, under the heading *what
 * moved your level* — and read that way they are unusable. A player looking at `3,10 · 2,40 ·
 * 2,90 · 3,05` beside a Level of `2,71` reaches for the arithmetic that is not there: the
 * four are not weighted, they do not average to anything, and there is no operation on them
 * that produces the number above. Nothing about the data was wrong. What was wrong is that
 * the screen never said what these numbers *are*.
 *
 * So each row is now **a scale with the Level marked on it**. That is the whole of the fix,
 * and it is a drawing decision rather than a data one: the same figures, on the same 1,00–5,00
 * scale the level bar uses, with the same coral mark meaning the same thing it means there —
 * *you are here*. The comparison the engine already computed is then a thing a player can see
 * rather than a word they have to trust, and the question the card answers changes from *how
 * do these add up* (they do not) to *which parts of my game read higher than the rest* (which
 * is what they were always for).
 *
 * **Nothing about the arithmetic moved and nothing here recomputes anything.** The label, the
 * figure and the direction are all still the server's, carried across exactly as they arrive.
 * The scale is the client drawing what it was given.
 *
 * ## The rules the drawing obeys
 *
 * - **The scale is always the full 1,00–5,00**, as `LevelBar`'s is, so a value lands in the
 *   same place on every row and on the bar above them.
 * - **One mark per scale, and it is coral**, which is the one thing coral means on a scale in
 *   this system (design-system 1.2, 7.5). A row is a level bar without its bands; it is not a
 *   second accent because it is not a second kind of object.
 * - **The strip is hidden from assistive technology**, on `Meter`'s argument: the row states
 *   its figure and its direction in words two inches away, and a drawing over a printed
 *   number is announced twice.
 *
 * ## What is still not drawn
 *
 * **What widened the range.** The engine still sends it and the mapper still reads it —
 * `AssessmentResult.wideners` is the contract and nothing here narrows it — but a player
 * meeting their first rating does not need σ arithmetic itemised at them. The range itself is
 * on the verdict above, the note beside it says the estimate is provisional, and that is the
 * whole of what the widening means to somebody who has not played a match yet. Restoring the
 * list is a rendering decision, not a data one.
 *
 * **Every word below the heading is the server's.** Labels are authored there so they can be
 * corrected without an App Store release, and directions are computed by the engine rather
 * than derived here. What this file owns is where a row sits and what shape it takes.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Card, Hairline, theme } from '@/shared/ui';

import type { EvidenceContribution } from '../domain/AssessmentResult';

import { directionMark, TRAIL_HEADING, trailLede } from './evidencePresentation';
import { formatLevel } from '@/shared/formatting/ratingFormat';

/** The drawn scale, and the only place this file writes it down. It is `LevelBar`'s. */
const SCALE_LOW = 1;
const SCALE_HIGH = 5;

export interface EvidenceTrailProps {
  readonly contributions: readonly EvidenceContribution[];
  /**
   * The Level every row is read against — the mark on each scale.
   *
   * Passed in rather than derived: the rows do not add up to it, which is the confusion the
   * card was redrawn to remove, and a component that computed a level from them would be
   * putting that arithmetic back where nobody can see it.
   */
  readonly level: number;
}

export function EvidenceTrail({ contributions, level }: EvidenceTrailProps) {
  // A run with nothing to account for draws nothing at all, rather than an empty card
  // under a heading promising an account.
  if (contributions.length === 0) return null;

  return (
    <Card>
      <Text style={s.heading}>{TRAIL_HEADING}</Text>
      {/* The lede is what makes the scales readable, and it is the one sentence on this
          card the client wrote: it says the rows are each read on their own and names what
          the mark on them is. Without it the coral line is a decoration. */}
      <Text style={s.lede}>{trailLede(formatLevel(level))}</Text>

      <View style={s.rows}>
        {contributions.map((contribution, index) => {
          const row = <ContributionRow contribution={contribution} level={level} />;

          // 5.5's `index > 0`, expressed with the primitive that owns the fold: the first
          // row has no rule above it and the last none below it.
          return index === 0 ? (
            <View key={contribution.key}>{row}</View>
          ) : (
            <Hairline key={contribution.key}>{row}</Hairline>
          );
        })}
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
 * category, its level and its place on the scale, which is the part the client did not
 * invent.
 *
 * One accessibility element, and its name is unchanged from the row this replaces: the scale
 * says the same thing the words do, and a listener who is told *above your level, 3,10* has
 * been given the whole of it.
 */
function ContributionRow({
  contribution,
  level,
}: {
  readonly contribution: EvidenceContribution;
  readonly level: number;
}) {
  const mark = directionMark(contribution.direction);
  const value = formatLevel(contribution.level);

  return (
    <View
      accessible
      accessibilityLabel={
        mark === undefined
          ? `${contribution.label}: ${value}`
          : `${contribution.label}: ${mark.spoken}, ${value}`
      }
    >
      <View style={s.head}>
        <Text style={s.label}>{contribution.label}</Text>
        <View style={s.direction}>
          {mark === undefined ? null : (
            <>
              <Text style={s.glyph}>{mark.glyph}</Text>
              <Text style={s.word}>{mark.word}</Text>
            </>
          )}
          <Text style={s.value}>{value}</Text>
        </View>
      </View>

      <ContributionScale value={contribution.level} level={level} />
    </View>
  );
}

/**
 * One category's level on the 1,00–5,00 scale, with the player's own Level marked.
 *
 * A level bar without its bands, at row size, drawn from the same theme values so the two
 * cannot drift apart: the coral mark is `LevelBar`'s mark with its surface-coloured ring, and
 * it means what it means there. The category's own value is a dot in `ink` — a second shape
 * rather than a second colour, because *which of these two is you* must not rest on hue.
 *
 * Hidden from assistive technology in full: the row above it prints both figures and the
 * word comparing them (`Meter`).
 */
function ContributionScale({ value, level }: { readonly value: number; readonly level: number }) {
  return (
    <View
      style={s.scale}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <View style={s.track} />
      <View style={[s.dot, { left: percent(fraction(value)) }]} />
      <View style={[s.mark, { left: percent(fraction(level)) }]} />
    </View>
  );
}

/** Where a level sits on the drawn scale, as a fraction of the strip's width. */
function fraction(value: number): number {
  const held = Math.min(Math.max(value, SCALE_LOW), SCALE_HIGH);
  return (held - SCALE_LOW) / (SCALE_HIGH - SCALE_LOW);
}

function percent(value: number): `${number}%` {
  return `${value * 100}%`;
}

const bar = theme.size.levelBar;
const dot = theme.size.bar * 2;

const s = StyleSheet.create({
  heading: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  lede: { ...theme.type.tiny, color: theme.color.muted, marginTop: theme.space.xxs },
  rows: { marginTop: theme.space.sm },
  head: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  // 5.5's own treatment: a `muted` label against an `ink` figure. The row is not a 5.5
  // row — it carries a drawing under it — but the pair it opens with is exactly one.
  label: { ...theme.type.rlLabel, color: theme.color.muted, flexShrink: 1 },
  direction: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  glyph: { ...theme.type.tag, color: theme.color.muted },
  word: { ...theme.type.rlValue, color: theme.color.muted },
  value: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },

  // The mark overhangs the track, so the strip is the mark's height and the track is
  // centred inside it — nothing is clipped at either end.
  scale: { height: bar.markHeight, marginTop: theme.space.xs, justifyContent: 'center' },
  track: {
    height: theme.size.bar,
    borderRadius: theme.radius.bar,
    backgroundColor: theme.color.line2,
  },
  dot: {
    position: 'absolute',
    width: dot,
    height: dot,
    borderRadius: dot / 2,
    // Centred on its value rather than started at it, as the mark is.
    marginLeft: -dot / 2,
    backgroundColor: theme.color.ink,
  },
  mark: {
    position: 'absolute',
    width: bar.markWidth + 2 * bar.markRing,
    height: bar.markHeight,
    marginLeft: -(bar.markWidth / 2 + bar.markRing),
    backgroundColor: theme.color.coral,
    // The ring is the surface showing through around the mark, exactly as on the level bar,
    // so a mark sitting on the dot is still two readable objects.
    borderWidth: bar.markRing,
    borderColor: theme.color.surface,
    borderRadius: bar.markRing,
  },
});
