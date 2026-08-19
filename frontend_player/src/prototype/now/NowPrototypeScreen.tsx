/**
 * THROWAWAY PROTOTYPE — issue #11. Not production. Deleted with the branch.
 *
 * ONE LINE PLAN: Now composed on the real kit at four widths and three strip geometries,
 * switchable from a floating bar, so the conflicts between v37's stated values and React
 * Native are things you can look at rather than things you have to be told.
 *
 * ## The three strip geometries
 *
 * The question the ticket asks — "268 leaves no peek at 320pt, what is the ratio?" — is
 * asked about `.mrail`, which UI spec §D5 says Now **does not use**. Now's strip is
 * `.hstrip`, and its child is `flex: 0 0 100%` of the content box with the strip bled to
 * the screen edge. So the peek is `gutter − gap` and does not depend on the card width at
 * all. All three are drawn here so that claim is checkable rather than asserted:
 *
 *   bleed  card = content width, strip bleeds ±15   → peek 5pt at EVERY width  (v37)
 *   ratio  card = 0.74 × content width, no bleed    → peek ~26% (ADR-0012 size.railCardRatio)
 *   inset  card = content width, no bleed           → peek 0   (the naive translation)
 */

import { useMemo, useRef, useState } from 'react';
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { theme } from '@/shared/ui';

import { FEED, INITIAL_KNOBS, STATES } from './data';
import { MatchCardProto } from './MatchCardProto';
import { PrototypeBar, type Knobs } from './PrototypeBar';
import { StateCardProto } from './StateCardProto';
import { TouchBox } from './TouchBox';

const SPORTS = ['All', 'Padel', 'Tennis', 'Squash', 'Badminton'] as const;

export function NowPrototypeScreen() {
  const insets = useSafeAreaInsets();
  const device = useWindowDimensions();
  const [knobs, setKnobs] = useState<Knobs>(INITIAL_KNOBS);
  const [page, setPage] = useState(0);
  const stripRef = useRef<ScrollView>(null);

  const screenWidth = knobs.width === 'device' ? device.width : knobs.width;
  const gutter = theme.size.gutter; // 15
  const content = screenWidth - gutter * 2;

  // `.hstrip` in three geometries. `step` is what `snapToInterval` gets — the same
  // arithmetic `wireStrip()` does to find the active dot.
  const strip = useMemo(() => {
    const gap = 10;
    if (knobs.strip === 'ratio') {
      const card = Math.round(theme.size.railCardRatio * content);
      return { card, gap, step: card + gap, bleed: 0, peek: content - card - gap };
    }
    if (knobs.strip === 'inset') {
      return { card: content, gap, step: content + gap, bleed: 0, peek: 0 };
    }
    return { card: content, gap, step: content + gap, bleed: gutter, peek: gutter - gap };
  }, [knobs.strip, content]);

  const showTouch = knobs.overlay === 'touch';

  return (
    <View style={[s.stage, { paddingTop: insets.top }]}>
      <View style={[s.screen, { width: screenWidth }]}>
        <ScrollView
          style={s.scroll}
          contentContainerStyle={{ paddingBottom: 220 }}
          showsVerticalScrollIndicator={false}
        >
          {/* Header — §B1. The eyebrow's city is #11's neighbour, not its problem. */}
          <View style={[s.headBar, { paddingHorizontal: gutter }]}>
            <View style={s.headLeft}>
              <Text style={s.eyebrow}>KRAKÓW · SATURDAY · 14:30</Text>
              <Text style={s.h1}>Hi, Tomek</Text>
            </View>
            <View style={s.nowPill}>
              <Text style={s.nowPillLabel}>NOW</Text>
            </View>
          </View>

          {/* Sport filter — §B2. 25pt chips against the 44pt rule. */}
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: gutter, gap: 6, paddingBottom: 9 }}
          >
            {SPORTS.map((name, i) => (
              <TouchBox key={name} show={showTouch}>
                <View style={[s.chip, i === 0 ? s.chipOn : null]}>
                  <Text style={[s.chipLabel, i === 0 ? s.chipOnLabel : null]}>{name}</Text>
                </View>
              </TouchBox>
            ))}
          </ScrollView>

          <View style={{ paddingHorizontal: gutter }}>
            <View style={s.sect}>
              <Text style={s.sectLabel}>YOUR MATCHES · {STATES.length} · SOONEST FIRST</Text>
              <Text style={s.sectHint}>swipe →</Text>
            </View>
          </View>

          {/* The strip.
              `bleed` / `ratio` — the ScrollView spans the whole SCREEN and its content is
              inset by the gutter, which is what CSS's `margin:0 -15px; padding:0 15px`
              amounts to once the surrounding column's padding is cancelled. The card can
              therefore scroll past the gutter to the frame edge.
              `inset` — the ScrollView is clipped to the content column, so nothing ever
              crosses the gutter and there is no peek at all. */}
          <View
            style={{ paddingHorizontal: strip.bleed === 0 && knobs.strip === 'inset' ? gutter : 0 }}
          >
            <ScrollView
              ref={stripRef}
              horizontal
              snapToInterval={strip.step}
              decelerationRate="fast"
              disableIntervalMomentum
              showsHorizontalScrollIndicator={false}
              onMomentumScrollEnd={(e) =>
                setPage(Math.round(e.nativeEvent.contentOffset.x / strip.step))
              }
              contentContainerStyle={{
                paddingHorizontal: knobs.strip === 'inset' ? 0 : gutter,
                gap: strip.gap,
                paddingTop: 1,
                paddingBottom: 5,
              }}
            >
              {STATES.map((state) => (
                <View key={state.key} style={{ width: strip.card }}>
                  <StateCardProto
                    state={state}
                    showTouch={showTouch}
                    fixContrast={knobs.fixContrast}
                  />
                </View>
              ))}
            </ScrollView>
          </View>

          <View style={s.dots}>
            {STATES.map((state, i) => (
              <View key={state.key} style={[s.dot, i === page ? s.dotOn : null]} />
            ))}
          </View>

          <View style={{ paddingHorizontal: gutter }}>
            {/* MultiSport — §B11 */}
            <View style={s.multi}>
              <View style={s.multiLeft}>
                <Text style={s.h2}>MultiSport Plus</Text>
                <Text style={s.tiny}>1 of 2 entries used today · show the QR at reception</Text>
              </View>
              <View style={s.tagOk}>
                <Text style={s.tagOkLabel}>1 left</Text>
              </View>
            </View>

            <View style={s.sect}>
              <Text style={s.sectLabel}>OPEN NEAR YOU</Text>
            </View>
            {FEED.map((item, i) => (
              <MatchCardProto key={i} item={item} fixContrast={knobs.fixContrast} />
            ))}

            {/* Empty state — §B12, the second instance */}
            <View style={s.empty}>
              <Text style={s.emptyTitle}>Nothing open in your sports right now</Text>
              <Text style={s.emptyBody}>
                We do not invent players to make a city look busy. Try another day, or create a
                match.
              </Text>
            </View>
          </View>
        </ScrollView>

        {/* Tab bar — §B13. Present so the bottom geometry and the safe area are real. */}
        <View style={[s.tabbar, { paddingBottom: 12 + insets.bottom }]}>
          {['Now', 'Courts', 'Create', 'Inbox', 'You'].map((label, i) => (
            <View key={label} style={s.tab}>
              <View style={[s.tabIcon, i === 2 ? s.tabFab : null, i === 0 ? s.tabOn : null]} />
              <Text style={[s.tabLabel, i === 0 ? s.tabLabelOn : null]}>{label}</Text>
            </View>
          ))}
        </View>
      </View>

      <PrototypeBar
        knobs={knobs}
        onChange={setKnobs}
        readout={`screen ${screenWidth} · content ${content} · card ${strip.card} · peek ${strip.peek}`}
      />
    </View>
  );
}

const s = StyleSheet.create({
  // The stage exists ONLY so a clamped width has visible edges. It is not the app —
  // ADR-0012 Part 0.1 drops the phone frame. Set width to `device` and it disappears.
  stage: { flex: 1, backgroundColor: '#08222B', alignItems: 'center' },
  screen: { flex: 1, backgroundColor: theme.color.paper, overflow: 'hidden' },
  scroll: { flex: 1 },

  headBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    paddingTop: 12,
    paddingBottom: 9,
  },
  headLeft: { flex: 1, minWidth: 0 },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted },
  h1: { ...theme.type.h1, color: theme.color.ink, marginTop: 2 },
  nowPill: {
    paddingHorizontal: 9,
    height: 23,
    borderRadius: theme.radius.fit,
    backgroundColor: theme.color.line2,
    justifyContent: 'center',
  },
  nowPillLabel: { ...theme.type.tag, color: theme.color.ink },

  chip: {
    height: theme.size.chipSm,
    paddingHorizontal: 8,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    justifyContent: 'center',
  },
  chipOn: { borderColor: theme.color.ink, backgroundColor: theme.color.ink },
  chipLabel: { fontFamily: theme.font.sans[600], fontSize: 10, color: theme.color.muted },
  chipOnLabel: { color: theme.color.paper },

  sect: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginTop: 14,
    marginBottom: 7,
  },
  sectLabel: { ...theme.type.eyebrow, color: theme.color.muted },
  sectHint: { ...theme.type.tiny, color: theme.color.muted },

  dots: { flexDirection: 'row', gap: 5, justifyContent: 'center', marginTop: -2, marginBottom: 11 },
  dot: {
    width: theme.size.pagerDot,
    height: theme.size.pagerDot,
    borderRadius: 3,
    backgroundColor: theme.color.line,
  },
  dotOn: { width: theme.size.pagerDotActive, backgroundColor: theme.color.coral },

  multi: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: theme.color.mintSoft,
    borderWidth: 1,
    borderColor: theme.color.mintLine,
    borderRadius: theme.radius.card,
    padding: theme.space.md,
  },
  multiLeft: { flex: 1, minWidth: 0 },
  h2: { ...theme.type.h2, color: theme.color.ink },
  tiny: { ...theme.type.tiny, color: theme.color.muted, marginTop: 2 },
  tagOk: {
    paddingVertical: 3,
    paddingHorizontal: 7,
    borderRadius: theme.radius.tag,
    backgroundColor: theme.color.surface,
  },
  tagOkLabel: { ...theme.type.tag, color: theme.color.mintInk },

  empty: {
    alignItems: 'center',
    padding: theme.space.xl,
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
  },
  emptyTitle: { ...theme.type.cardTitle, color: theme.color.ink, marginBottom: 5 },
  emptyBody: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },

  tabbar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: theme.color.line,
    backgroundColor: theme.color.surface,
    paddingTop: 7,
  },
  tab: { flex: 1, alignItems: 'center', gap: 4 },
  tabIcon: {
    width: theme.size.tabIcon,
    height: theme.size.tabIcon,
    borderRadius: 5,
    backgroundColor: theme.color.muted,
    opacity: 0.85,
  },
  tabOn: { backgroundColor: theme.color.coral },
  tabFab: {
    width: theme.size.fab,
    height: theme.size.fab,
    borderRadius: 10,
    backgroundColor: theme.color.coral,
  },
  tabLabel: { fontFamily: theme.font.sans[600], fontSize: 8.5, color: theme.color.muted },
  tabLabelOn: { color: theme.color.ink },
});
