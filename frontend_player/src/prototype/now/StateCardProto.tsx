/**
 * THROWAWAY PROTOTYPE — issue #11. Not production.
 *
 * `StateCard` per UI spec §B5, six slots in DOM order, on the real kit.
 *
 * Every style below comes from `theme` EXCEPT the ones marked `MISSING TOKEN`. Those are
 * the answer to the ticket's question 5 and are deliberately written as literals here so
 * they show up in a grep: a literal in a production component is a bug (ADR-0012), so
 * each one is a value the theme has to grow before this card can be built for real.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { CourtGlyph } from './CourtGlyph';
import type { ProtoState, Tone } from './data';
import { TouchBox } from './TouchBox';

/** UI spec §A1.3 `ST_TONE` — the only place tone becomes pixels. */
const TONE_DOT: Record<Tone, string> = {
  good: theme.color.mint,
  watch: theme.color.coral,
  time: theme.color.amber,
  ended: theme.color.red,
  // v37: rgba(255,255,255,.45). On the on-dark tag that is legible; §E5 records it as
  // invisible on a LIGHT tag, which is where the match card puts it.
  idle: 'rgba(255,255,255,0.45)',
  // §B6.3 ⚠ `inventoryLost` declares tone 'bad' and ST_TONE has no 'bad' key, so the
  // dot renders with `background: undefined`. Reproduced as transparent, on purpose.
  bad: 'transparent',
};

export interface StateCardProtoProps {
  readonly state: ProtoState;
  readonly showTouch: boolean;
  readonly fixContrast: boolean;
}

export function StateCardProto({ state, showTouch, fixContrast }: StateCardProtoProps) {
  return (
    <View style={s.card}>
      {/* 1 — header row */}
      <View style={s.headRow}>
        <View style={s.tag}>
          <View style={[s.toneDot, { backgroundColor: TONE_DOT[state.tone] }]} />
          <Text style={s.tagLabel} numberOfLines={1}>
            {state.tag}
          </Text>
        </View>
        <Text style={s.eyebrowOnDark} numberOfLines={1}>
          {cap(state.sport)} · {state.format}
        </Text>
      </View>

      {/* 2 — identity row */}
      <View style={s.identRow}>
        <View style={s.identLeft}>
          <Text style={s.startTime}>{state.startTime}</Text>
          <Text style={s.whenLine}>
            {state.whenLabel} · {state.clubName}
          </Text>
          <Text style={s.tinyOnDark}>
            {state.courtLabel} · {state.durationMin} min
          </Text>
        </View>
        <View style={s.identRight}>
          <CourtGlyph
            sport={state.sport}
            seats={state.seats}
            w={58}
            dark
            fixContrast={fixContrast}
          />
          <Text style={s.seatCount}>
            {state.filled}/{state.capacity}
          </Text>
        </View>
      </View>

      {/* 3 — facet row */}
      <View style={s.hair}>
        <View style={s.facetRow}>
          <View style={s.facet}>
            <Text style={s.facetLabel}>COURT</Text>
            <Text style={s.facetValue}>{state.court}</Text>
          </View>
          <View style={s.divider} />
          <View style={s.facet}>
            <Text style={s.facetLabel}>GROUP</Text>
            <Text style={s.facetValue}>{state.group}</Text>
          </View>
        </View>
      </View>

      {/* 4 — alert */}
      {state.alert !== undefined ? (
        <View style={s.alert}>
          <View style={s.alertDot} />
          <Text style={s.alertText}>
            {state.alert.text}
            <Text style={s.alertBold}>{state.alert.bold}</Text>
          </Text>
        </View>
      ) : null}

      {/* 5 — line list */}
      <View style={s.hair}>
        {state.lines.map(([done, text], i) => (
          <View key={i} style={s.line}>
            {done === 1 ? <Text style={s.check}>✓</Text> : <View style={s.ring} />}
            <Text style={s.lineText}>{text}</Text>
          </View>
        ))}
      </View>

      {/* 6 — action row */}
      <View style={s.actions}>
        <TouchBox show={showTouch} style={s.grow}>
          <Pressable
            style={s.cta}
            accessibilityRole="button"
            accessibilityLabel="Open match"
            hitSlop={theme.hit.btn}
            onPress={() => {}}
          >
            <Text style={s.ctaLabel}>Open match</Text>
          </Pressable>
        </TouchBox>
        <TouchBox show={showTouch}>
          <Pressable
            style={s.iconBtn}
            accessibilityRole="button"
            accessibilityLabel="Open inbox"
            hitSlop={{ top: 5, bottom: 5, left: 2, right: 2 }}
            onPress={() => {}}
          >
            <Text style={s.iconGlyph}>✉</Text>
          </Pressable>
        </TouchBox>
        {state.post === true ? null : (
          <TouchBox show={showTouch}>
            <Pressable
              style={s.iconBtn}
              accessibilityRole="button"
              accessibilityLabel="Getting in — door code and QR"
              hitSlop={{ top: 5, bottom: 5, left: 2, right: 2 }}
              onPress={() => {}}
            >
              <Text style={s.iconGlyph}>⌘</Text>
            </Pressable>
          </TouchBox>
        )}
      </View>
    </View>
  );
}

function cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const s = StyleSheet.create({
  card: {
    backgroundColor: theme.color.night,
    borderRadius: theme.radius.cardDark,
    // MISSING TOKEN: the state card's padding is 13, and `space` has 12 and 15. The 3pt
    // grid ADR-0012 adopted does not contain 13. See conflicts C7.
    padding: 13,
    flex: 1,
  },

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
    // v37 `.tag.w` is rgba(255,255,255,.17). `theme.color.onDarkTag` is .14 — see C6.
    backgroundColor: 'rgba(255,255,255,0.17)',
    flexShrink: 1,
  },
  // v37 draws this ROUND (border-radius 3 on a 6px box). The shipped `Tag` draws its dot
  // SQUARE and reserves the round form for the sport dot. See C5.
  toneDot: { width: 6, height: 6, borderRadius: 3 },
  tagLabel: { ...theme.type.tag, color: theme.color.surface },
  eyebrowOnDark: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
    flexShrink: 0,
  },

  identRow: { flexDirection: 'row', alignItems: 'flex-start' },
  identLeft: { minWidth: 0, flex: 1 },
  identRight: { flexShrink: 0, alignItems: 'flex-end' },
  startTime: {
    // MISSING TOKEN: 30pt Archivo 700, tracking -.035em = -1.05pt, lineHeight 1.
    // `theme.num` is entirely IBM Plex Mono; there is no 30pt Archivo display role.
    fontFamily: theme.font.sans[700],
    fontSize: 30,
    letterSpacing: -1.05,
    lineHeight: 30,
    color: theme.color.surface,
    ...theme.tabular,
  },
  whenLine: {
    // MISSING TOKEN: 12pt Archivo 600. `theme.type.inlineTitle` is 12.5/600.
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
  facetRow: { flexDirection: 'row', gap: 10 },
  facet: { flex: 1, minWidth: 0 },
  divider: { width: StyleSheet.hairlineWidth, backgroundColor: theme.color.onDarkHair },
  facetLabel: {
    // MISSING TOKEN: 8.5pt eyebrow. `theme.type.eyebrow` is 9.5 — §E5 already records
    // the 8.5 on-dark eyebrow at 4.3:1, failing at that size.
    fontFamily: theme.font.sans[700],
    fontSize: 8.5,
    letterSpacing: 1.28,
    lineHeight: 11,
    color: theme.color.onDarkEyebrow,
  },
  facetValue: {
    // MISSING TOKEN: 11 × 1.35 = 14.85. `theme.type.tiny` is 11/16 (1.45).
    fontFamily: theme.font.sans[600],
    fontSize: 11,
    lineHeight: 14.85,
    color: theme.color.surface,
    marginTop: 2,
  },

  alert: {
    flexDirection: 'row',
    gap: 7,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: theme.radius.avatar,
    // MISSING TOKEN: #D64D3A at 16% / 40%. That is NOT `theme.color.red` (#B4392C).
    backgroundColor: 'rgba(214,77,58,0.16)',
    borderWidth: 1,
    borderColor: 'rgba(214,77,58,0.4)',
    marginTop: theme.space.sm,
    alignItems: 'flex-start',
  },
  alertDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: theme.color.red,
    marginTop: 4,
  },
  alertText: { ...theme.type.tiny, color: theme.color.surface, flex: 1 },
  alertBold: { fontFamily: theme.font.sans[700] },

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

  actions: { flexDirection: 'row', gap: 7, marginTop: 11, flexWrap: 'nowrap' },
  grow: { flex: 1 },
  cta: {
    height: theme.size.btn,
    borderRadius: theme.radius.btn,
    // ADR-0012 Rule C: white never sits on coral (3.89). The v37 primary is coral+white.
    backgroundColor: theme.color.coralInk,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 14,
  },
  ctaLabel: { ...theme.type.btn, color: theme.color.surface },
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
