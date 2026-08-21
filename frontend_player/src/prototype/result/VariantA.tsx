/* eslint-disable no-restricted-syntax --
 * THROWAWAY PROTOTYPE. The rule is right and the literals below are the POINT: every one
 * is a value `theme.ts` cannot express yet, marked `MISSING TOKEN`, and the list of them
 * is part of this ticket's answer. A literal in a production component stays a bug.
 */
/**
 * THROWAWAY PROTOTYPE — issue #24. Not production.
 *
 * VARIANT A — **in the card.** No new surface at all.
 *
 * The argument: `confirmResult` is a situation on the ladder like the other 32, and
 * ADR-0040 already says the ladder resolves a situation and the CLIENT renders it — with
 * `confirmResult` the one situation that reads the viewer. So the two audiences are two
 * renderings of one card, which is exactly what the specification set already describes,
 * and the entry pad opens inside the card rather than over it. Nothing new is introduced,
 * and Now stays a status surface you can act on without leaving.
 *
 * What it costs, and the reason to look hard at it: the state card's action row is built
 * for ONE action plus two icon buttons (`UI` §B6.3), and this needs two real actions. And
 * the pad inside a night card at 320pt pushes the card past a screen height on its own.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { CourtGlyph } from './CourtGlyph';
import { SHAPE, inlineScore, refuse, type Leg } from './data';
import { ScoreGrid } from './ScoreGrid';
import type { VariantProps } from './types';

export function VariantA({ fixture, screen, draft, setDraft }: VariantProps) {
  const shape = SHAPE[fixture.sport];
  const entering = screen === 'enter' || screen === 'counter';
  const problem = entering ? refuse(draft) : null;

  const tag =
    screen === 'enter'
      ? 'Needs result'
      : screen === 'unscored'
        ? 'Played'
        : screen === 'counter'
          ? 'Confirm the result'
          : 'Confirm the result';

  return (
    <View style={s.card}>
      {/* 1 — header row, unchanged from every other state card */}
      <View style={s.headRow}>
        <View style={s.tag}>
          <View
            style={[
              s.toneDot,
              {
                backgroundColor:
                  screen === 'unscored' ? 'rgba(255,255,255,0.45)' : theme.color.coral,
              },
            ]}
          />
          <Text style={s.tagLabel}>{tag}</Text>
        </View>
        <Text style={s.eyebrowOnDark}>
          {fixture.sport.toUpperCase()} · {fixture.format.toUpperCase()}
        </Text>
      </View>

      {/* 2 — identity row. The score does NOT replace the start time: the card still has
          to say which evening this was, and that is the whole reason it is still on Now. */}
      <View style={s.identRow}>
        <View style={s.identLeft}>
          <Text style={s.startTime}>{fixture.startTime}</Text>
          <Text style={s.whenLine}>
            {fixture.whenLabel} · {fixture.clubName}
          </Text>
          <Text style={s.tinyOnDark}>
            {fixture.courtLabel} · {fixture.durationMin} min
          </Text>
        </View>
        <View style={s.identRight}>
          <CourtGlyph sport={fixture.sport} seats={fixture.seats} w={58} dark fixContrast />
          <Text style={s.seatCount}>
            {fixture.capacity}/{fixture.capacity}
          </Text>
        </View>
      </View>

      {/* 3 — where the facet row was. On a settled or proposed result the two facets say
          `Settled` and `4 of 4 played`, which nobody needs twice, so the score takes the
          slot: the card's one changing fact. */}
      {screen === 'asked' || screen === 'waiting' ? (
        <View style={s.hair}>
          <Text style={s.attrib}>
            {screen === 'asked'
              ? `${fixture.proposer.toUpperCase()} ENTERED · ${fixture.enteredAt.toUpperCase()}`
              : `YOU ENTERED · ${fixture.enteredAt.toUpperCase()}`}
          </Text>
          <ScoreLine legs={fixture.proposed} sides={fixture.sides} />
        </View>
      ) : null}

      {screen === 'unscored' ? (
        <View style={s.hair}>
          <Text style={s.attrib}>NO SCORE</Text>
          <Text style={s.unscoredLead}>This one counted as an evening.</Text>
        </View>
      ) : null}

      {entering ? (
        <View style={s.hair}>
          {screen === 'counter' ? (
            <View style={s.onTable}>
              <Text style={s.onTableLabel}>
                {fixture.proposer.toUpperCase()} PROPOSED · STILL ON THE TABLE
              </Text>
              <Text style={s.onTableScore}>{inlineScore(fixture.proposed)}</Text>
            </View>
          ) : null}
          <ScoreGrid
            shape={shape}
            sides={fixture.sides}
            value={draft}
            onChange={setDraft}
            surface="night"
          />
        </View>
      ) : null}

      {/* 5 — the line list, carrying the consequence. This is the whole design: silence
          becomes consent in a fact line, in the same list that already carries
          `You paid 34,00 zł`, with no banner. */}
      <View style={s.hair}>
        {LINES(screen, fixture).map(([done, text], i) => (
          <View key={i} style={s.line}>
            {done === 1 ? <Text style={s.check}>✓</Text> : <View style={s.ring} />}
            <Text style={s.lineText}>{text}</Text>
          </View>
        ))}
      </View>

      {/* 6 — action row. Two REAL actions where `UI` §B6.3 has one; the `⌘` access button
          is already dropped by the `post` flag, so the room comes from there. */}
      <View style={s.actions}>
        {screen === 'asked' ? (
          <>
            <Pressable style={[s.cta, s.grow]} accessibilityRole="button">
              <Text style={s.ctaLabel}>That's right</Text>
            </Pressable>
            <Pressable style={[s.ctaGhost, s.grow]} accessibilityRole="button">
              <Text style={s.ctaGhostLabel}>Modify</Text>
            </Pressable>
          </>
        ) : null}
        {screen === 'waiting' ? (
          <Pressable style={[s.ctaGhost, s.grow]} accessibilityRole="button">
            <Text style={s.ctaGhostLabel}>Change what I entered</Text>
          </Pressable>
        ) : null}
        {entering ? (
          <Pressable
            style={[s.cta, s.grow, problem !== null ? s.ctaOff : null]}
            accessibilityRole="button"
          >
            <Text style={s.ctaLabel}>
              {problem ?? (screen === 'counter' ? 'Propose this instead' : 'Send this score')}
            </Text>
          </Pressable>
        ) : null}
        {screen === 'unscored' ? (
          <Pressable style={[s.ctaGhost, s.grow]} accessibilityRole="button">
            <Text style={s.ctaGhostLabel}>Open match</Text>
          </Pressable>
        ) : null}
        <Pressable style={s.iconBtn} accessibilityRole="button" accessibilityLabel="Open inbox">
          <Text style={s.iconGlyph}>✉</Text>
        </Pressable>
      </View>
    </View>
  );
}

function ScoreLine({
  legs,
  sides,
}: {
  readonly legs: readonly Leg[];
  readonly sides: VariantProps['fixture']['sides'];
}) {
  const played = legs.filter(([a, b]) => a !== null && b !== null);
  return (
    <View style={s.scoreLine}>
      <View style={s.scoreNames}>
        <Text style={s.scoreNameMine} numberOfLines={1}>
          {sides[0].label}
        </Text>
        <Text style={s.scoreNameTheirs} numberOfLines={1}>
          {sides[1].label}
        </Text>
      </View>
      <View style={s.scoreCols}>
        {played.map(([a, b], i) => (
          <View key={i} style={s.scoreCol}>
            <Text style={s.scoreNum}>{a}</Text>
            <Text style={s.scoreNumTheirs}>{b}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

/** Copy is client-owned and still in fog — these are placeholders that carry the FACTS. */
function LINES(
  screen: VariantProps['screen'],
  f: VariantProps['fixture'],
): readonly (readonly [0 | 1, string])[] {
  switch (screen) {
    case 'enter':
      return [
        [1, 'Everybody turned up and the court is settled'],
        [0, `Enter it by ${f.entryDeadline} or the match counts as an evening with no result`],
        [0, 'A score typed on court is a score nobody argues about'],
      ];
    case 'asked':
      return [
        [0, `If nobody on your side answers, this stands at ${f.standsAt} — in ${f.standsIn}`],
        [0, 'One tap from either of you settles it'],
        [0, 'A modification always carries a score of its own'],
      ];
    case 'waiting':
      return [
        [1, `Sent ${f.enteredAt}. You can change it until they answer`],
        [0, `If they say nothing it stands at ${f.standsAt} — in ${f.standsIn}`],
        [0, 'If they propose something else, only an acceptance settles it'],
      ];
    case 'counter':
      return [
        [0, 'Both scores then stand until one side accepts the other'],
        [0, `If neither of you does by ${f.standsAt}, the match counts as an evening`],
      ];
    case 'unscored':
      return [
        [1, 'It is in your history and in how much you have played'],
        [1, 'You have now played with these three'],
        [0, 'Nobody lost anything, and nobody’s level moved'],
      ];
  }
}

const s = StyleSheet.create({
  card: { backgroundColor: theme.color.night, borderRadius: theme.radius.cardDark, padding: 13 },
  headRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 3,
    paddingHorizontal: 7,
    borderRadius: theme.radius.tag,
    backgroundColor: 'rgba(255,255,255,0.17)',
  },
  toneDot: { width: 6, height: 6 },
  tagLabel: { ...theme.type.tag, color: theme.color.surface },
  eyebrowOnDark: { ...theme.type.eyebrow, color: theme.color.onDarkEyebrow },

  identRow: { flexDirection: 'row', alignItems: 'flex-start' },
  identLeft: { minWidth: 0, flex: 1 },
  identRight: { flexShrink: 0, alignItems: 'flex-end' },
  // MISSING TOKEN: 30pt Archivo 700 — recorded by #11, still absent.
  startTime: {
    fontFamily: theme.font.sans[700],
    fontSize: 30,
    letterSpacing: -1.05,
    lineHeight: 30,
    color: theme.color.surface,
    ...theme.tabular,
  },
  whenLine: {
    fontFamily: theme.font.sans[600],
    fontSize: 12,
    lineHeight: 16,
    color: theme.color.surface,
    marginTop: 2,
  },
  tinyOnDark: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  seatCount: {
    fontFamily: theme.font.mono[400],
    fontSize: 11,
    lineHeight: 16,
    color: theme.color.onDarkTiny,
    marginTop: 3,
    ...theme.tabular,
  },

  hair: {
    marginTop: theme.space.sm,
    paddingTop: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: theme.color.onDarkHair,
  },
  attrib: {
    fontFamily: theme.font.sans[700],
    fontSize: 8.5,
    letterSpacing: 1.28,
    lineHeight: 11,
    color: theme.color.onDarkEyebrow,
    marginBottom: 6,
  },

  scoreLine: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  scoreNames: { flex: 1, minWidth: 0, gap: 2 },
  scoreNameMine: { ...theme.type.rlValue, color: theme.color.surface },
  scoreNameTheirs: { ...theme.type.rlLabel, color: theme.color.onDarkTiny },
  scoreCols: { flexDirection: 'row', gap: 10, flexShrink: 0 },
  scoreCol: { alignItems: 'center', gap: 2 },
  // MISSING TOKEN: the score wants a display figure. `num.m` (17) is the closest.
  scoreNum: { ...theme.num.m, color: theme.color.surface, ...theme.tabular },
  scoreNumTheirs: { ...theme.num.m, color: theme.color.onDarkTiny, ...theme.tabular },

  onTable: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: theme.radius.avatar,
    padding: 8,
    marginBottom: theme.space.sm,
  },
  onTableLabel: {
    fontFamily: theme.font.sans[700],
    fontSize: 8.5,
    letterSpacing: 1.28,
    color: theme.color.onDarkEyebrow,
  },
  onTableScore: { ...theme.num.s, color: theme.color.surface, marginTop: 3, ...theme.tabular },

  unscoredLead: {
    fontFamily: theme.font.sans[700],
    fontSize: 15,
    letterSpacing: -0.38,
    lineHeight: 20,
    color: theme.color.surface,
  },

  line: { flexDirection: 'row', gap: 7, paddingVertical: 2, alignItems: 'flex-start' },
  check: { fontSize: 10, lineHeight: 15, color: theme.color.volt },
  ring: {
    width: 7,
    height: 7,
    borderRadius: 4,
    borderWidth: 1.5,
    borderColor: 'rgba(255,255,255,0.75)',
    marginTop: 4,
  },
  lineText: { ...theme.type.tiny, color: 'rgba(255,255,255,0.92)', flex: 1 },

  actions: { flexDirection: 'row', gap: 7, marginTop: 11 },
  grow: { flex: 1 },
  cta: {
    height: theme.size.btn,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.coralInk,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
  },
  ctaOff: { backgroundColor: 'rgba(255,255,255,0.17)' },
  ctaLabel: { ...theme.type.btn, color: theme.color.surface, textAlign: 'center' },
  ctaGhost: {
    height: theme.size.btn,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.onDarkFill,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
  },
  ctaGhostLabel: { ...theme.type.btn, color: theme.color.surface, textAlign: 'center' },
  iconBtn: {
    width: 40,
    height: theme.size.btn,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.onDarkFill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconGlyph: { fontSize: 13, color: theme.color.surface },
});
