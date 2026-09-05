/**
 * The entry instrument — **the prototype's `ScoreGrid`, brought across.**
 *
 * `prototype/result-confirmation` shared one grid between all three variants on purpose,
 * *"because the variants disagree about WHERE the conversation happens, not about how a number
 * is typed"*, and the ticket says so: the score-entry interaction is solved work. Two arguments
 * came with it and both survive:
 *
 * 1. **A pad, not a stepper and not a keyboard.** A score is typed standing on a court,
 *    one-handed, in the dark. A stepper is six taps to reach 6; the system keyboard puts a 300pt
 *    panel over the thing being typed and offers ten keys where the sport has eight legal values.
 * 2. **The grid is named on both axes.** `6-4 3-6 6-2` is not a score until you know whose 6 it
 *    is, so both sides are named above the columns they own.
 *
 * The **`+` key** is what keeps the pad honest about the one thing the prototype's README left
 * open — badminton's range, and a padel third set that is really a ten-point tie-break. It
 * counts past the ceiling rather than the pad ruling on a format, which is *"the app knows the
 * shape, not the rulebook"* built into the instrument instead of only into the validator.
 *
 * **The reader's side is the left column, and the draft is absolute.** The flip is a `mine`
 * lookup at the point of drawing, exactly as `ScoreTable`'s is: *"a score stored from one point
 * of view has to be flipped by whoever reads it next, and the first reader to forget publishes
 * a loss as a win."*
 */

import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  SHAPE,
  advancesCaret,
  applyKey,
  nextCell,
  padKeys,
  type Cell,
  type ScoreDraft,
  type ScoreKey,
} from '../domain/score';
import { otherSide, scoreColumn, type GameSide, type ScoreColumn } from '../domain/vocabulary';

import { cellLabel, keyLabel, type SpokenSides } from './gameAccessibility';
import { keyFace, setLabel, shapeNote } from './gamePresentation';

export interface ScoreEntryProps {
  readonly draft: ScoreDraft;
  readonly onChange: (next: ScoreDraft) => void;
  readonly sport: Sport;
  /** Which side of the net is the reader's — the left column. */
  readonly mine: GameSide;
  readonly sides: SpokenSides;
}

export function ScoreEntry({ draft, onChange, sport, mine, sides }: ScoreEntryProps) {
  const ours = scoreColumn(mine);

  /**
   * Which cell the pad is typing into. **Route-local and never lifted** — it is a caret, not a
   * value, and a caret in a store is a caret that survives a screen it was drawn on.
   */
  const [focus, setFocus] = useState<Cell>({ set: 0, side: ours });

  const { padTo } = SHAPE[sport];
  const columns: readonly [ScoreColumn, ScoreColumn] = [ours, scoreColumn(otherSide(mine))];
  const sideName = (column: ScoreColumn) => (column === ours ? sides.ours : sides.theirs);

  function press(key: ScoreKey): void {
    onChange(applyKey(draft, focus, key, padTo));
    if (advancesCaret(key)) setFocus(nextCell(focus, columns, draft.length));
  }

  return (
    <View style={s.entry}>
      {/* The two sides, named once, above the columns they own. Each cell says its own side,
          so these are drawn for the eye alone — 6.8's hidden column heads, one grid over. */}
      <View style={s.head} accessibilityElementsHidden importantForAccessibility="no">
        <Text style={s.rowLabel} />
        {columns.map((side) => (
          <Text key={side} style={[s.sideLabel, side === ours ? null : s.sideLabelAway]}>
            {sideName(side)}
          </Text>
        ))}
      </View>

      {draft.map((set, index) => (
        <View key={setLabel(sport, index + 1)} style={s.row}>
          <Text style={s.rowLabel}>{setLabel(sport, index + 1)}</Text>
          {columns.map((side) => {
            const value = set[side];
            const on = focus.set === index && focus.side === side;
            return (
              <Pressable
                key={side}
                accessibilityRole="button"
                accessibilityLabel={cellLabel(sport, index, sideName(side), value)}
                accessibilityState={{ selected: on }}
                onPress={() => setFocus({ set: index, side })}
                // Touch has no hover, so the pressed appearance is declared rather than
                // inherited (6.6), and it sits over either of the two states — the availability
                // cell's own arrangement, one grid over.
                style={({ pressed }) => [
                  s.cell,
                  on ? s.cellOn : null,
                  pressed ? s.cellPressed : null,
                ]}
              >
                <Text style={[s.figure, on ? s.figureOn : null]}>{value === '' ? '·' : value}</Text>
              </Pressable>
            );
          })}
        </View>
      ))}

      <Text style={s.note}>{shapeNote(sport)}</Text>

      {/* 44 x 44 without hitSlop, so a cold thumb in the dark hits it. */}
      <View style={s.pad}>
        {padKeys(padTo).map((key) => {
          const face = keyFace(key, padTo);
          const word = key.kind !== 'value';
          return (
            <Pressable
              key={face}
              accessibilityRole="button"
              accessibilityLabel={keyLabel(key)}
              onPress={() => press(key)}
              style={({ pressed }) => [
                s.key,
                word ? s.keyWord : null,
                pressed ? s.keyPressed : null,
              ]}
            >
              <Text style={[s.keyLabel, word ? s.keyWordLabel : null]}>{face}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

/**
 * The label column, wide enough for `GAME 5` at `flab` — named here rather than in `theme.ts` on
 * `CANDIDATE_PANEL`'s precedent: it is this grid's geometry, not a value the design system holds
 * an opinion about.
 */
const ROW_LABEL_WIDTH = 52;

const s = StyleSheet.create({
  entry: { gap: theme.space.xs },
  head: { flexDirection: 'row', alignItems: 'flex-end', gap: theme.space.xs },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  // `flab`, not the eyebrow role: it labels cells a player is about to OPERATE, and 3.3 says
  // the two are not interchangeable — the availability grid's own rule, applied to its own
  // shape. The width is fixed so every row's cells start in the same place.
  rowLabel: {
    ...theme.type.flab,
    color: theme.color.ink,
    textTransform: 'uppercase',
    width: ROW_LABEL_WIDTH,
  },
  sideLabel: { ...theme.type.rlValue, color: theme.color.ink, flex: 1, textAlign: 'center' },
  sideLabelAway: { color: theme.color.muted },
  cell: {
    flex: 1,
    // The 44pt minimum by geometry rather than by slop, as the availability grid's cell is.
    height: theme.size.minTouch,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.paper2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cellOn: { backgroundColor: theme.color.night },
  cellPressed: { opacity: 0.7 },
  figure: { ...theme.num.l, ...theme.tabular, color: theme.color.ink },
  figureOn: { color: theme.color.surface },
  note: { ...theme.type.tiny, color: theme.color.muted, marginTop: theme.space.xxs },
  pad: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs, marginTop: theme.space.xs },
  key: {
    width: theme.size.minTouch,
    height: theme.size.minTouch,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  keyPressed: { backgroundColor: theme.color.paper2 },
  // The two keys that are not a value carry a word instead, so they need their own width.
  keyWord: { width: 'auto', paddingHorizontal: theme.space.md },
  keyLabel: { ...theme.num.m, ...theme.tabular, color: theme.color.ink },
  keyWordLabel: { ...theme.type.btn, color: theme.color.muted },
});
