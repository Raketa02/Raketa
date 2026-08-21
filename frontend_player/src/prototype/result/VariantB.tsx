/* eslint-disable no-restricted-syntax --
 * THROWAWAY PROTOTYPE. The rule is right and the literals below are the POINT: every one
 * is a value `theme.ts` cannot express yet, marked `MISSING TOKEN`, and the list of them
 * is part of this ticket's answer. A literal in a production component stays a bug.
 */
/**
 * THROWAWAY PROTOTYPE — issue #24. Not production.
 *
 * VARIANT B — **a sheet over Now.** One modal surface, no route.
 *
 * The argument: the card's job is to say a result is waiting; the sheet's job is the
 * conversation. It buys the two things the card cannot give — a full-width pad, and room
 * for the consequence as a sentence rather than a fact line — while keeping the player on
 * Now, which matters because the whole prompt is a card and a badge (`§9`, in-app only)
 * and a player who lands somewhere else has lost the rest of their home screen.
 *
 * The sheet is drawn here rather than mounted through `shared/ui/BottomSheet` because the
 * prototype frames itself at a fixed width and a Modal escapes the frame. Geometry inside
 * the frame is what is being judged; the real screen would use the shipped component.
 *
 * What to look hard at: this is the only variant where the score you are being asked
 * about is hidden behind a tap. A player who never opens the sheet still gets bound by it.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { SHAPE, inlineScore, refuse } from './data';
import { ScoreGrid } from './ScoreGrid';
import type { VariantProps } from './types';

export function VariantB({ fixture, screen, draft, setDraft }: VariantProps) {
  const shape = SHAPE[fixture.sport];
  const entering = screen === 'enter' || screen === 'counter';
  const problem = entering ? refuse(draft) : null;

  return (
    <View style={s.stage}>
      {/* The card underneath: a prompt, and nothing else. Everything the old card put in
          fact lines is now the sheet's, so this shrinks to four rows. */}
      <View style={s.card}>
        <View style={s.tagRow}>
          <View style={s.tag}>
            <View style={s.toneDot} />
            <Text style={s.tagLabel}>
              {screen === 'enter'
                ? 'Needs result'
                : screen === 'unscored'
                  ? 'Played'
                  : 'Confirm the result'}
            </Text>
          </View>
          <Text style={s.eyebrowOnDark}>
            {fixture.whenLabel.toUpperCase()} · {fixture.clubName.toUpperCase()}
          </Text>
        </View>
        <Text style={s.prompt}>
          {screen === 'enter'
            ? 'How did it go?'
            : screen === 'waiting'
              ? `You said ${inlineScore(fixture.proposed)}`
              : screen === 'unscored'
                ? 'No score — it counted as an evening'
                : `${fixture.proposer} said ${inlineScore(fixture.proposed)}`}
        </Text>
        <Text style={s.promptSub}>
          {screen === 'enter'
            ? `Nobody has entered a score yet · until ${fixture.entryDeadline}`
            : screen === 'unscored'
              ? 'Nobody lost anything'
              : `Stands at ${fixture.standsAt} unless somebody answers`}
        </Text>
        <Pressable style={s.cardCta} accessibilityRole="button">
          <Text style={s.cardCtaLabel}>
            {screen === 'enter'
              ? 'Enter the score'
              : screen === 'unscored'
                ? 'Open match'
                : screen === 'waiting'
                  ? 'Change it'
                  : 'Check it'}
          </Text>
        </Pressable>
      </View>

      {screen === 'unscored' ? null : (
        <>
          <View style={s.scrim} />
          <View style={s.sheet}>
            <View style={s.grabber} />
            <View style={s.sheetHead}>
              <Text style={s.sheetTitle}>
                {screen === 'enter'
                  ? 'The score'
                  : screen === 'counter'
                    ? 'Propose a modification'
                    : screen === 'waiting'
                      ? 'Waiting on the other side'
                      : 'Is that right?'}
              </Text>
              <Pressable style={s.close} accessibilityRole="button" accessibilityLabel="Close">
                <Text style={s.closeGlyph}>✕</Text>
              </Pressable>
            </View>

            {screen === 'asked' || screen === 'waiting' ? (
              <View style={s.bigScore}>
                <Text style={s.bigScoreAttrib}>
                  {screen === 'asked'
                    ? `${fixture.proposer} entered this at ${fixture.enteredAt}`
                    : `You entered this at ${fixture.enteredAt}`}
                </Text>
                <View style={s.grid}>
                  {(
                    [
                      [fixture.sides[0].label, 0],
                      [fixture.sides[1].label, 1],
                    ] as const
                  ).map(([label, col]) => (
                    <View key={label} style={s.gridRow}>
                      <Text
                        style={[s.gridName, col === 0 ? s.gridNameMine : null]}
                        numberOfLines={1}
                      >
                        {label}
                      </Text>
                      {fixture.proposed
                        .filter(([a, b]) => a !== null && b !== null)
                        .map((leg, i) => (
                          <Text key={i} style={s.gridNum}>
                            {leg[col]}
                          </Text>
                        ))}
                    </View>
                  ))}
                </View>
              </View>
            ) : null}

            {entering ? (
              <>
                {screen === 'counter' ? (
                  <View style={s.onTable}>
                    <Text style={s.onTableText}>
                      {fixture.proposer}’s {inlineScore(fixture.proposed)} stays on the table.
                      Either side can still accept the other’s.
                    </Text>
                  </View>
                ) : null}
                <ScoreGrid
                  shape={shape}
                  sides={fixture.sides}
                  value={draft}
                  onChange={setDraft}
                  surface="paper"
                />
              </>
            ) : null}

            {/* The consequence, as a sentence. This is what the sheet is FOR. */}
            <View style={s.note}>
              <Text style={s.noteText}>
                {screen === 'asked'
                  ? `If nobody on your side answers, this becomes the result at ${fixture.standsAt} — in ${fixture.standsIn}. One tap from you or Marta settles it now.`
                  : screen === 'waiting'
                    ? `${fixture.sides[1].label} have until ${fixture.standsAt}. If they say nothing, this stands. If they propose something else, only an acceptance settles it.`
                    : screen === 'counter'
                      ? `Both scores then stand. If neither side accepts by ${fixture.standsAt}, the match counts as an evening and no result.`
                      : `Once you send this, ${fixture.sides[1].label} have 24 hours. Silence confirms it.`}
              </Text>
            </View>

            <View style={s.sheetActions}>
              {screen === 'asked' ? (
                <>
                  <Pressable style={[s.primary, s.grow]} accessibilityRole="button">
                    <Text style={s.primaryLabel}>That’s right</Text>
                  </Pressable>
                  <Pressable style={[s.secondary, s.grow]} accessibilityRole="button">
                    <Text style={s.secondaryLabel}>Propose a modification</Text>
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
            </View>
          </View>
        </>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  stage: { flex: 1 },

  card: { backgroundColor: theme.color.night, borderRadius: theme.radius.cardDark, padding: 13 },
  tagRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 },
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 3,
    paddingHorizontal: 7,
    borderRadius: theme.radius.tag,
    backgroundColor: 'rgba(255,255,255,0.17)',
  },
  toneDot: { width: 6, height: 6, backgroundColor: theme.color.coral },
  tagLabel: { ...theme.type.tag, color: theme.color.surface },
  eyebrowOnDark: { ...theme.type.eyebrow, color: theme.color.onDarkEyebrow, flexShrink: 1 },
  prompt: { ...theme.type.h1, color: theme.color.surface },
  promptSub: { ...theme.type.tiny, color: theme.color.onDarkTiny, marginTop: 3 },
  cardCta: {
    height: theme.size.btn,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.coralInk,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: theme.space.md,
  },
  cardCtaLabel: { ...theme.type.btn, color: theme.color.surface },

  scrim: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.scrim },
  sheet: {
    position: 'absolute',
    left: -theme.space.lg,
    right: -theme.space.lg,
    bottom: 0,
    backgroundColor: theme.color.surface,
    borderTopLeftRadius: theme.radius.sheet,
    borderTopRightRadius: theme.radius.sheet,
    paddingHorizontal: theme.space.lg,
    paddingTop: theme.space.sm,
    paddingBottom: theme.space.xxl,
  },
  grabber: {
    width: 36,
    height: 4,
    borderRadius: 2,
    backgroundColor: theme.color.line,
    alignSelf: 'center',
    marginBottom: theme.space.sm,
  },
  sheetHead: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.space.md,
  },
  sheetTitle: { ...theme.type.h1, color: theme.color.ink, flex: 1 },
  close: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: theme.color.paper2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeGlyph: { fontSize: 12, color: theme.color.muted },

  bigScore: { marginBottom: theme.space.md },
  bigScoreAttrib: { ...theme.type.tiny, color: theme.color.muted, marginBottom: theme.space.sm },
  grid: { gap: 4 },
  gridRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  gridName: { ...theme.type.rlLabel, color: theme.color.muted, flex: 1, minWidth: 0 },
  gridNameMine: { ...theme.type.rlValue, color: theme.color.ink },
  gridNum: {
    ...theme.num.xl,
    color: theme.color.ink,
    width: 26,
    textAlign: 'center',
    ...theme.tabular,
  },

  onTable: {
    backgroundColor: theme.color.paper2,
    borderRadius: theme.radius.note,
    padding: theme.space.sm,
    marginBottom: theme.space.md,
  },
  onTableText: { ...theme.type.tiny, color: theme.color.muted },

  note: {
    marginTop: theme.space.md,
    borderLeftWidth: 3,
    borderLeftColor: theme.color.coral,
    backgroundColor: theme.color.coralSoft,
    borderRadius: theme.radius.note,
    padding: theme.space.md,
  },
  noteText: { ...theme.type.rlLabel, color: theme.color.ink },

  sheetActions: { flexDirection: 'row', gap: theme.space.xs, marginTop: theme.space.md },
  grow: { flex: 1 },
  primary: {
    // `size.btnXl` is documented as "42 result primary" — the theme already expected this.
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
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  secondaryLabel: { ...theme.type.btn, color: theme.color.ink, textAlign: 'center' },
});
