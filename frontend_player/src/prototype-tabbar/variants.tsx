/**
 * PROTOTYPE — throwaway. See `tabs.ts`.
 *
 * Five tab bars, one question: what are the five glyphs, and does one family cover
 * Now · Find · Create · Inbox · You without a metaphor anyone has to be taught?
 *
 * `@expo/vector-icons` ships inside the `expo` package, so none of this adds a
 * dependency — which is itself part of the answer ADR-0012 left open.
 */

import { Feather, Ionicons, MaterialIcons } from '@expo/vector-icons';
import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui/theme';

import { TabBarShell, type GlyphProps } from './TabBarShell';
import { type TabKey } from './tabs';

export type VariantProps = { active: TabKey; badge: number; onSelect: (t: TabKey) => void };

export type Variant = {
  key: string;
  name: string;
  /** What this one is arguing. Shown in the switcher so a verdict has something to attach to. */
  claim: string;
  render: (p: VariantProps) => React.ReactNode;
};

/** §B13: the create control is 28pt, radius 10, solid coral, opacity 1, margin-bottom -4. */
const FAB = theme.size.fab;

// ---------------------------------------------------------------------------
// A — the placeholder squares that ship today. The control.
// ---------------------------------------------------------------------------

function SquareGlyph({ color }: GlyphProps) {
  return <View style={[s.square, { backgroundColor: color }]} />;
}

// ---------------------------------------------------------------------------
// B — no glyphs at all. A square that shipped this long is weak evidence anyone
//     missed them. Labels carry the whole bar, so they grow from 8.5 to 11.
// ---------------------------------------------------------------------------

function NoGlyph() {
  return null;
}

// ---------------------------------------------------------------------------
// C — Feather. One weight, geometric, closest to the UI spec's recommended
//     "24px canvas, 1.75px stroke" — though Feather is 2/24, so it renders
//     slightly heavier than the recommendation at the same box.
// ---------------------------------------------------------------------------

const FEATHER: Record<Exclude<TabKey, 'create'>, keyof typeof Feather.glyphMap> = {
  now: 'home',
  find: 'search',
  msg: 'inbox',
  you: 'user',
};

function FeatherGlyph({ tabKey, color }: GlyphProps) {
  if (tabKey === 'create') return null;
  return <Feather name={FEATHER[tabKey]} size={theme.size.tabIcon} color={color} />;
}

// ---------------------------------------------------------------------------
// D — Ionicons, outline when resting and FILLED when selected. The only variant
//     where the selected state is carried by the glyph and not by colour alone.
// ---------------------------------------------------------------------------

const IONIC: Record<Exclude<TabKey, 'create'>, { off: keyof typeof Ionicons.glyphMap; on: keyof typeof Ionicons.glyphMap }> = {
  now: { off: 'home-outline', on: 'home' },
  find: { off: 'search-outline', on: 'search' },
  msg: { off: 'mail-outline', on: 'mail' },
  you: { off: 'person-outline', on: 'person' },
};

function IonicGlyph({ tabKey, active, color }: GlyphProps) {
  if (tabKey === 'create') return null;
  const pair = IONIC[tabKey];
  return <Ionicons name={active ? pair.on : pair.off} size={theme.size.tabIcon} color={color} />;
}

// ---------------------------------------------------------------------------
// E — MaterialIcons, solid throughout. Mass instead of line. The honest test of
//     whether a hairline outline survives a 16pt box at all.
// ---------------------------------------------------------------------------

const MATERIAL: Record<Exclude<TabKey, 'create'>, keyof typeof MaterialIcons.glyphMap> = {
  now: 'home',
  find: 'search',
  msg: 'mail',
  you: 'person',
};

function MaterialGlyph({ tabKey, color }: GlyphProps) {
  if (tabKey === 'create') return null;
  return <MaterialIcons name={MATERIAL[tabKey]} size={theme.size.tabIcon} color={color} />;
}

// ---------------------------------------------------------------------------
// The four create treatments
// ---------------------------------------------------------------------------

/** A: the coral rounded square that ships. */
function CreateSquare() {
  return <View style={s.fabSquare} />;
}

/** B: no glyph anywhere, so create says what it is. `ink` on coral is 4.50 — Rule C
 *  forbids the white that a coral pill wants. */
function CreateWord() {
  return (
    <View style={s.fabPill}>
      <Text style={s.fabPillText}>Create</Text>
    </View>
  );
}

/** C / E: a coral filled circle with the family's own plus knocked out. Flat in the bar. */
function CreateCircle({ glyph }: { glyph: 'feather' | 'material' }) {
  return (
    <View style={s.fabCircle}>
      {glyph === 'feather' ? (
        <Feather name="plus" size={16} color={theme.color.surface} />
      ) : (
        <MaterialIcons name="add" size={18} color={theme.color.surface} />
      )}
    </View>
  );
}

/** D: the same circle, RAISED — §B13's `margin-bottom:-4px` taken seriously enough to
 *  see whether the odd-one-out reads as a mistake or as the point. */
function CreateRaised() {
  return (
    <View style={[s.fabCircle, { marginBottom: -4, marginTop: -6 }]}>
      <Ionicons name="add" size={18} color={theme.color.surface} />
    </View>
  );
}

// ---------------------------------------------------------------------------

export const VARIANTS: readonly [Variant, ...Variant[]] = [
  {
    key: 'A',
    name: 'Placeholder squares',
    claim: 'The control — exactly what ships today. Judge every other variant against this.',
    render: (p) => <TabBarShell {...p} renderGlyph={SquareGlyph} renderCreate={CreateSquare} />,
  },
  {
    key: 'B',
    name: 'Labels only, no glyphs',
    claim: 'Five words at 11pt. If nothing is lost, the answer is "no icon family at all".',
    render: (p) => (
      <TabBarShell {...p} renderGlyph={NoGlyph} renderCreate={CreateWord} labelSize={11} />
    ),
  },
  {
    key: 'C',
    name: 'Feather — hairline outline',
    claim: "The UI spec's recommended default: one outline family, one weight, no fills.",
    render: (p) => (
      <TabBarShell {...p} renderGlyph={FeatherGlyph} renderCreate={() => <CreateCircle glyph="feather" />} />
    ),
  },
  {
    key: 'D',
    name: 'Ionicons — outline, filled when selected',
    claim: 'Selection is a shape change, not only coral. Create is raised out of the bar.',
    render: (p) => (
      <TabBarShell {...p} renderGlyph={IonicGlyph} renderCreate={CreateRaised} />
    ),
  },
  {
    key: 'E',
    name: 'MaterialIcons — solid',
    claim: 'Mass instead of line. Does a 16pt box want a filled shape rather than a stroke?',
    render: (p) => (
      <TabBarShell {...p} renderGlyph={MaterialGlyph} renderCreate={() => <CreateCircle glyph="material" />} />
    ),
  },
];

const s = StyleSheet.create({
  square: {
    width: theme.size.tabIcon,
    height: theme.size.tabIcon,
    borderRadius: 5,
    opacity: 0.85,
  },
  fabSquare: {
    width: FAB,
    height: FAB,
    borderRadius: 10,
    backgroundColor: theme.color.coral,
    marginBottom: -4,
  },
  fabCircle: {
    width: FAB,
    height: FAB,
    borderRadius: FAB / 2,
    backgroundColor: theme.color.coral,
    alignItems: 'center',
    justifyContent: 'center',
  },
  fabPill: {
    height: FAB,
    paddingHorizontal: 12,
    borderRadius: FAB / 2,
    backgroundColor: theme.color.coral,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: -4,
  },
  fabPillText: { fontFamily: theme.font.sans[700], fontSize: 11, color: theme.color.ink },
});
