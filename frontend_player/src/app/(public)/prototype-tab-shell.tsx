/**
 * ⚠️ THROWAWAY PROTOTYPE — not production. Lives on `research/tab-shell` and is deleted
 * from `main`. Written for
 * [#227 The five-tab shell, and where back goes](https://github.com/Raketa02/Raketa02/issues/227).
 *
 * THE QUESTION
 *   What is the tab shell, and how does ⚡ Play declare that it is the active tab?
 *   UI spec §E7 records that the FAB is emitted down a branch that never takes the
 *   selected class, so for the whole of Find a game, Match me, the court and the pool the
 *   bar shows no active tab at all. AC-7 requires Play stay highlighted for all four.
 *
 * WHAT VARIES  — two axes, both switched from the bar pinned at the TOP of the screen
 *   (the subject is at the bottom, so the switcher may not sit on top of it).
 *
 *   1. ACTIVE-STATE IDIOM
 *      A · Ringed disc   — UI Open decision #4's literal recommendation: a volt ring.
 *                          Drawn here so its ~1.3:1 on paper is visible rather than argued.
 *      B · Label-led     — the disc never changes; Play's label takes the SAME active
 *                          idiom as the other four, so all five tabs declare it identically.
 *      C · Seated disc   — raised means "you can go there", seated means "you are there":
 *                          active drops the shadow, deepens the fill to coralInk and cuts
 *                          a paper collar, so the disc sits IN the bar.
 *
 *   2. LABEL TYPE ROLE — §10.2 sets paddingTop 6, paddingBottom 12 + inset and a 16pt icon
 *      box, and stops. It never sets a label size. The UI spec has 8.5/600, below the 9.5
 *      floor #219 fixed. Cycle eyebrow (9.5 tracked, uppercase) · tag (9.5 flat) ·
 *      flab (10.5 tracked, uppercase, near-black).
 *
 * WHAT IS REAL  — real safe-area insets (§D3's whole point), real `theme.ts` tokens, and
 *   the back stack actually wired: E-1/AC-1/AC-2, AC-4/E-3, E-8, AC-7, AC-144. Walk it.
 *
 * WHAT IS FAKE  — every screen body is one line of text. No data, no network, no state
 *   that survives a reload. The icons are §10.2's honest `currentColor` squares.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { theme } from '@/shared/ui';

// ---------------------------------------------------------------------------
// The model
// ---------------------------------------------------------------------------

type ScreenId = 'now' | 'around' | 'chats' | 'you' | 'find' | 'deck' | 'builder' | 'pool';
type TabId = 'now' | 'around' | 'play' | 'chats' | 'you';

const PLAY_SCREENS: ScreenId[] = ['find', 'deck', 'builder', 'pool'];

const TABS: { id: TabId; label: string }[] = [
  { id: 'now', label: 'Now' },
  { id: 'around', label: 'Around' },
  { id: 'play', label: 'Play' },
  { id: 'chats', label: 'Chats' },
  { id: 'you', label: 'You' },
];

const tabOf = (s: ScreenId): TabId => (PLAY_SCREENS.includes(s) ? 'play' : (s as TabId));

type Variant = 'A' | 'B' | 'C';
const VARIANTS: { id: Variant; name: string }[] = [
  { id: 'A', name: 'Ringed disc — CHOSEN' },
  { id: 'B', name: 'Label-led' },
  { id: 'C', name: 'Seated disc' },
];

type LabelRole = 'eyebrow' | 'tag' | 'flab';
const LABEL_ROLES: LabelRole[] = ['eyebrow', 'tag', 'flab'];
const UPPERCASE: Record<LabelRole, boolean> = { eyebrow: true, tag: false, flab: true };

// ---------------------------------------------------------------------------
// The shell
// ---------------------------------------------------------------------------

export default function PrototypeTabShell() {
  const insets = useSafeAreaInsets();
  // Defaults are the DECIDED design: A, with `tag` labels. B and C are kept because the
  // branch is the primary source of the exploration, not just of the answer.
  const [variant, setVariant] = useState<Variant>('A');
  const [role, setRole] = useState<LabelRole>('tag');

  // The whole navigation model. `stack[0]` is what BACK falls out to.
  const [stack, setStack] = useState<ScreenId[]>(['now']);
  const [sent, setSent] = useState(false);
  const current = stack[stack.length - 1] as ScreenId;

  const push = (s: ScreenId) => setStack((k) => [...k, s]);
  const back = () => setStack((k) => (k.length > 1 ? k.slice(0, -1) : k));

  /** E-1 / AC-1 / AC-2 — the ⚡ button always opens Find a game, whichever Play tab was
   *  used last, and Home sits behind it so BACK leaves Play entirely. */
  const openPlay = () => {
    setSent(false);
    setStack(['now', 'find']);
  };

  const goTab = (t: TabId) => {
    setSent(false);
    if (t === 'play') return openPlay();
    setStack([t]);
  };

  /** AC-144 / E7 — the line-up is cleared and the journey ENDS. There is no game screen on
   *  this map, so the send lands on Now and the Play stack is discarded: no back-path into
   *  the arrangement that was sent. */
  const send = () => {
    setSent(true);
    setStack(['now']);
  };

  const activeTab = tabOf(current);

  return (
    <View style={styles.root}>
      <Switcher
        top={insets.top}
        variant={variant}
        role={role}
        stack={stack}
        onVariant={setVariant}
        onRole={setRole}
      />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[styles.scrollBody, { paddingTop: insets.top + 74 }]}
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

      {/* §D4 — the CTA and the bar are flex siblings outside the scroller, not fixed. */}
      {current === 'builder' ? (
        <View style={styles.cta}>
          <Pressable style={styles.ctaBtn} onPress={send}>
            <Text style={styles.ctaLabel}>Send the challenge</Text>
          </Pressable>
        </View>
      ) : null}

      <TabBar
        variant={variant}
        role={role}
        active={activeTab}
        bottomInset={insets.bottom}
        onPress={goTab}
      />
    </View>
  );
}

// ---------------------------------------------------------------------------
// The bar — the thing being judged
// ---------------------------------------------------------------------------

function TabBar({
  variant,
  role,
  active,
  bottomInset,
  onPress,
}: {
  variant: Variant;
  role: LabelRole;
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
            variant={variant}
            role={role}
            selected={active === 'play'}
            onPress={() => onPress('play')}
          />
        ) : (
          <FlankTab
            key={t.id}
            label={t.label}
            role={role}
            selected={active === t.id}
            onPress={() => onPress(t.id)}
          />
        ),
      )}
    </View>
  );
}

function FlankTab({
  label,
  role,
  selected,
  onPress,
}: {
  label: string;
  role: LabelRole;
  selected: boolean;
  onPress: () => void;
}) {
  const tone = selected ? theme.color.ink : theme.color.muted;
  return (
    <Pressable
      style={styles.column}
      onPress={onPress}
      accessibilityRole="tab"
      accessibilityLabel={label}
      accessibilityState={{ selected }}
    >
      {/* §10.2 — the icon set is a separate recorded decision. A square is the honest
          placeholder: it specifies the 16pt box and the position, not the glyph. */}
      <View style={[styles.icon, { backgroundColor: tone }]} />
      <Label role={role} text={label} color={tone} />
    </Pressable>
  );
}

function PlayTab({
  variant,
  role,
  selected,
  onPress,
}: {
  variant: Variant;
  role: LabelRole;
  selected: boolean;
  onPress: () => void;
}) {
  // A · the disc never changes shape; a 3pt volt ring is added. UI Open #4's own words.
  // B · the disc never changes at all; the LABEL carries what the other four carry.
  // C · raised at rest, seated when active: shadow off, fill deepened, paper collar.
  const seated = variant === 'C' && selected;

  const disc = [styles.disc, seated ? styles.discSeated : styles.discRaised];

  const labelColor =
    variant === 'B' ? (selected ? theme.color.ink : theme.color.muted) : theme.color.ink;

  return (
    <Pressable
      style={styles.column}
      onPress={onPress}
      accessibilityRole="tab"
      accessibilityLabel="Play"
      accessibilityState={{ selected }}
    >
      <View style={styles.discBox}>
        {/* The ring is ABSOLUTE, so entering Play never changes the bar's height. A bar
            that grows 8pt when you arrive is a worse orientation cue than none. The 2pt
            gap between disc and ring is the bar's own `surface`, so there is no collar to
            token: coral reads 3.89:1 against it on BOTH edges. */}
        {variant === 'A' && selected ? <View style={styles.ring} /> : null}
        <View style={disc}>
          {/* §E6 — the ⚡ is hidden from the reader; the visible "Play" label already says it. */}
          <Text style={styles.bolt} accessibilityElementsHidden importantForAccessibility="no">
            ⚡
          </Text>
        </View>
      </View>
      <Label role={role} text="Play" color={labelColor} />
    </Pressable>
  );
}

function Label({ role, text, color }: { role: LabelRole; text: string; color: string }) {
  return (
    <Text
      numberOfLines={1}
      style={[theme.type[role], styles.label, { color }]}
      // Part 13 forbids `allowFontScaling={false}` outside the level bar, and names the
      // tab bar as the fixed-height exception. The third mechanism — scale, but bounded.
      maxFontSizeMultiplier={1.6}
    >
      {UPPERCASE[role] ? text.toUpperCase() : text}
    </Text>
  );
}

// ---------------------------------------------------------------------------
// The screens — one line of text each, plus whatever route the rules need
// ---------------------------------------------------------------------------

const ONE_LINER: Record<ScreenId, { title: string; line: string }> = {
  now: { title: 'Now', line: 'Nothing is happening yet. Tap ⚡ to find a game.' },
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
      {/* §C / Open #6 — the header is the first child INSIDE the scroller, so it scrolls
          away. Nothing sticks. */}
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
            Challenge sent. The line-up is cleared and there is no way back into it — AC-144 with no
            game screen to land on.
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
          <Action label="⚡ Let the engine fill the seats" onPress={() => undefined} />
        </>
      ) : null}

      {id === 'pool' ? (
        <Action label="Court — back to the builder (E-8)" onPress={() => onPopTo('builder')} />
      ) : null}

      {id === 'deck' ? <Action label="Say yes (mutual → sent)" onPress={onSend} /> : null}

      <Text style={styles.foot}>
        {inPlay
          ? 'Play stays the active tab here — AC-7. Press back and watch where you land.'
          : 'Not a Play screen. The bar should say so.'}
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
  variant,
  role,
  stack,
  onVariant,
  onRole,
}: {
  top: number;
  variant: Variant;
  role: LabelRole;
  stack: ScreenId[];
  onVariant: (v: Variant) => void;
  onRole: (r: LabelRole) => void;
}) {
  const name = VARIANTS.find((v) => v.id === variant)?.name ?? '';
  return (
    <View style={[styles.switcher, { paddingTop: top + 6 }]}>
      {/* #238 lives on a DIFFERENT route. This bar's squares never change, so landing
          here looking for glyph variants shows nothing varying. One tap across. */}
      <Pressable style={styles.crossLink} onPress={() => router.push('/prototype-tab-glyphs')}>
        <Text style={styles.crossLinkText}>
          #238 — the glyph prototype is on /prototype-tab-glyphs →
        </Text>
      </Pressable>
      <View style={styles.switchRow}>
        {VARIANTS.map((v) => (
          <Pressable
            key={v.id}
            style={[styles.pill, variant === v.id ? styles.pillOn : null]}
            onPress={() => onVariant(v.id)}
          >
            <Text style={[styles.pillText, variant === v.id ? styles.pillTextOn : null]}>
              {v.id}
            </Text>
          </Pressable>
        ))}
        <Text style={styles.switchText}>{name}</Text>
      </View>
      <View style={styles.switchRow}>
        {LABEL_ROLES.map((r) => (
          <Pressable
            key={r}
            style={[styles.pill, role === r ? styles.pillOn : null]}
            onPress={() => onRole(r)}
          >
            <Text style={[styles.pillText, role === r ? styles.pillTextOn : null]}>{r}</Text>
          </Pressable>
        ))}
        <Text style={styles.switchText}>{stack.join(' › ')}</Text>
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

  // §10.2 — equal columns, paddingTop 6, paddingBottom 12 + bottom inset.
  bar: {
    flexDirection: 'row',
    backgroundColor: theme.color.surface,
    borderTopWidth: 1,
    borderTopColor: theme.color.line,
    paddingTop: theme.space.xs,
  },
  column: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', gap: 4 },
  icon: { width: theme.size.tabIcon, height: theme.size.tabIcon, borderRadius: 5 },
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
    // §6.1 `primary`: the disc is not a new colour treatment, it is the primary button in
    // a squircle — coralInk fill, white mark, brightening to coral on press (§2.2 Rule C).
    // The prototype's white-on-coral ⚡ was 3.89:1, the exact pairing §2.2 refuses.
    backgroundColor: theme.color.coralInk,
    // §A3's `0 6px 14px -6px rgba(232,72,43,.7)` — a FIFTH shadow, and #219 already added
    // a fourth. If C wins, this token is never created.
    shadowColor: theme.color.coral,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.7,
    shadowRadius: 7,
    elevation: 8,
  },
  discSeated: {
    backgroundColor: theme.color.coralInk,
    borderWidth: 3,
    borderColor: theme.color.paper,
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
  crossLink: {
    backgroundColor: theme.color.volt,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.space.sm,
    paddingVertical: 4,
    marginBottom: 2,
  },
  crossLinkText: { ...theme.type.tag, color: theme.color.ink, textAlign: 'center' },

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
