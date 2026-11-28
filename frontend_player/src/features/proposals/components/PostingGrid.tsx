/**
 * **WHEN** — the posting grid: its head, its legend and one week of cells
 * ([#558](https://github.com/Rakieta02/Rakieta/issues/558); the screens A5.2; mocks 2-, 20–32).
 *
 * ```
 * WHEN (i)                         [‹]  This week  [›]
 *            Today  Fri   Sat   Sun   Mon   Tue   Wed
 *           30 Sep 1 Oct 2 Oct …
 * Morning   [   ] [ 1 ] [ 5▭] [ 2▭] …
 * 07:00–
 * 12:00
 * Afternoon …
 * Evening   …
 * ```
 *
 * **The head** — *WHEN*, the **ⓘ** that opens the legend (mock 20) as 7.6's anchored popover,
 * widened for its rows, and the pager: week one starts today, so *‹* is shut on it and *›* on week
 * two. **The columns** are the read's seven days, *Today* in `coralInk` over its date; **the rows**
 * are Morning 07–12, Afternoon 12–17, Evening 17–23 (Q71 — the mocks' 08–12 and 17–22:30 are
 * superseded). A range the read left out of a day is a blank slot, never a guessed cell.
 */

import Feather from '@expo/vector-icons/Feather';
import { useRef, useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { InfoMark, Popover, theme } from '@/shared/ui';

import {
  cellIn,
  isPicked,
  type PostingCell as Cell,
  type PostingGrid as Grid,
  type PostingWeek,
  type PostPick,
} from '../domain/posting';
import { DAY_RANGES } from '../domain/vocabulary';

import { PostingCell } from './PostingCell';
import { POSTING_COPY } from './postingCopy';
import {
  dayHead,
  dayHeadSpoken,
  rangeHoursLines,
  rangeLabelSpoken,
  weekTitle,
} from './postingPresentation';

const COPY = POSTING_COPY;
const GRID = theme.size.postingGrid;

export interface PostingGridProps {
  readonly week: PostingWeek;
  readonly onWeek: (week: PostingWeek) => void;
  /** The week's read — absent while it is on its way or could not be read. */
  readonly grid: Grid | undefined;
  readonly pick: PostPick | undefined;
  readonly onCell: (cell: Cell) => void;
  /** What the grid's place says while there is no read to draw — the spinner, a note, a refusal. */
  readonly placeholder: ReactNode;
}

export function PostingGrid({ week, onWeek, grid, pick, onCell, placeholder }: PostingGridProps) {
  const [legend, setLegend] = useState(false);
  const mark = useRef<View | null>(null);

  return (
    <View style={s.when}>
      <View style={s.head}>
        <View style={s.title}>
          <Text style={s.flab} accessibilityRole="header">
            {COPY.when}
          </Text>
          <InfoMark
            ref={mark}
            accessibilityLabel={COPY.legend.open}
            onPress={() => setLegend((open) => !open)}
          />
        </View>
        <View style={s.pager}>
          <PageKey
            glyph="chevron-left"
            label={COPY.earlierWeek}
            onPress={week === 2 ? () => onWeek(1) : undefined}
          />
          <Text style={s.week} accessibilityRole="header">
            {weekTitle(week)}
          </Text>
          <PageKey
            glyph="chevron-right"
            label={COPY.laterWeek}
            onPress={week === 1 ? () => onWeek(2) : undefined}
          />
        </View>
      </View>

      {grid === undefined ? placeholder : <Week grid={grid} pick={pick} onCell={onCell} />}

      <Popover
        visible={legend}
        trigger={mark}
        title={COPY.legend.title}
        closeLabel={COPY.legend.close}
        onClose={() => setLegend(false)}
        wide
      >
        <PostingLegend />
      </Popover>
    </View>
  );
}

function Week({
  grid,
  pick,
  onCell,
}: {
  readonly grid: Grid;
  readonly pick: PostPick | undefined;
  readonly onCell: (cell: Cell) => void;
}) {
  const readAt = Date.parse(grid.readAt);
  return (
    <View style={s.grid} testID={`posting-grid-week-${grid.week}`}>
      <View style={s.row}>
        <View style={s.label} />
        {grid.days.map((day) => {
          const head = dayHead(day);
          return (
            <View
              key={day.day}
              style={s.column}
              accessible
              accessibilityLabel={dayHeadSpoken(head)}
            >
              <Text style={[s.dayName, day.isToday ? s.today : undefined]} numberOfLines={1}>
                {head.name}
              </Text>
              <Text style={s.date} numberOfLines={1}>
                {head.date}
              </Text>
            </View>
          );
        })}
      </View>
      {DAY_RANGES.map((range) => {
        const [from, to] = rangeHoursLines(range);
        return (
          <View key={range} style={s.row}>
            <View style={s.label} accessible accessibilityLabel={rangeLabelSpoken(range)}>
              <Text style={s.range} numberOfLines={1}>
                {COPY.ranges[range]}
              </Text>
              <Text style={s.hours}>{from}</Text>
              <Text style={s.hours}>{to}</Text>
            </View>
            {grid.days.map((day) => {
              const cell = cellIn(day, range);
              return cell === undefined ? (
                <View key={day.day} style={s.blank} />
              ) : (
                <PostingCell
                  key={day.day}
                  cell={cell}
                  picked={isPicked(cell, pick)}
                  readAt={readAt}
                  onPress={() => onCell(cell)}
                />
              );
            })}
          </View>
        );
      })}
    </View>
  );
}

/** A week chevron — a square key, shut at the end of the fortnight. */
function PageKey({
  glyph,
  label,
  onPress,
}: {
  readonly glyph: 'chevron-left' | 'chevron-right';
  readonly label: string;
  readonly onPress: (() => void) | undefined;
}) {
  const shut = onPress === undefined;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: shut }}
      disabled={shut}
      onPress={onPress}
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [
        s.pageKey,
        shut ? s.shut : undefined,
        pressed ? s.pressed : undefined,
      ]}
    >
      <Feather
        name={glyph}
        size={theme.size.rowLeadGlyph}
        color={theme.color.ink}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </Pressable>
  );
}

/**
 * ***How to read the map*** (mock 20) — six rows, each a mark drawn as the grid draws it and its
 * meaning, the red dot's line as A5.2 rewrote it.
 */
function PostingLegend() {
  return (
    <View style={s.legend}>
      <LegendRow text={COPY.legend.brighter}>
        <View style={s.ramp}>
          {[theme.color.mintSoft, theme.color.gridLight, theme.color.gridMid].map((fill) => (
            <View key={fill} style={[s.swatch, { backgroundColor: fill }]} />
          ))}
          <View style={[s.swatch, s.hotSwatch]} />
        </View>
      </LegendRow>
      <LegendRow text={COPY.legend.count}>
        <View style={s.badge}>
          <Text style={s.badgeCount}>{COPY.legend.sampleCount}</Text>
        </View>
      </LegendRow>
      <LegendRow text={COPY.legend.court}>
        <View style={s.legendGlyph} />
      </LegendRow>
      <LegendRow text={COPY.legend.happening}>
        <View style={s.legendDot} />
      </LegendRow>
      <LegendRow text={COPY.legend.outside}>
        <View style={[s.swatch, s.outsideSwatch]} />
      </LegendRow>
      <LegendRow text={COPY.legend.pick} last>
        <Feather
          name="check"
          size={theme.size.rowLeadGlyph}
          color={theme.color.ink}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      </LegendRow>
    </View>
  );
}

function LegendRow({
  text,
  last = false,
  children,
}: {
  readonly text: string;
  readonly last?: boolean;
  readonly children: ReactNode;
}) {
  return (
    <View style={[s.legendRow, last ? undefined : s.legendRule]}>
      <View
        style={s.legendMark}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        {children}
      </View>
      <Text style={s.legendText}>{text}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  when: { gap: theme.space.sm },
  head: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  title: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  // 3.3: `flab` labels a control you are about to operate.
  flab: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  pager: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  week: {
    ...theme.type.cardTitle,
    color: theme.color.ink,
    minWidth: GRID.weekLabel,
    textAlign: 'center',
  },
  pageKey: {
    width: GRID.pager,
    height: GRID.pager,
    borderRadius: theme.radius.btn,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  shut: { opacity: 0.4 },
  pressed: { opacity: 0.7 },
  grid: { gap: GRID.gap },
  row: { flexDirection: 'row', alignItems: 'center', gap: GRID.gap },
  label: { width: GRID.label },
  column: { flex: 1, alignItems: 'center' },
  dayName: { ...theme.type.cardTitle, color: theme.color.ink },
  // Words, so the ink of coral (Rule C) — coral itself is a mark.
  today: { color: theme.color.coralInk },
  date: { ...theme.num.tiny, ...theme.tabular, color: theme.color.muted },
  range: { ...theme.type.cardTitle, color: theme.color.ink },
  hours: { ...theme.num.tiny, ...theme.tabular, color: theme.color.muted },
  blank: { flex: 1, height: GRID.cell },
  legend: { gap: 0 },
  legendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.md,
    paddingVertical: theme.space.sm,
  },
  legendRule: { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: theme.color.line2 },
  legendMark: { width: GRID.legendMark, alignItems: 'center' },
  legendText: { ...theme.type.tiny, color: theme.color.ink, flex: 1 },
  ramp: { flexDirection: 'row', gap: theme.space.xxs },
  swatch: { width: GRID.swatch, height: GRID.swatch, borderRadius: theme.radius.meter },
  hotSwatch: {
    backgroundColor: theme.color.mintInk,
    borderWidth: GRID.glyph.stroke,
    borderColor: theme.color.volt,
  },
  outsideSwatch: {
    backgroundColor: theme.color.mintSoft,
    borderStyle: 'dashed',
    borderWidth: GRID.dash,
    borderColor: theme.color.mintInk,
    opacity: GRID.outside,
  },
  badge: {
    minWidth: theme.size.fit,
    height: theme.size.fit,
    borderRadius: theme.radius.fit,
    backgroundColor: theme.color.mintInk,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeCount: { ...theme.num.xs, ...theme.tabular, color: theme.color.surface },
  legendGlyph: {
    width: GRID.glyph.width,
    height: GRID.glyph.height,
    borderWidth: GRID.glyph.stroke,
    borderRadius: GRID.glyph.radius,
    borderColor: theme.color.ink,
  },
  legendDot: {
    width: GRID.dot,
    height: GRID.dot,
    borderRadius: GRID.dot / 2,
    backgroundColor: theme.color.coralInk,
  },
});
