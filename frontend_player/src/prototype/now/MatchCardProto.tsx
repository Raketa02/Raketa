/**
 * THROWAWAY PROTOTYPE — issue #11. Not production.
 *
 * `MatchCard` per UI spec §B8, plus the `FitBadge` (§B9) as ADR-0037 settled it: always a
 * number, clamped 20–99 at display time, emphatic only when the server says so.
 *
 * It is here because three of the ticket's questions only have an answer on a LIGHT
 * surface: the light court glyph, the `idle` tone dot (§E5 measures it at ~1.0:1 on a
 * white tag — invisible), and the tag row that wraps when a badge and a card discount
 * coexist.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { CourtGlyph } from './CourtGlyph';
import type { SeatSym, Tone } from './data';

const TONE_LIGHT: Record<Tone, string> = {
  good: theme.color.mint,
  watch: theme.color.coral,
  time: theme.color.amber,
  ended: theme.color.red,
  // §E5: this is the defect. Left as v37 states it so it can be seen not to be there.
  idle: 'rgba(255,255,255,0.45)',
  bad: 'transparent',
};

export interface FeedItem {
  readonly when: string;
  readonly badge?: string;
  readonly club: string;
  readonly travel: number;
  readonly sport: 'padel' | 'tennis' | 'squash' | 'badminton';
  readonly format: string;
  readonly counts: boolean;
  readonly cardOff?: string;
  readonly seats: readonly SeatSym[];
  readonly filled: number;
  readonly capacity: number;
  readonly fit: number;
  readonly emphatic: boolean;
  readonly stateTag: string;
  readonly stateTone: Tone;
  readonly strike?: string;
  readonly payable: string;
}

export function MatchCardProto({
  item,
  fixContrast,
}: {
  readonly item: FeedItem;
  readonly fixContrast: boolean;
}) {
  return (
    <Pressable
      style={s.card}
      accessibilityRole="button"
      accessibilityLabel={`${item.when} at ${item.club}, ${item.filled} of ${item.capacity} seats paid`}
      onPress={() => {}}
    >
      <View style={s.top}>
        <View style={s.left}>
          <View style={s.titleRow}>
            <Text style={s.when}>{item.when}</Text>
            {item.badge !== undefined ? (
              <View style={[s.tag, s.tagHot]}>
                <Text style={[s.tagLabel, s.tagHotLabel]}>{item.badge}</Text>
              </View>
            ) : null}
          </View>
          <Text style={s.tiny}>
            {item.club} · {item.travel} min
          </Text>
          <View style={s.tagRow}>
            <View style={s.tag}>
              <View style={[s.dot, { backgroundColor: theme.sport[item.sport] }]} />
              <Text style={s.tagLabel}>{cap(item.sport)}</Text>
            </View>
            <View style={s.tag}>
              <Text style={s.tagLabel}>{item.format}</Text>
            </View>
            <View style={[s.tag, item.counts ? s.tagHot : null]}>
              <Text style={[s.tagLabel, item.counts ? s.tagHotLabel : null]}>
                {item.counts ? 'Counts' : 'Friendly'}
              </Text>
            </View>
            {item.cardOff !== undefined ? (
              <View style={[s.tag, s.tagOk]}>
                <Text style={[s.tagLabel, s.tagOkLabel]}>{item.cardOff}</Text>
              </View>
            ) : null}
          </View>
        </View>
        <View style={s.right}>
          <CourtGlyph
            sport={item.sport}
            seats={item.seats}
            w={46}
            dark={false}
            fixContrast={fixContrast}
          />
          <Text style={s.seatCount}>
            {item.filled}/{item.capacity}
          </Text>
        </View>
      </View>

      <View style={s.foot}>
        <View style={s.footLeft}>
          <View style={[s.fit, item.emphatic ? s.fitHi : null]}>
            <Text style={[s.fitLabel, item.emphatic ? s.fitHiLabel : null]}>
              ✦ {clamp(item.fit)}
            </Text>
          </View>
          <View style={s.tag}>
            <View style={[s.dot, s.round, { backgroundColor: TONE_LIGHT[item.stateTone] }]} />
            <Text style={s.tagLabel} numberOfLines={1}>
              {item.stateTag}
            </Text>
          </View>
        </View>
        <View style={s.footRight}>
          {item.strike !== undefined ? <Text style={s.strike}>{item.strike}</Text> : null}
          <Text style={s.payable}>{item.payable}</Text>
          <Text style={s.tiny}> · 0 fee</Text>
        </View>
      </View>
    </Pressable>
  );
}

const clamp = (n: number) => Math.max(20, Math.min(99, Math.round(n)));
const cap = (v: string) => v.charAt(0).toUpperCase() + v.slice(1);

const s = StyleSheet.create({
  card: {
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.color.line,
    // MISSING TOKEN: the match card's padding is 11.
    padding: 11,
    marginBottom: theme.space.sm,
  },
  top: { flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
  left: { flex: 1, minWidth: 0 },
  right: { flexShrink: 0, alignItems: 'flex-end' },
  titleRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 5, alignItems: 'center' },
  when: {
    fontFamily: theme.font.mono[600],
    fontSize: 12,
    color: theme.color.ink,
    ...theme.tabular,
  },
  tiny: { ...theme.type.tiny, color: theme.color.muted, marginTop: 2 },
  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 5, marginTop: 6 },
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 3,
    paddingHorizontal: 7,
    borderRadius: theme.radius.tag,
    backgroundColor: theme.color.line2,
    alignSelf: 'flex-start',
  },
  tagHot: { backgroundColor: theme.color.coralSoft },
  tagOk: { backgroundColor: theme.color.mintSoft },
  tagLabel: { ...theme.type.tag, color: theme.color.muted },
  tagHotLabel: { color: theme.color.coralInk },
  tagOkLabel: { color: theme.color.mintInk },
  dot: { width: 6, height: 6 },
  round: { borderRadius: 3 },
  seatCount: {
    fontFamily: theme.font.mono[400],
    fontSize: 11,
    lineHeight: 16,
    color: theme.color.muted,
    marginTop: 3,
    ...theme.tabular,
  },
  foot: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 6,
    marginTop: theme.space.sm,
    paddingTop: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: theme.color.line2,
  },
  footLeft: { flexDirection: 'row', alignItems: 'center', gap: 5, flex: 1, minWidth: 0 },
  footRight: { flexDirection: 'row', alignItems: 'baseline', flexShrink: 0 },
  fit: {
    height: theme.size.fit,
    paddingHorizontal: 9,
    borderRadius: theme.radius.fit,
    backgroundColor: theme.color.night,
    justifyContent: 'center',
  },
  // Rule C again: v37's `.hi` is white on coral (3.89). ADR-0012 forbids it.
  fitHi: { backgroundColor: theme.color.coralInk },
  fitLabel: { ...theme.type.tag, color: theme.color.surface },
  fitHiLabel: { color: theme.color.surface },
  strike: {
    ...theme.type.tiny,
    color: theme.color.muted,
    textDecorationLine: 'line-through',
    marginRight: 5,
  },
  payable: {
    // MISSING FAMILY: v37 asks for Plex Mono 700 here (14/700). `theme.font.mono` loads
    // 400/500/600 only, and weight is a family name on Android — so 700 is unreachable,
    // not merely unwritten. Falls back to 600. See C8.
    fontFamily: theme.font.mono[600],
    fontSize: 14,
    letterSpacing: -0.49,
    color: theme.color.ink,
    ...theme.tabular,
  },
});
