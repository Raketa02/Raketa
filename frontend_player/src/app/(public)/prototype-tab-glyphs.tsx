/**
 * ⚠️ THROWAWAY PROTOTYPE — not production. Lives on `prototype/play-tab-glyphs` and is
 * deleted from `main`. Written for
 * [#238 Five glyphs, and the set they come from](https://github.com/Raketa02/Raketa/issues/238).
 *
 * THE QUESTION
 *   Which icon set does the tab bar draw from, which glyph is each of the five tabs, what
 *   happens to the ⚡, and does the glyph change between rest and active?
 *
 *   `design-system.md` §10.2 ships `currentColor` squares and says picking the set is a
 *   separate recorded decision. [#227](https://github.com/Raketa02/Raketa/issues/227) built
 *   the bar, so the squares are now an honest placeholder sitting in the app's real bottom
 *   chrome, which is not the same thing.
 *
 * WHAT IS ALREADY DECIDED AND IS THEREFORE FIXED HERE — not switchable, so the glyphs are
 * judged against the bar that ships and not against a bar nobody chose:
 *   · §10.2 geometry — equal columns, paddingTop 6, paddingBottom 12 + bottom inset, 16pt box
 *   · `tag` labels, 9.5/700 flat, `maxFontSizeMultiplier` (#227, #219's 9.5 floor)
 *   · flank tone — `ink` selected, `muted` resting (3.25:1, a LIGHTNESS difference)
 *   · the centre — a 30pt disc, radius 11, §6.1 `primary` (`coralInk` fill, white mark),
 *     `shadow.fab`, and a 2pt `coral` ring 2pt clear when Play is active (#227)
 *
 * WHAT VARIES — four axes, all switched from the bar pinned at the TOP (the subject is at
 * the bottom, so the switcher may not sit on it).
 *
 *   1. FAMILY   feather · ionicons · matcomm · squares(control)
 *      One family or none. Mixing families is how a bar stops reading as one object, so
 *      the unit of judgement is a whole bar, never a glyph.
 *
 *   2. SLATE    1 · 2 · 3 — three COMPLETE slates per family for the four labelled tabs.
 *      The five acts moved since the last time this was asked: `Around` is proximity and
 *      not a search box, `Chats` is a conversation and not an inbox. Only `you` is
 *      uncontested. Each slate is a different reading of Now and Around together.
 *
 *   3. MARK     emoji · text · set · svg — the ⚡, the one mark not in a 16pt box.
 *      `emoji` is what `research/tab-shell` ships: a bare U+26A1. That codepoint has
 *      Emoji_Presentation=Yes, so with no U+FE0E it renders as the COLOUR emoji and the
 *      `color: surface` style is ignored — a yellow mark on the coralInk disc, which
 *      defeats §6.1 `primary`'s white mark and #227's whole disc argument. Look at
 *      `emoji` and `text` side by side on a real device: that is the finding, not an
 *      argument about it.
 *
 *   4. ACTIVE   tone · shape — does the glyph itself change when the tab is selected, or
 *      is selection carried by tone alone? `shape` needs outline/filled pairs, which
 *      Feather does not have (it is a font with one weight and no fill), so on Feather
 *      the two are identical and that is the point.
 *
 * WHAT IS REAL  — real safe-area insets, real `theme.ts`, real `@expo/vector-icons`
 *   (14.0.4, already in `pnpm-lock.yaml` via `expo`), real `react-native-svg`, and the
 *   back stack wired exactly as #227 decided it.
 *
 * WHAT IS FAKE  — every screen body is one line. No data, no network, nothing survives a
 *   reload.
 */

import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';

import { theme } from '@/shared/ui';

// ---------------------------------------------------------------------------
// The model — #227's, unchanged
// ---------------------------------------------------------------------------

type ScreenId = 'now' | 'around' | 'chats' | 'you' | 'find' | 'deck' | 'builder' | 'pool';
type TabId = 'now' | 'around' | 'play' | 'chats' | 'you';
type FlankId = Exclude<TabId, 'play'>;

const PLAY_SCREENS: ScreenId[] = ['find', 'deck', 'builder', 'pool'];

const TABS: { id: TabId; label: string }[] = [
  { id: 'now', label: 'Now' },
  { id: 'around', label: 'Around' },
  { id: 'play', label: 'Play' },
  { id: 'chats', label: 'Chats' },
  { id: 'you', label: 'You' },
];

const tabOf = (s: ScreenId): TabId => (PLAY_SCREENS.includes(s) ? 'play' : (s as TabId));

// ---------------------------------------------------------------------------
// Axis 1 + 2 — the families and their slates
//
// A slate is FOUR glyphs judged together, because the question "is `home` right for a tab
// called Now" is not answerable next to a square — it is answerable next to whatever is
// drawn in the Around column. Each family gets three, and the three disagree about the
// same two things: whether Now is a place or a time, and whether Around is a point, a
// direction or a sweep.
// ---------------------------------------------------------------------------

// Each family's slates are typed against that family's OWN glyphMap, so a name that does
// not exist in `@expo/vector-icons` 14.0.4 is a compile error rather than a blank column
// nobody notices at 16pt. `pnpm typecheck` is the check on this whole file.
type FeatherName = keyof typeof Feather.glyphMap;
type IoniconsName = keyof typeof Ionicons.glyphMap;
type MatCommName = keyof typeof MaterialCommunityIcons.glyphMap;

type Pair<N> = { off: N; on: N };
type Slate<N> = { name: string; claim: string; glyphs: Record<FlankId, Pair<N>> };

const one = <N,>(n: N): Pair<N> => ({ off: n, on: n });

/** Feather — one weight, geometric, 2/24 stroke. No filled counterparts anywhere, so
 *  axis 4 has no `shape` to offer and every slate is `off === on`. */
const FEATHER: Slate<FeatherName>[] = [
  {
    name: 'the place read',
    claim: 'Now is where you start · Around is a point on a map',
    glyphs: {
      now: one('home'),
      around: one('map-pin'),
      chats: one('message-circle'),
      you: one('user'),
    },
  },
  {
    name: 'the time read',
    claim: 'Now is today and next · Around is a direction you face',
    glyphs: {
      now: one('calendar'),
      around: one('compass'),
      chats: one('message-square'),
      you: one('user'),
    },
  },
  {
    name: 'the moment read',
    claim: 'Now is the clock · Around is a sweep of what is near',
    glyphs: {
      now: one('clock'),
      around: one('globe'),
      chats: one('message-circle'),
      you: one('user'),
    },
  },
];

/** Ionicons — outline/filled pairs throughout, rounder, the iOS-native idiom. The only
 *  family of the three that can carry selection without colour. */
const IONICONS: Slate<IoniconsName>[] = [
  {
    name: 'the place read',
    claim: 'Now is where you start · Around is a pin',
    glyphs: {
      now: { off: 'home-outline', on: 'home' },
      around: { off: 'location-outline', on: 'location' },
      chats: { off: 'chatbubble-outline', on: 'chatbubble' },
      you: { off: 'person-outline', on: 'person' },
    },
  },
  {
    name: 'the time read',
    claim: 'Now is today · Around is a direction · Chats is plural',
    glyphs: {
      now: { off: 'today-outline', on: 'today' },
      around: { off: 'compass-outline', on: 'compass' },
      chats: { off: 'chatbubbles-outline', on: 'chatbubbles' },
      you: { off: 'person-outline', on: 'person' },
    },
  },
  {
    name: 'the moment read',
    claim: 'Now is the clock · Around is a heading you are pointed along',
    glyphs: {
      now: { off: 'time-outline', on: 'time' },
      around: { off: 'navigate-outline', on: 'navigate' },
      chats: { off: 'chatbox-outline', on: 'chatbox' },
      you: { off: 'person-circle-outline', on: 'person-circle' },
    },
  },
];

/** MaterialCommunityIcons — the widest vocabulary of the three, which is the only reason
 *  it is here: `radar` and `lightning-bolt` exist nowhere else, and Around is the tab with
 *  no obvious glyph in any family. */
const MATCOMM: Slate<MatCommName>[] = [
  {
    name: 'the place read',
    claim: 'Now is where you start · Around is a marker',
    glyphs: {
      now: { off: 'home-outline', on: 'home' },
      around: { off: 'map-marker-outline', on: 'map-marker' },
      chats: { off: 'message-outline', on: 'message' },
      you: { off: 'account-outline', on: 'account' },
    },
  },
  {
    name: 'the time read',
    claim: 'Now is today and next · Around is a radar sweep · Chats is a forum',
    glyphs: {
      now: { off: 'calendar-blank-outline', on: 'calendar-blank' },
      around: one('radar'),
      chats: { off: 'forum-outline', on: 'forum' },
      you: { off: 'account-circle-outline', on: 'account-circle' },
    },
  },
  {
    name: 'the moment read',
    claim: 'Now is the clock · Around is a compass',
    glyphs: {
      now: { off: 'clock-outline', on: 'clock' },
      around: { off: 'compass-outline', on: 'compass' },
      chats: { off: 'chat-outline', on: 'chat' },
      you: { off: 'account-outline', on: 'account' },
    },
  },
];

type FamilyId = 'feather' | 'ionicons' | 'matcomm' | 'squares';

/** Slate metadata only. The glyph arrays stay apart because each is typed against its own
 *  family's `glyphMap` — merging them into one registry is exactly what would erase the
 *  compile-time check on all 24 names. */
type FamilyMeta = {
  id: FamilyId;
  name: string;
  /** What this one is arguing. Shown in the switcher so a verdict has something to attach to. */
  claim: string;
  slates: { name: string; claim: string }[];
  /** The family's own bolt, for MARK = `set`. */
  bolt: string | null;
  hasFilled: boolean;
};

const meta = <N,>(slates: Slate<N>[]) => slates.map((s) => ({ name: s.name, claim: s.claim }));

const FAMILIES: FamilyMeta[] = [
  {
    id: 'feather',
    name: 'Feather',
    claim: 'one weight, no fill — selection can only ever be tone',
    slates: meta(FEATHER),
    bolt: 'zap',
    hasFilled: false,
  },
  {
    id: 'ionicons',
    name: 'Ionicons',
    claim: 'outline/filled pairs — the only family that can carry selection without colour',
    slates: meta(IONICONS),
    bolt: 'flash',
    hasFilled: true,
  },
  {
    id: 'matcomm',
    name: 'MaterialCommunity',
    claim: 'widest vocabulary — `radar` and `lightning-bolt` exist in no other family',
    slates: meta(MATCOMM),
    bolt: 'lightning-bolt',
    hasFilled: true,
  },
  {
    id: 'squares',
    name: 'squares (control)',
    claim: '§10.2 as it ships today — the honest placeholder, in the real bar',
    slates: [{ name: '—', claim: 'no glyph is specified' }],
    bolt: null,
    hasFilled: false,
  },
];

/** `noUncheckedIndexedAccess` is on, and every lookup here is over a closed literal union
 *  with an entry for each member — so the fallback is unreachable rather than defensive. */
const familyMeta = (id: FamilyId): FamilyMeta => FAMILIES.find((f) => f.id === id) ?? FAMILIES[0]!;

// ---------------------------------------------------------------------------
// Axis 3 — the ⚡
// ---------------------------------------------------------------------------

type MarkId = 'emoji' | 'text' | 'set' | 'svg';

const MARKS: { id: MarkId; note: string }[] = [
  { id: 'emoji', note: 'bare U+26A1 — what ships on research/tab-shell. Is it white?' },
  { id: 'text', note: 'U+26A1 + U+FE0E — text presentation requested' },
  { id: 'set', note: "the family's own bolt, in the 16pt box's weight" },
  { id: 'svg', note: 'a drawn bolt — react-native-svg, a direct dependency' },
];

/** MARK = `svg`. One solid bolt on a 24 canvas, so it is white by fill rather than by a
 *  `color` the renderer may ignore. Deliberately not an outline: at 15pt inside a 30pt
 *  disc a hairline outline is a smudge, which is itself worth seeing. */
function DrawnBolt({ size, color }: { size: number; color: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Path d="M13.5 2 L5 13.2 h5.2 L9.4 22 L19 10.4 h-5.4 z" fill={color} />
    </Svg>
  );
}

// ---------------------------------------------------------------------------
// Axis 4 — what selection changes
// ---------------------------------------------------------------------------

type ActiveMode = 'tone' | 'shape';

// ---------------------------------------------------------------------------
// The shell
// ---------------------------------------------------------------------------

export default function PrototypeTabGlyphs() {
  const insets = useSafeAreaInsets();

  const [family, setFamily] = useState<FamilyId>('feather');
  const [slate, setSlate] = useState(0);
  const [mark, setMark] = useState<MarkId>('emoji');
  const [activeMode, setActiveMode] = useState<ActiveMode>('tone');

  // #227's back stack, verbatim — the bar is judged by walking it, not by looking at it.
  const [stack, setStack] = useState<ScreenId[]>(['now']);
  const [sent, setSent] = useState(false);
  const current = stack[stack.length - 1] as ScreenId;

  const push = (s: ScreenId) => setStack((k) => [...k, s]);
  const back = () => setStack((k) => (k.length > 1 ? k.slice(0, -1) : k));

  const openPlay = () => {
    setSent(false);
    setStack(['now', 'find']);
  };

  const goTab = (t: TabId) => {
    setSent(false);
    if (t === 'play') return openPlay();
    setStack([t]);
  };

  const send = () => {
    setSent(true);
    setStack(['now']);
  };

  const fam = familyMeta(family);
  const slateIndex = Math.min(slate, fam.slates.length - 1);

  return (
    <View style={styles.root}>
      <Switcher
        top={insets.top}
        family={family}
        slate={slateIndex}
        mark={mark}
        activeMode={activeMode}
        stack={stack}
        onFamily={(f) => {
          setFamily(f);
          setSlate(0);
        }}
        onSlate={setSlate}
        onMark={setMark}
        onActiveMode={setActiveMode}
      />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[styles.scrollBody, { paddingTop: insets.top + 108 }]}
      >
        <Screen
          id={current}
          sent={sent}
          canGoBack={stack.length > 1}
          onBack={back}
          onPush={push}
          onResetToFind={openPlay}
          onSend={send}
          onPopTo={(s) => setStack((k) => k.slice(0, k.indexOf(s) + 1))}
        />
      </ScrollView>

      {current === 'builder' ? (
        <View style={styles.cta}>
          <Pressable style={styles.ctaBtn} onPress={send}>
            <Text style={styles.ctaLabel}>Send the challenge</Text>
          </Pressable>
        </View>
      ) : null}

      <TabBar
        family={family}
        slate={slateIndex}
        mark={mark}
        activeMode={activeMode}
        active={tabOf(current)}
        bottomInset={insets.bottom}
        onPress={goTab}
      />
    </View>
  );
}

// ---------------------------------------------------------------------------
// The bar — the thing being judged. §10.2 whole; only the glyph varies.
// ---------------------------------------------------------------------------

function TabBar({
  family,
  slate,
  mark,
  activeMode,
  active,
  bottomInset,
  onPress,
}: {
  family: FamilyId;
  slate: number;
  mark: MarkId;
  activeMode: ActiveMode;
  active: TabId;
  bottomInset: number;
  onPress: (t: TabId) => void;
}) {
  return (
    <View style={[styles.bar, { paddingBottom: theme.space.md + bottomInset }]}>
      {TABS.map((t) =>
        t.id === 'play' ? (
          <PlayTab
            key={t.id}
            family={family}
            mark={mark}
            selected={active === 'play'}
            onPress={() => onPress('play')}
          />
        ) : (
          <FlankTab
            key={t.id}
            id={t.id}
            label={t.label}
            family={family}
            slate={slate}
            activeMode={activeMode}
            selected={active === t.id}
            onPress={() => onPress(t.id)}
          />
        ),
      )}
    </View>
  );
}

function FlankTab({
  id,
  label,
  family,
  slate,
  activeMode,
  selected,
  onPress,
}: {
  id: FlankId;
  label: string;
  family: FamilyId;
  slate: number;
  activeMode: ActiveMode;
  selected: boolean;
  onPress: () => void;
}) {
  // #227 — `ink` selected, `muted` resting. 3.25:1, and it is a LIGHTNESS difference, so
  // unlike the coral/muted pair the last record accepted it survives greyscale.
  const tone = selected ? theme.color.ink : theme.color.muted;

  return (
    <Pressable
      style={styles.column}
      onPress={onPress}
      accessibilityRole="tab"
      accessibilityLabel={label}
      accessibilityState={{ selected }}
    >
      <View style={styles.iconBox}>
        <Glyph
          id={id}
          family={family}
          slate={slate}
          filled={activeMode === 'shape' && selected}
          color={tone}
        />
      </View>
      <Label text={label} color={tone} />
    </Pressable>
  );
}

function Glyph({
  id,
  family,
  slate,
  filled,
  color,
}: {
  id: FlankId;
  family: FamilyId;
  slate: number;
  filled: boolean;
  color: string;
}) {
  const size = theme.size.tabIcon;

  if (family === 'squares') {
    // §10.2's honest placeholder: it specifies the box and the position, not the glyph.
    return <View style={[styles.square, { backgroundColor: color }]} />;
  }

  const pick = <N,>(slates: Slate<N>[]): N => {
    const pair = (slates[slate] ?? slates[0]!).glyphs[id];
    return filled ? pair.on : pair.off;
  };

  if (family === 'feather') {
    return <Feather name={pick(FEATHER)} size={size} color={color} />;
  }
  if (family === 'ionicons') {
    return <Ionicons name={pick(IONICONS)} size={size} color={color} />;
  }
  return <MaterialCommunityIcons name={pick(MATCOMM)} size={size} color={color} />;
}

function PlayTab({
  family,
  mark,
  selected,
  onPress,
}: {
  family: FamilyId;
  mark: MarkId;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      style={styles.column}
      onPress={onPress}
      accessibilityRole="tab"
      accessibilityLabel="Play"
      accessibilityState={{ selected }}
    >
      <View style={styles.discBox}>
        {/* #227 — the ring is ABSOLUTE, so entering Play never changes the bar's height. */}
        {selected ? <View style={styles.ring} /> : null}
        <View style={[styles.disc, styles.discRaised]}>
          {/* §E6 — the mark is hidden from the reader; the visible "Play" label says it. */}
          <View accessibilityElementsHidden importantForAccessibility="no">
            <Mark family={family} mark={mark} />
          </View>
        </View>
      </View>
      <Label text="Play" color={theme.color.ink} />
    </Pressable>
  );
}

function Mark({ family, mark }: { family: FamilyId; mark: MarkId }) {
  const white = theme.color.surface;

  if (mark === 'emoji') {
    return <Text style={styles.bolt}>{'⚡'}</Text>;
  }
  if (mark === 'text') {
    return <Text style={styles.bolt}>{'⚡︎'}</Text>;
  }
  if (mark === 'svg') {
    return <DrawnBolt size={15} color={white} />;
  }

  const fam = familyMeta(family);
  if (!fam.bolt) {
    // The control has no bolt to offer, so it falls back to its own idiom: a square.
    return <View style={[styles.square, { backgroundColor: white }]} />;
  }
  if (family === 'feather') {
    return <Feather name={fam.bolt as never} size={15} color={white} />;
  }
  if (family === 'ionicons') {
    return <Ionicons name={fam.bolt as never} size={15} color={white} />;
  }
  return <MaterialCommunityIcons name={fam.bolt as never} size={15} color={white} />;
}

function Label({ text, color }: { text: string; color: string }) {
  return (
    <Text
      numberOfLines={1}
      style={[theme.type.tag, styles.label, { color }]}
      // #227 — Part 13 names the bar as the fixed-height exception AND forbids
      // `allowFontScaling={false}` outside the level bar. Scale, but bounded.
      maxFontSizeMultiplier={1.6}
    >
      {text}
    </Text>
  );
}

// ---------------------------------------------------------------------------
// The screens — #227's, one line each
// ---------------------------------------------------------------------------

const ONE_LINER: Record<ScreenId, { title: string; line: string }> = {
  now: { title: 'Now', line: 'What is happening today and next. Not built yet.' },
  around: { title: 'Around', line: 'Players and courts near you. Not built yet.' },
  chats: { title: 'Chats', line: 'A chat opens when somebody accepts. Not built yet.' },
  you: { title: 'You', line: 'Your profile, your radius, your week. Not built yet.' },
  find: { title: 'Find me a game', line: 'Sport · what kind of game · when could you play.' },
  deck: { title: 'Match me', line: 'One player at a time. Yes or pass.' },
  builder: { title: 'Build the four', line: '3 seats open · tap one, or let the engine fill.' },
  pool: { title: 'The pool', line: 'Everybody you could play, ranked.' },
};

function Screen({
  id,
  sent,
  canGoBack,
  onBack,
  onPush,
  onResetToFind,
  onSend,
  onPopTo,
}: {
  id: ScreenId;
  sent: boolean;
  canGoBack: boolean;
  onBack: () => void;
  onPush: (s: ScreenId) => void;
  onResetToFind: () => void;
  onSend: () => void;
  onPopTo: (s: ScreenId) => void;
}) {
  const meta = ONE_LINER[id];
  const inPlay = PLAY_SCREENS.includes(id);

  return (
    <View>
      <View style={styles.header}>
        {canGoBack ? (
          <Pressable onPress={onBack} hitSlop={theme.hit.infoMark} accessibilityLabel="Back">
            <Text style={styles.chev}>‹</Text>
          </Pressable>
        ) : null}
        <View style={styles.headerText}>
          {inPlay ? <Text style={styles.eyebrow}>THE MATCHMAKING ENGINE</Text> : null}
          <Text style={styles.h1}>{meta.title}</Text>
        </View>
      </View>

      {sent && id === 'now' ? (
        <View style={styles.note}>
          <Text style={styles.noteText}>
            Challenge sent — the Play stack is discarded, so the bar drops back to Now. Watch what
            the glyph does on the way.
          </Text>
        </View>
      ) : null}

      <Text style={styles.body}>{meta.line}</Text>

      {id === 'find' || id === 'deck' ? (
        <Segment active={id} onFind={onResetToFind} onDeck={() => onPush('deck')} />
      ) : null}

      {id === 'find' ? <Action label="Build the four →" onPress={() => onPush('builder')} /> : null}

      {id === 'builder' ? (
        <>
          <Action label="Pick players myself →" onPress={() => onPush('pool')} />
          <Action label="Let the engine fill the seats" onPress={() => undefined} />
        </>
      ) : null}

      {id === 'pool' ? (
        <Action label="Court — back to the builder (E-8)" onPress={() => onPopTo('builder')} />
      ) : null}

      {id === 'deck' ? <Action label="Say yes (mutual → sent)" onPress={onSend} /> : null}

      <Text style={styles.foot}>
        {inPlay
          ? 'Play is the active tab on all four of these — AC-7. The ring is the only thing that says so.'
          : 'Not a Play screen. The disc is at rest and the glyph column carries the state.'}
      </Text>
    </View>
  );
}

function Segment({
  active,
  onFind,
  onDeck,
}: {
  active: ScreenId;
  onFind: () => void;
  onDeck: () => void;
}) {
  return (
    <View style={styles.seg}>
      <Pressable style={[styles.segItem, active === 'find' ? styles.segOn : null]} onPress={onFind}>
        <Text style={styles.segLabel}>Find a game</Text>
      </Pressable>
      <Pressable style={[styles.segItem, active === 'deck' ? styles.segOn : null]} onPress={onDeck}>
        <Text style={styles.segLabel}>Match me · 3</Text>
      </Pressable>
    </View>
  );
}

function Action({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable style={styles.action} onPress={onPress}>
      <Text style={styles.actionLabel}>{label}</Text>
    </Pressable>
  );
}

// ---------------------------------------------------------------------------
// The switcher — deliberately ugly, deliberately at the top
// ---------------------------------------------------------------------------

function Switcher({
  top,
  family,
  slate,
  mark,
  activeMode,
  stack,
  onFamily,
  onSlate,
  onMark,
  onActiveMode,
}: {
  top: number;
  family: FamilyId;
  slate: number;
  mark: MarkId;
  activeMode: ActiveMode;
  stack: ScreenId[];
  onFamily: (f: FamilyId) => void;
  onSlate: (i: number) => void;
  onMark: (m: MarkId) => void;
  onActiveMode: (a: ActiveMode) => void;
}) {
  const fam = familyMeta(family);
  const current = fam.slates[slate];

  return (
    <View style={[styles.switcher, { paddingTop: top + 6 }]}>
      <View style={styles.switchRow}>
        {FAMILIES.map((f) => (
          <Pressable
            key={f.id}
            style={[styles.pill, family === f.id ? styles.pillOn : null]}
            onPress={() => onFamily(f.id)}
          >
            <Text style={[styles.pillText, family === f.id ? styles.pillTextOn : null]}>
              {f.id === 'squares' ? '□' : f.name.slice(0, 4)}
            </Text>
          </Pressable>
        ))}
        <Text style={styles.switchText}>{fam.claim}</Text>
      </View>

      <View style={styles.switchRow}>
        {fam.slates.map((s, i) => (
          <Pressable
            key={s.name}
            style={[styles.pill, slate === i ? styles.pillOn : null]}
            onPress={() => onSlate(i)}
          >
            <Text style={[styles.pillText, slate === i ? styles.pillTextOn : null]}>{i + 1}</Text>
          </Pressable>
        ))}
        <Text style={styles.switchText}>{current?.claim ?? ''}</Text>
      </View>

      <View style={styles.switchRow}>
        {MARKS.map((m) => (
          <Pressable
            key={m.id}
            style={[styles.pill, mark === m.id ? styles.pillOn : null]}
            onPress={() => onMark(m.id)}
          >
            <Text style={[styles.pillText, mark === m.id ? styles.pillTextOn : null]}>{m.id}</Text>
          </Pressable>
        ))}
        <Text style={styles.switchText}>{MARKS.find((m) => m.id === mark)?.note ?? ''}</Text>
      </View>

      <View style={styles.switchRow}>
        {(['tone', 'shape'] as ActiveMode[]).map((a) => (
          <Pressable
            key={a}
            style={[styles.pill, activeMode === a ? styles.pillOn : null]}
            onPress={() => onActiveMode(a)}
          >
            <Text style={[styles.pillText, activeMode === a ? styles.pillTextOn : null]}>{a}</Text>
          </Pressable>
        ))}
        <Text style={styles.switchText}>
          {activeMode === 'shape' && !fam.hasFilled
            ? 'no filled counterparts — identical to tone, and that IS the finding'
            : stack.join(' › ')}
        </Text>
      </View>
    </View>
  );
}

// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: theme.color.paper },
  scroll: { flex: 1 },
  scrollBody: { paddingHorizontal: theme.space.lg, paddingBottom: theme.space.lg },

  header: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: theme.space.sm,
    marginBottom: theme.space.md,
  },
  headerText: { flex: 1 },
  chev: { fontSize: 20, color: theme.color.muted, lineHeight: 24 },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, marginBottom: 2 },
  h1: { ...theme.type.h1, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.muted, marginBottom: theme.space.md },
  foot: { ...theme.type.tiny, color: theme.color.muted, marginTop: theme.space.xl },

  note: {
    backgroundColor: theme.color.mintSoft,
    borderLeftWidth: 3,
    borderLeftColor: theme.color.mintInk,
    borderRadius: theme.radius.note,
    padding: theme.space.md,
    marginBottom: theme.space.md,
  },
  noteText: { ...theme.type.tiny, color: theme.color.ink },

  seg: {
    flexDirection: 'row',
    backgroundColor: theme.color.line2,
    borderRadius: theme.radius.seg,
    padding: theme.space.xxs,
    gap: theme.space.xxs,
    marginBottom: theme.space.md,
  },
  segItem: {
    flex: 1,
    height: 28,
    borderRadius: theme.radius.segThumb,
    alignItems: 'center',
    justifyContent: 'center',
  },
  segOn: { backgroundColor: theme.color.surface },
  segLabel: { ...theme.type.chip, color: theme.color.ink },

  action: {
    height: theme.size.btnLg,
    borderRadius: theme.radius.btn,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.space.sm,
  },
  actionLabel: { ...theme.type.btn, color: theme.color.ink },

  cta: {
    paddingHorizontal: theme.space.lg,
    paddingTop: theme.space.sm,
    paddingBottom: theme.space.sm,
    borderTopWidth: 1,
    borderTopColor: theme.color.line,
    backgroundColor: theme.color.paper,
  },
  ctaBtn: {
    height: theme.size.btnLg,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.coralInk,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ctaLabel: { ...theme.type.btn, color: theme.color.surface },

  // §10.2 — equal columns, paddingTop 6, paddingBottom 12 + bottom inset, 16pt box.
  bar: {
    flexDirection: 'row',
    backgroundColor: theme.color.surface,
    borderTopWidth: 1,
    borderTopColor: theme.color.line,
    paddingTop: theme.space.xs,
  },
  column: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', gap: 4 },
  iconBox: {
    width: theme.size.tabIcon,
    height: theme.size.tabIcon,
    alignItems: 'center',
    justifyContent: 'center',
  },
  square: { width: theme.size.tabIcon, height: theme.size.tabIcon, borderRadius: 5 },
  label: { textAlign: 'center' },

  discBox: { width: 30, height: 30, alignItems: 'center', justifyContent: 'center' },
  ring: {
    position: 'absolute',
    width: 38,
    height: 38,
    borderRadius: 15,
    borderWidth: 2,
    borderColor: theme.color.coral,
  },
  disc: {
    width: 30,
    height: 30,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  discRaised: {
    backgroundColor: theme.color.coralInk,
    shadowColor: theme.color.coral,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.7,
    shadowRadius: 7,
    elevation: 8,
  },
  bolt: { fontSize: 15, color: theme.color.surface },

  switcher: {
    backgroundColor: theme.color.night,
    paddingHorizontal: theme.space.sm,
    paddingBottom: theme.space.xs,
    gap: 4,
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 99,
  },
  switchRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  pill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.onDarkTag,
  },
  pillOn: { backgroundColor: theme.color.volt },
  pillText: { ...theme.type.tag, color: theme.color.surface },
  pillTextOn: { color: theme.color.ink },
  switchText: { ...theme.type.tag, color: theme.color.onDarkTiny, flex: 1, textAlign: 'right' },
});
