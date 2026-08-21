/**
 * PROTOTYPE — throwaway. Answers Raketa02/Raketa#49.
 *
 * Five tab bars on the real kit, switchable from the floating bar. Nothing here is
 * production code: the winner gets rewritten as a real `TabBar` component.
 *
 * The bar is not shown in a vacuum. Above it sits enough of Now to expose the two
 * collisions the ticket names:
 *
 *   1. the sport chips' own colour family — Padel IS `coral`, the same coral the
 *      selected tab uses, and they are 300pt apart on the same screen;
 *   2. the create control at 28pt against everything else at 16pt.
 *
 * And the two controls that change the answer: a width clamp (a 320pt phone is the
 * smallest supported) and the Inbox badge, which is specified and must survive.
 */

import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { theme } from '@/shared/ui/theme';

import { VARIANTS } from './variants';
import { type TabKey } from './tabs';

const WIDTHS = [
  { key: 'full', label: 'Full', value: null as number | null },
  { key: '375', label: '375', value: 375 },
  { key: '320', label: '320', value: 320 },
] as const;

const BADGES = [0, 2, 12] as const;

const SPORTS = [
  { name: 'All', dot: null as string | null },
  { name: 'Padel', dot: theme.sport.padel },
  { name: 'Tennis', dot: theme.sport.tennis },
  { name: 'Squash', dot: theme.sport.squash },
  { name: 'Badminton', dot: theme.sport.badminton },
] as const;

export function PrototypeScreen() {
  const insets = useSafeAreaInsets();
  const [index, setIndex] = useState(0);
  const [active, setActive] = useState<TabKey>('now');
  const [badge, setBadge] = useState<number>(2);
  const [width, setWidth] = useState<number | null>(null);
  const [sport, setSport] = useState('All');

  const variant = VARIANTS[index] ?? VARIANTS[0];
  const cycle = (d: number) => setIndex((i) => (i + d + VARIANTS.length) % VARIANTS.length);

  return (
    <View style={[st.root, { paddingTop: insets.top }]}>
      {/* ---- prototype chrome: obviously not the design being judged ---- */}
      <View style={st.chrome}>
        <Text style={st.chromeTitle}>
          #49 · tab-bar glyphs — {variant.key} of {VARIANTS.length}
        </Text>
        <View style={st.chromeRow}>
          <Text style={st.chromeLabel}>WIDTH</Text>
          {WIDTHS.map((w) => (
            <Pressable key={w.key} onPress={() => setWidth(w.value)} style={[st.pill, width === w.value && st.pillOn]}>
              <Text style={[st.pillText, width === w.value && st.pillTextOn]}>{w.label}</Text>
            </Pressable>
          ))}
          <Text style={[st.chromeLabel, { marginLeft: 10 }]}>BADGE</Text>
          {BADGES.map((b) => (
            <Pressable key={b} onPress={() => setBadge(b)} style={[st.pill, badge === b && st.pillOn]}>
              <Text style={[st.pillText, badge === b && st.pillTextOn]}>{b}</Text>
            </Pressable>
          ))}
        </View>

        {/* The switcher lives ABOVE the phone on purpose: a floating bar at the bottom
            would cover the one thing this prototype exists to look at. */}
        <View style={st.switcher}>
          <Pressable onPress={() => cycle(-1)} style={st.arrow} hitSlop={12}>
            <Text style={st.arrowText}>‹</Text>
          </Pressable>
          <Text style={st.switcherText}>
            {variant.key} — {variant.name}
          </Text>
          <Pressable onPress={() => cycle(1)} style={st.arrow} hitSlop={12}>
            <Text style={st.arrowText}>›</Text>
          </Pressable>
        </View>
      </View>

      {/* ---- the phone the bar lives at the bottom of ---- */}
      <View style={st.stage}>
        <View style={[st.phone, width === null ? st.phoneFull : { width }]}>
          <ScrollView contentContainerStyle={st.body} showsVerticalScrollIndicator={false}>
            <View style={st.header}>
              <Text style={st.eyebrow}>KRAKÓW · SATURDAY · 14:00</Text>
              <Text style={st.h1}>Hi, Tomek</Text>
            </View>

            {/* The colour family the tab bar has to survive being next to. */}
            <View style={st.chipRow}>
              {SPORTS.map((sp) => {
                const on = sport === sp.name;
                return (
                  <Pressable
                    key={sp.name}
                    onPress={() => setSport(sp.name)}
                    style={[st.chip, on && st.chipOn]}
                  >
                    {sp.dot ? <View style={[st.dot, { backgroundColor: sp.dot }]} /> : null}
                    <Text style={[st.chipText, on && st.chipTextOn]}>{sp.name}</Text>
                  </Pressable>
                );
              })}
            </View>

            <View style={st.stateCard}>
              <Text style={st.stateEyebrow}>YOU ARE IN</Text>
              <Text style={st.stateTime}>14:00</Text>
              <Text style={st.stateLine}>Padel · Mondo Kraków · court 3</Text>
              <Text style={st.stateLine}>3 of 4 seats · one still open</Text>
            </View>

            <View style={st.card}>
              <Text style={st.cardTitle}>Saturday 16:30 · Tennis</Text>
              <Text style={st.cardTiny}>Nowa Hala · 2 seats left · 35,00 zł</Text>
            </View>
            <View style={st.card}>
              <Text style={st.cardTitle}>Sunday 09:00 · Squash</Text>
              <Text style={st.cardTiny}>Forma · 1 seat left · 24,00 zł</Text>
            </View>

            <Text style={st.claim}>{variant.claim}</Text>
          </ScrollView>

          {variant.render({ active, badge, onSelect: setActive })}
        </View>
      </View>

    </View>
  );
}

const st = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#1A1A1A' },

  chrome: { paddingHorizontal: 12, paddingTop: 6, paddingBottom: 8 },
  chromeTitle: { color: '#8A8A8A', fontFamily: theme.font.mono[500], fontSize: 10, marginBottom: 6 },
  chromeRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  chromeLabel: { color: '#6A6A6A', fontFamily: theme.font.mono[500], fontSize: 8, letterSpacing: 1 },
  pill: { paddingHorizontal: 7, paddingVertical: 3, borderRadius: 999, backgroundColor: '#2E2E2E' },
  pillOn: { backgroundColor: '#EFEFEF' },
  pillText: { color: '#BDBDBD', fontFamily: theme.font.mono[500], fontSize: 10 },
  pillTextOn: { color: '#1A1A1A' },

  stage: { flex: 1, alignItems: 'center' },
  phone: { flex: 1, backgroundColor: theme.color.paper, overflow: 'hidden' },
  phoneFull: { width: '100%' },

  body: { paddingBottom: 24 },
  header: { paddingHorizontal: theme.space.lg, paddingTop: 12, paddingBottom: 9 },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted },
  h1: { ...theme.type.h1, color: theme.color.ink, marginTop: 2 },

  chipRow: { flexDirection: 'row', gap: 4, paddingHorizontal: theme.space.lg, paddingBottom: 9 },
  chip: {
    height: 25,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
  },
  chipOn: { backgroundColor: theme.color.ink, borderColor: theme.color.ink },
  dot: { width: 5, height: 5, borderRadius: 2 },
  chipText: { fontFamily: theme.font.sans[600], fontSize: 10, color: theme.color.ink },
  chipTextOn: { color: '#FFFFFF' },

  stateCard: {
    marginHorizontal: theme.space.lg,
    padding: 13,
    borderRadius: theme.radius.cardDark,
    backgroundColor: theme.color.night,
  },
  stateEyebrow: { ...theme.type.eyebrow, color: theme.color.onDarkEyebrow },
  stateTime: { ...theme.num.levelHero, fontSize: 30, lineHeight: 32, color: '#FFFFFF', marginVertical: 2 },
  stateLine: { ...theme.type.tiny, color: theme.color.onDarkTiny },

  card: {
    marginHorizontal: theme.space.lg,
    marginTop: theme.space.sm,
    padding: 11,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
  },
  cardTitle: { ...theme.type.cardTitle, color: theme.color.ink },
  cardTiny: { ...theme.type.tiny, color: theme.color.muted },

  claim: {
    ...theme.type.tiny,
    color: theme.color.muted,
    paddingHorizontal: theme.space.lg,
    paddingTop: theme.space.md,
    fontStyle: 'italic',
  },

  switcher: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 8,
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: '#111111',
    borderWidth: 1,
    borderColor: '#3A3A3A',
  },
  arrow: { width: 22, alignItems: 'center' },
  arrowText: { color: '#FFFFFF', fontSize: 18, lineHeight: 20 },
  switcherText: { color: '#FFFFFF', fontFamily: theme.font.sans[600], fontSize: 11 },
});
