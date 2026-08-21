/**
 * THROWAWAY PROTOTYPE — issue #24. Not production.
 *
 * VARIANT C — **a result screen.** A route of its own; the Now card is a tap target.
 *
 * The argument: four people, two sides and up to 48 hours is a conversation, and this is
 * the only version where it is drawn as one. The screen names both sides, shows the
 * proposal as a table rather than a string, and — the thing neither other variant can do
 * — shows the counter and the original SIDE BY SIDE, which is what "either side can
 * accept the other's" actually looks like. It is also the only one with room for a
 * settled result to say what it was worth, the day the rating context can tell it.
 *
 * What it costs: a player is taken off Now to answer a card that was already on Now, and
 * the screen is empty most of the time it exists. And it is a route the app does not have
 * — every other variant ships nothing new.
 */

import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { SHAPE, refuse, type Leg, type Side } from './data';
import { ScoreGrid } from './ScoreGrid';
import type { VariantProps } from './types';

export function VariantC({ fixture, screen, draft, setDraft }: VariantProps) {
  const shape = SHAPE[fixture.sport];
  const entering = screen === 'enter' || screen === 'counter';
  const problem = entering ? refuse(draft) : null;

  return (
    <View style={s.screen}>
      <View style={s.header}>
        <Pressable style={s.back} accessibilityRole="button" accessibilityLabel="Back to Now">
          <Text style={s.backGlyph}>‹</Text>
        </Pressable>
        <View style={s.headerText}>
          <Text style={s.eyebrow}>
            {fixture.whenLabel.toUpperCase()} · {fixture.clubName.toUpperCase()}
          </Text>
          <Text style={s.title}>
            {screen === 'enter'
              ? 'The score'
              : screen === 'counter'
                ? 'Propose a modification'
                : screen === 'unscored'
                  ? 'No result'
                  : screen === 'waiting'
                    ? 'Sent — waiting'
                    : 'Is that right?'}
          </Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={s.body} showsVerticalScrollIndicator={false}>
        {screen === 'unscored' ? (
          <View>
            <Text style={s.lead}>
              Nobody wrote a score down, so this one counted as an evening.
            </Text>
            <View style={s.factList}>
              {[
                'It is in your history, and in how much you have played',
                `You have now played with ${fixture.sides[1].label}`,
                'It moved nobody’s level, and nobody lost anything',
                'It was a counted match, not a friendly',
              ].map((t) => (
                <View key={t} style={s.factRow}>
                  <View style={s.factDot} />
                  <Text style={s.factText}>{t}</Text>
                </View>
              ))}
            </View>
          </View>
        ) : null}

        {screen === 'asked' || screen === 'waiting' ? (
          <>
            <Text style={s.attrib}>
              {screen === 'asked'
                ? `${fixture.proposer} entered this · ${fixture.enteredAt}`
                : `You entered this · ${fixture.enteredAt}`}
            </Text>
            <ScoreTable legs={fixture.proposed} sides={fixture.sides} emphasise />
            <View style={s.clock}>
              <Text style={s.clockBig}>{fixture.standsIn}</Text>
              <Text style={s.clockText}>
                {screen === 'asked'
                  ? `until this becomes the result. Nobody has to do anything — it stands at ${fixture.standsAt}.`
                  : `${fixture.sides[1].label} have until ${fixture.standsAt}. Silence confirms it.`}
              </Text>
            </View>
            <Text style={s.small}>
              {screen === 'asked'
                ? 'One tap from either of you settles it now. A modification always carries a score of its own — there is no way to just say no.'
                : 'You can change what you sent until they answer. If they propose something else, only an acceptance settles it.'}
            </Text>
          </>
        ) : null}

        {entering ? (
          <>
            {screen === 'counter' ? (
              <>
                <Text style={s.attrib}>
                  {fixture.proposer.toUpperCase()}’S — STILL ON THE TABLE
                </Text>
                <ScoreTable legs={fixture.proposed} sides={fixture.sides} emphasise={false} />
                <Text style={s.attribGap}>YOURS</Text>
              </>
            ) : null}
            <ScoreGrid
              shape={shape}
              sides={fixture.sides}
              value={draft}
              onChange={setDraft}
              surface="paper"
            />
            <Text style={s.small}>
              {screen === 'counter'
                ? `Both scores then stand, and either side can accept the other’s. If neither of you does by ${fixture.standsAt}, the match counts as an evening with no result.`
                : `Once you send this, ${fixture.sides[1].label} have 24 hours to answer. If they say nothing, it becomes the result.`}
            </Text>
          </>
        ) : null}
      </ScrollView>

      <View style={s.footer}>
        {screen === 'asked' ? (
          <>
            <Pressable style={[s.secondary, s.grow]} accessibilityRole="button">
              <Text style={s.secondaryLabel}>Propose a modification</Text>
            </Pressable>
            <Pressable style={[s.primary, s.grow]} accessibilityRole="button">
              <Text style={s.primaryLabel}>That’s right</Text>
            </Pressable>
          </>
        ) : null}
        {screen === 'waiting' ? (
          <Pressable style={[s.secondary, s.grow]} accessibilityRole="button">
            <Text style={s.secondaryLabel}>Change what I entered</Text>
          </Pressable>
        ) : null}
        {entering ? (
          <Pressable
            style={[s.primary, s.grow, problem !== null ? s.primaryOff : null]}
            accessibilityRole="button"
          >
            <Text style={[s.primaryLabel, problem !== null ? s.primaryLabelOff : null]}>
              {problem ?? (screen === 'counter' ? 'Propose this instead' : 'Send this score')}
            </Text>
          </Pressable>
        ) : null}
        {screen === 'unscored' ? (
          <Pressable style={[s.secondary, s.grow]} accessibilityRole="button">
            <Text style={s.secondaryLabel}>Back to Now</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

/** The score as a named table. `{inlineScore()}` is the same fact with the names cut off. */
function ScoreTable({
  legs,
  sides,
  emphasise,
}: {
  readonly legs: readonly Leg[];
  readonly sides: readonly [Side, Side];
  readonly emphasise: boolean;
}) {
  const played = legs.filter(([a, b]) => a !== null && b !== null);
  return (
    <View style={[s.table, emphasise ? null : s.tableQuiet]}>
      {([0, 1] as const).map((col) => {
        const won = played.filter((l) => (l[col] as number) > (l[1 - col] as number)).length;
        const lost = played.length - won;
        return (
          <View key={col} style={s.tableRow}>
            <Text style={[s.tableName, sides[col].mine ? s.tableNameMine : null]} numberOfLines={1}>
              {sides[col].label}
            </Text>
            {played.map((leg, i) => (
              <Text
                key={i}
                style={[
                  emphasise ? s.tableNum : s.tableNumQuiet,
                  (leg[col] as number) > (leg[1 - col] as number) ? s.tableNumWon : null,
                ]}
              >
                {leg[col]}
              </Text>
            ))}
            {won > lost ? <Text style={s.winMark}>✓</Text> : <Text style={s.winMarkOff} />}
          </View>
        );
      })}
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingBottom: theme.space.md,
  },
  back: {
    width: 32,
    height: 32,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backGlyph: { fontSize: 18, color: theme.color.ink, lineHeight: 20 },
  headerText: { flex: 1, minWidth: 0 },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted },
  title: { ...theme.type.h1, color: theme.color.ink, marginTop: 2 },

  body: { paddingBottom: theme.space.xl },
  lead: { ...theme.type.h2, color: theme.color.ink, marginBottom: theme.space.md },
  attrib: { ...theme.type.tiny, color: theme.color.muted, marginBottom: theme.space.sm },
  attribGap: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    marginTop: theme.space.lg,
    marginBottom: theme.space.sm,
  },

  table: {
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.color.line,
    padding: theme.space.md,
    gap: theme.space.xs,
  },
  tableQuiet: { backgroundColor: theme.color.paper2, borderColor: 'transparent' },
  tableRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  tableName: { ...theme.type.rlLabel, color: theme.color.muted, flex: 1, minWidth: 0 },
  tableNameMine: { ...theme.type.rlValue, color: theme.color.ink },
  tableNum: {
    ...theme.num.l,
    color: theme.color.muted,
    width: 24,
    textAlign: 'center',
    ...theme.tabular,
  },
  tableNumQuiet: {
    ...theme.num.s,
    color: theme.color.muted,
    width: 24,
    textAlign: 'center',
    ...theme.tabular,
  },
  tableNumWon: { color: theme.color.ink },
  winMark: { width: 16, textAlign: 'center', color: theme.color.mint, fontSize: 12 },
  winMarkOff: { width: 16 },

  clock: {
    flexDirection: 'row',
    gap: theme.space.md,
    alignItems: 'center',
    marginTop: theme.space.lg,
  },
  clockBig: { ...theme.num.levelLarge, color: theme.color.coralInk, ...theme.tabular },
  clockText: { ...theme.type.rlLabel, color: theme.color.ink, flex: 1 },
  small: { ...theme.type.tiny, color: theme.color.muted, marginTop: theme.space.md },

  factList: { gap: theme.space.sm },
  factRow: { flexDirection: 'row', gap: theme.space.sm, alignItems: 'flex-start' },
  factDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: theme.color.line,
    marginTop: 6,
  },
  factText: { ...theme.type.rlLabel, color: theme.color.ink, flex: 1 },

  footer: {
    flexDirection: 'row',
    gap: theme.space.xs,
    paddingTop: theme.space.md,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: theme.color.line,
  },
  grow: { flex: 1 },
  primary: {
    height: theme.size.btnXl,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.coralInk,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  primaryOff: { backgroundColor: theme.color.line2 },
  primaryLabel: { ...theme.type.btn, color: theme.color.surface, textAlign: 'center' },
  primaryLabelOff: { color: theme.color.muted },
  secondary: {
    height: theme.size.btnXl,
    borderRadius: theme.radius.btn,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  secondaryLabel: { ...theme.type.btn, color: theme.color.ink, textAlign: 'center' },
});
