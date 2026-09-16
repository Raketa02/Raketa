/**
 * The **radar card** — a player at 5,4 km across and below, and the selected player at every
 * width ([`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §7.4, mocks
 * 10–14).
 *
 * A paper card ~190 pt wide at the card radius, anchored so its **top-left** sits at the
 * player's spot, drawn line for line as the mocks draw it:
 *
 * 1. **Identity** — a 34 pt face (photograph or poster), the name in `h2`, the distance in
 *    mono `tiny` under it; the on-court mark where the deck would draw it, at the row's end.
 * 2. **A rule** — 5.3's hairline.
 * 3. **One sport row per sport they are rated in** — the sport's dot, its name as an eyebrow,
 *    the level right-aligned in mono — the reading's sport first (`domain/reading`'s
 *    `sportRows`) and every sport, not only the ones the viewer shares.
 * 4. **The two scores, labelled** — the Fit pill with *fit* after its figure, and the
 *    reliability chip, `88 reliability` on `paper2`, *—* where the platform has watched nothing.
 *    *Labelled, because two bare numbers read as one printed twice.*
 * 5. **Tags in common** — *N tags in common* in mint where there are any, *no tags in common*
 *    muted, and **a count, never a list**. Derived by the deck's own function
 *    (`domain/socialTagOverlap`): the engine's published `matched[]`, never recomputed from a
 *    profile. Where the engine compared nothing — one side published no tags in a column, or
 *    the match is beyond this build's vocabulary — the line is **not drawn**, because *no tags in
 *    common* is a claim and *we do not know* is not (`shared/vocabulary/socialTagOverlap`).
 * 6. **The last line** — *Tap for the full card ›* in coral. #464 replaces it with the answer
 *    line after a yes or a pass; nothing here knows about answers yet.
 *
 * ## The whole card is the target
 *
 * One accessibility element, a `button`, named by the §26 sentence — the same name the face
 * carries at the other two widths, so a listener follows one person through every state —
 * and its press opens the record sheet (§7.5): read-only until #464 fills the sheet's foot.
 * The pill, the chip, the dot and the mark merge into it, as they merge into the deck card.
 *
 * The card is drawn at its natural size and the field places and counter-scales it, so a
 * card is always ~190 pt whatever the pinch is doing (§7.9).
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { sportColour, sportLabel } from '@/features/onboarding/types';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import { playerName } from '@/shared/formatting/playerName';
import { FitPill, Hairline, OnCourtMark, PlayerPhoto, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { wearsOnCourtMark } from '../../domain/onCourtMark';
import { sportRows, type RadarRow } from '../../domain/reading';
import { socialTagOverlap } from '../../domain/socialTagOverlap';
import {
  FIT_WORD,
  RELIABILITY_WORD,
  TAP_FOR_THE_FULL_CARD,
  UNWATCHED_MARK,
  cardDistance,
  tagsInCommon,
} from '../radarPresentation';

export interface RadarCardProps {
  readonly row: RadarRow;
  /** The reading's sport — first among the sport rows. */
  readonly sport: Sport;
  /** The §26 sentence — composed by the field, so one label names one person in every state. */
  readonly accessibilityLabel: string;
  readonly onPress: () => void;
}

export function RadarCard({ row, sport, accessibilityLabel, onPress }: RadarCardProps) {
  const name = playerName({ kind: 'player', name: row.card.name });
  const common = tagsInCommonCount(row);

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      style={({ pressed }) => [s.card, pressed ? s.pressed : undefined]}
    >
      <View style={s.identity}>
        <PlayerPhoto playerId={row.playerId} photoUrl={row.card.photoUrl} box={FACE} />
        <View style={s.who}>
          <Text style={s.name} numberOfLines={1}>
            {name}
          </Text>
          <Text style={s.distance}>{cardDistance(row.distanceKm)}</Text>
        </View>
        {wearsOnCourtMark(row.card) ? <OnCourtMark on="radar" /> : null}
      </View>

      {/* The card's own gap is the rule's top margin, so the hairline's is taken back. */}
      <Hairline style={s.rows}>
        {sportRows(row, sport).map((rated) => (
          <View key={rated.sport} style={s.sportRow}>
            {/* 6.4's square dot, with the name beside it — 2.3's condition on drawing a hue. */}
            <View
              style={[s.dot, { backgroundColor: sportColour(rated.sport) }]}
              accessibilityElementsHidden
              importantForAccessibility="no"
            />
            <Text style={s.sport} numberOfLines={1}>
              {sportLabel(rated.sport)}
            </Text>
            <Text style={s.level}>{formatLevel(rated.level)}</Text>
          </View>
        ))}
      </Hairline>

      <View style={s.scores}>
        <FitPill fit={row.fit} trailing={FIT_WORD} />
        {/* One sentence for a reader — `88 reliability` — drawn as a mono figure and a word, so
            the number is tabular as every number is (1.4) and the word is the pill's own role. */}
        <View style={s.reliability}>
          <Text style={s.reliabilityFigure}>{row.card.playerScore ?? UNWATCHED_MARK}</Text>
          <Text style={s.reliabilityWord}>{RELIABILITY_WORD}</Text>
        </View>
      </View>

      {common === undefined ? null : (
        <Text style={common > 0 ? s.tagsShared : s.tagsNone}>{tagsInCommon(common)}</Text>
      )}

      <Text style={s.door}>{TAP_FOR_THE_FULL_CARD}</Text>
    </Pressable>
  );
}

/**
 * How many tags the two have in common, **or nothing where the engine compared nothing**.
 *
 * `socialTagOverlap`'s four answers, read for a count: `shared` counts the marked tags,
 * `none-in-common` is the amber claim and counts nought, and the two silences — not compared,
 * or matched beyond this build's words — are `undefined`, which draws no line. See the module
 * note.
 */
function tagsInCommonCount(row: RadarRow): number | undefined {
  const overlap = socialTagOverlap(row);
  switch (overlap.kind) {
    case 'shared':
      return overlap.tags.filter((tag) => tag.shared).length;
    case 'none-in-common':
      return 0;
    case 'unknown':
    case 'hidden':
      return undefined;
  }
}

const FACE = { kind: 'face', size: theme.size.radar.face } as const;

const s = StyleSheet.create({
  card: {
    width: theme.size.radar.card,
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.color.line,
    padding: theme.space.md,
    gap: theme.space.sm,
  },
  pressed: { opacity: 0.85 },
  identity: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  who: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.h2, color: theme.color.ink },
  distance: { ...theme.num.tiny, ...theme.tabular, color: theme.color.muted },
  rows: { marginTop: 0, gap: theme.space.xs },
  sportRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  dot: { width: theme.size.sportDot, height: theme.size.sportDot },
  sport: {
    flex: 1,
    ...theme.type.eyebrow,
    textTransform: 'uppercase',
    color: theme.color.muted,
  },
  level: { ...theme.num.s, ...theme.tabular, color: theme.color.ink },
  scores: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  reliability: {
    height: theme.size.fit,
    paddingHorizontal: theme.space.sm,
    borderRadius: theme.radius.fit,
    backgroundColor: theme.color.paper2,
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
  },
  reliabilityFigure: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
  reliabilityWord: { ...theme.type.inlineTitle, color: theme.color.muted },
  tagsShared: { ...theme.type.rlValue, color: theme.color.mintInk },
  tagsNone: { ...theme.type.rlLabel, color: theme.color.muted },
  door: { ...theme.type.cardTitle, color: theme.color.coralInk },
});
