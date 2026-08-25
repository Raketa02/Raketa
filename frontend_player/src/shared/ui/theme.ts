/**
 * Raketa Player App — design tokens.
 *
 * THE source of colour, type, spacing, radius, elevation and motion values for
 * frontend_player. Components read from here; a literal hex, font size or gap in a
 * component is a bug, not a shortcut.
 *
 * Rules — see docs/design-system.md for the reasoning behind each:
 *   line   BOUNDS a thing        line2  is a FOLD inside one thing
 *   volt   on dark surfaces only (on paper it is ~1.3:1)
 *   Rule C white text never sits on `coral` or `mint`; it needs `coralInk` or
 *          `mintInk`. `ink` is the only dark that may sit on `coral` (4.50:1).
 *   Colour is picked by MEANING, never by appearance.
 *
 * React Native specifics that bite:
 *   - letterSpacing and lineHeight are in POINTS, not em/multiples. Pre-converted here.
 *   - fontWeight is IGNORED on Android when a custom fontFamily is set. Weight is
 *     selected by family name — use `font.sans[600]`, never `fontWeight: '600'`.
 *   - Nothing tappable may have a reachable area under 44 x 44pt. Use `hitSlop`.
 *
 * Every contrast ratio in the comments was computed against WCAG 2.1. Values corrected
 * from the v34 prototype are marked (!) with the reason.
 *
 * @see docs/design-system.md
 * @see docs/adr/0012-player-app-design-system.md
 */

// ---------------------------------------------------------------------------
// Colour
// ---------------------------------------------------------------------------

const color = {
  // --- Surfaces and structure ---
  paper: '#F4F2ED', // app background — warm off-white, never pure white
  paper2: '#EDEAE3', // recessed: the situation header, the popover close
  surface: '#FFFFFF', // cards, sheets, popovers, raised controls

  ink: '#101B20', // body text — 15.65 on paper, 17.50 on surface
  night: '#0A3441', // dark cards, avatars, fit badge, toast — white 13.29
  night2: '#12495B', // secondary dark — white 9.86
  /** (!) was #6E7F85 — `tiny` at 11pt was 3.73:1 on paper, the audit's own
   *  headline failure. Now 4.83 paper / 5.40 surface / 4.62 line2. */
  muted: '#5C6D73',

  line: '#E5E1D8', // BOUNDS a thing: card borders, chip borders
  line2: '#F0EDE6', // a FOLD inside one thing: hairlines, tag backgrounds, tracks

  // --- Accent: the only attention colour in the app ---
  coral: '#E8482B', // a MARK, not a text bed. ink on it 4.50 · white 3.89 (X)
  coralSoft: '#FDEBE6',
  coralInk: '#B8351C', // on coralSoft 5.11 · white on it 5.89
  coralLine: '#F3CFC5', // border of a coral note

  // --- Semantics: each means exactly one thing ---
  mint: '#0C8F6B', // settled, safe, covered. A MARK. white on it 4.07 (X)
  mintSoft: '#E2F3EC',
  mintInk: '#0A7355', // (!) new — on mintSoft 5.08 · white on it 5.84
  mintLine: '#CFE7DD',

  /** (!) was #9A6A0B (4.18 on its soft). Now 5.04 on amberSoft, white on it 5.70. */
  amber: '#8A5E09', // watch this — reversible, not yet wrong
  amberSoft: '#FBF0DA',
  amberLine: '#EFDCB8',

  red: '#B4392C', // ended badly. on redSoft 5.06 · white on it 5.90
  redSoft: '#FBEAE7',

  info: '#12495B', // explanation, NOT status. on infoSoft 8.63
  infoSoft: '#EAF1F4',
  infoLine: '#C7DBE3',

  /** DARK SURFACES ONLY — night on it 10.60, ink on it 13.96. Never on paper. */
  volt: '#D9F24B',

  // --- On-dark-card child colours (the dark card repaints its children) ---
  onDarkTiny: 'rgba(255,255,255,0.68)', // 6.97 on night
  onDarkEyebrow: 'rgba(255,255,255,0.52)', // 4.74 on night
  onDarkHair: 'rgba(255,255,255,0.15)',
  onDarkFill: 'rgba(255,255,255,0.17)', // the on-dark button
  onDarkFillPressed: 'rgba(255,255,255,0.26)',
  onDarkTag: 'rgba(255,255,255,0.14)',

  scrim: 'rgba(10,52,65,0.45)', // the night colour at 45%, not black
} as const;

/**
 * Sport identity deliberately reuses the semantic palette rather than extending it —
 * four more hues would make every screen with a sport dot noisier, and the dot is always
 * accompanied by the sport name in text. A FIFTH SPORT FORCES A REAL DECISION.
 */
const sport = {
  padel: color.coral,
  tennis: color.mint,
  squash: color.night2,
  badminton: color.amber,
} as const;

/**
 * The level bar's four bands. Three values each, not one with opacity:
 *   tint — the large bar fill
 *   deep — the current band's fill. NOT the bar's mark: 7.5 draws that in `coral`, and
 *          the legend calls it a coral tick. The two disagreed here until #25 built it.
 *   ink  — TEXT and the band card's left rail. (!) The prototype drew band names in
 *          `deep`, which is 2.83-3.20 on paper — below AA. Every `ink` is 4.51-4.59 on
 *          paper and >=5.05 for white on it.
 *
 * `lo`/`hi` are the DRAWING boundaries and are contiguous so the bar has no gaps. They
 * are NOT the model's band edges (1,0-1,5 / 1,6-2,6 / 2,7-3,8 / 3,9-5,0). Anything that
 * PRINTS a range prints the model's bandLo/bandHi. Confusing the two is a correctness
 * bug, not a styling one.
 */
const band = {
  new: { lo: 1.0, hi: 1.55, tint: '#9AA8AD', deep: '#7E8C92', ink: '#657075' },
  developing: { lo: 1.55, hi: 2.65, tint: '#7FB3CC', deep: '#4E8FAE', ink: '#40758F' },
  established: { lo: 2.65, hi: 3.85, tint: '#6FC5A8', deep: '#3FA184', ink: '#307A64' },
  advanced: { lo: 3.85, hi: 5.0, tint: '#F0A08A', deep: '#D9714F', ink: '#A9583E' },
} as const;

// ---------------------------------------------------------------------------
// Typography
//
// Weight is a FAMILY NAME. `fontWeight` is ignored on Android with a custom family,
// which is the most common way an RN app silently loses its typography on one platform.
// ---------------------------------------------------------------------------

const font = {
  sans: {
    400: 'Archivo_400Regular',
    500: 'Archivo_500Medium',
    600: 'Archivo_600SemiBold',
    700: 'Archivo_700Bold',
    800: 'Archivo_800ExtraBold',
  },
  mono: {
    400: 'IBMPlexMono_400Regular',
    500: 'IBMPlexMono_500Medium',
    600: 'IBMPlexMono_600SemiBold',
  },
  /** The information mark is a SYMBOL, not text — the serif form is the one people
   *  recognise. The only non-app family in the system. */
  serif: { ios: 'Georgia', android: 'serif' },
} as const;

/**
 * Type roles. There is no modular ratio — sizes are chosen per role.
 * `letterSpacing` and `lineHeight` are in POINTS, pre-converted from the prototype's em.
 */
const type = {
  h1: { fontFamily: font.sans[700], fontSize: 19, letterSpacing: -0.57, lineHeight: 24 },
  h2: { fontFamily: font.sans[700], fontSize: 15, letterSpacing: -0.38, lineHeight: 20 },
  /** The onboarding question itself. The prototype's 650 maps to 700. */
  question: { fontFamily: font.sans[700], fontSize: 15, letterSpacing: -0.38, lineHeight: 20 },
  cardTitle: { fontFamily: font.sans[700], fontSize: 13, lineHeight: 17 },
  inlineTitle: { fontFamily: font.sans[600], fontSize: 12.5, lineHeight: 17 },
  btn: { fontFamily: font.sans[700], fontSize: 12 },
  rlLabel: { fontFamily: font.sans[400], fontSize: 11.5, lineHeight: 16 },
  rlValue: { fontFamily: font.sans[600], fontSize: 11.5, lineHeight: 16 },
  /** The workhorse secondary text. 11 x 1.45 = 16. */
  tiny: { fontFamily: font.sans[400], fontSize: 11, lineHeight: 16 },
  /** FORM LABEL — labels a control you are about to OPERATE. Uppercase, near-black,
   *  a full point larger than the eyebrow and tighter-tracked, because a form label has
   *  to be findable at a glance and the muted eyebrow was not. */
  flab: { fontFamily: font.sans[700], fontSize: 10.5, letterSpacing: 0.95, lineHeight: 12 },
  chip: { fontFamily: font.sans[600], fontSize: 10.5 },
  /** EYEBROW — labels a region you are READING. Not interchangeable with flab. */
  eyebrow: { fontFamily: font.sans[700], fontSize: 9.5, letterSpacing: 1.43, lineHeight: 12 },
  tag: { fontFamily: font.sans[700], fontSize: 9.5, lineHeight: 12 },
} as const;

/**
 * Display numbers. Always mono, always tabular, tracking -0.035em pre-converted.
 * lineHeight equals the size: a 40pt level must not grow the card it sits in.
 */
const num = {
  levelHero: { fontFamily: font.mono[600], fontSize: 40, letterSpacing: -1.4, lineHeight: 40 },
  levelLarge: { fontFamily: font.mono[600], fontSize: 26, letterSpacing: -0.91, lineHeight: 26 },
  xl: { fontFamily: font.mono[600], fontSize: 22, letterSpacing: -0.77, lineHeight: 22 },
  l: { fontFamily: font.mono[600], fontSize: 19, letterSpacing: -0.67, lineHeight: 19 },
  m: { fontFamily: font.mono[600], fontSize: 17, letterSpacing: -0.6, lineHeight: 17 },
  s: { fontFamily: font.mono[500], fontSize: 14, letterSpacing: -0.49, lineHeight: 18 },
  xs: { fontFamily: font.mono[500], fontSize: 13, letterSpacing: -0.46, lineHeight: 17 },
} as const;

/**
 * Apply to every figure that is compared vertically. Mono is the mechanism, not a style.
 *
 * Deliberately NOT `as const`: React Native's `TextStyle['fontVariant']` is a mutable
 * array, and a `readonly` one is not assignable to it.
 */
const tabular: { fontVariant: 'tabular-nums'[] } = { fontVariant: ['tabular-nums'] };

// ---------------------------------------------------------------------------
// Space — a 3pt grid.
//
// The prototype used 5,6,7,9,10,11,12,13,14,15. Every one is within 1pt of a multiple
// of 3: the grid was already there and unnamed.
// ---------------------------------------------------------------------------

const space = {
  xxs: 3,
  xs: 6,
  /** THE GAP BETWEEN STACKED CARDS, and the hairline's top margin. */
  sm: 9,
  md: 12,
  /** THE HORIZONTAL PAGE GUTTER. Content width = screen width - 30. */
  lg: 15,
  xl: 18,
  xxl: 24,
  xxxl: 30,
} as const;

// ---------------------------------------------------------------------------
// Radius — the bigger the surface, the rounder. A dark card is 15 where a light one is
// 13, because the darker fill makes the corner read tighter at the same radius.
// ---------------------------------------------------------------------------

const radius = {
  sheet: 22, // top corners only
  cardDark: 15,
  card: 13,
  popover: 13,
  toast: 12,
  btn: 10,
  note: 10,
  daySquare: 10,
  seg: 10,
  segThumb: 8,
  /** The availability grid's cell. A fresh token beside the dead `daySquare`: the slot
   *  squares of the deleted 6.7 are NOT being restored, and a cell that borrowed their
   *  radius would be the first step back toward a booking grid. */
  availabilityCell: 10,
  avatar: 9,
  hourSquare: 9,
  rangeSquare: 9,
  timeSquare: 8,
  balanceBar: 8,
  fit: 7,
  tag: 6,
  dot: 6,
  meter: 3,
  bar: 2,
  /** The chip is the only true pill. Compute as height / 2. */
  pill: 999,
} as const;

// ---------------------------------------------------------------------------
// Component metrics
// ---------------------------------------------------------------------------

const size = {
  btn: 34, // 32 tertiary-in-card · 34 default · 40 screen action · 42 result primary
  btnSm: 32,
  btnLg: 40,
  btnXl: 42,
  chip: 27,
  chipSm: 25,
  seg: 25,
  tag: 19,
  fit: 23,
  avatar: 27,
  timeSquare: 32,
  meter: 5,
  bar: 4,
  /** The confidence ring — a drawn object, dark card only. Stroke matches the level
   *  bar's band segments; the tick crosses the stroke and overshoots it outward.
   *  Geometry and reasoning: docs/design-system.md 7.8. The 30% ceiling the tick marks
   *  is a domain constant, NOT a design value — it does not belong here. */
  ring: 72,
  ringStroke: 6,
  ringTick: 2,
  ringTickOvershoot: 3,
  /** The level bar — the other drawn object, per docs/design-system.md 7.5.
   *
   *  `trackTop`, `bracketTop` and `namesTop` are 7.5's own y coordinates, kept as
   *  coordinates rather than pre-subtracted into margins, so this block can be read
   *  against the specification line by line. The component does the arithmetic.
   *
   *  Its scale is always the full 1,00-5,00, exactly as the ring's is always 0-100 —
   *  that is what makes a value land in the same place on every screen that draws one. */
  levelBar: {
    trackTop: 0,
    trackHeight: 6,
    trackRadius: 3,
    /** 1pt separators between segments, drawn in the surface colour. */
    segmentSeparator: 1,
    /** Bands that are not the player's. A shape carries the state as well: the mark. */
    inactiveOpacity: 0.38,
    markTop: -3,
    markWidth: 3,
    markHeight: 12,
    markRing: 2,
    bracketTop: 13,
    bracketHeight: 8,
    bracketStroke: 2,
    namesTop: 24,
  },
  /** The question navigator — the third drawn object, per docs/design-system.md 7.9.
   *
   *  Fixed-width segments in a left-aligned row: the row GROWS and never arrives, which
   *  is how it claims no total. A flex-filled track would put the last segment at the
   *  right edge and assert a denominator the engine does not have. At the engine's
   *  10-question ceiling the row is 10 x 12 + 9 x 3 = 147pt against 290pt of content on
   *  the narrowest phone, so it is visibly short of the end at every length it reaches.
   *
   *  `currentHeight` is double `segmentHeight` for the same reason the level bar's mark
   *  is double its track: height carries the state, never opacity alone. The segments are
   *  NOT touch targets — ten of them across the content width is 26pt each against the
   *  44pt minimum, so the navigator indicates and the header's back control moves. */
  navigator: {
    segmentWidth: 12,
    segmentHeight: 4, // = size.bar
    segmentRadius: 2,
    currentHeight: 8,
    currentRadius: 3,
    gap: 3,
  },
  /** The availability grid — 6.8. Seven rows of three, days DOWN and parts of the day
   *  ACROSS, which is a touch decision and not a taste one: seven columns want
   *  7 x 44 = 308pt against the 290pt of content the narrowest phone has, and no
   *  hit-slop closes that. Laid out the other way the cell reaches the minimum by its own
   *  geometry — the first control in the app that does — so there is no `hit` entry here.
   *
   *  `labelMaxRatio` caps the day-label column so Dynamic Type grows the labels without
   *  starving the cells: at the cap the three still share 65,5pt each on that phone.
   *  `footnoteMinHeight` is two lines of `type.tiny`, always laid out, so ticking the
   *  first cell never moves the grid out from under the finger. */
  availability: {
    cellHeight: 44, // = minTouch, by geometry rather than by slop
    gap: 6,
    labelGutter: 9,
    labelMaxRatio: 0.25,
    tick: 12,
    tickStroke: 2,
    footnoteMinHeight: 2 * type.tiny.lineHeight,
  },
  /** The photo tile — 6.9. Three across the content width, 3:4 portrait, at the card
   *  radius because a 90 x 121 tile is a card-sized surface.
   *
   *  `strip` is the foot strip: ONE slot with three mutually exclusive occupants — the
   *  profile marker, the upload bar, the failure notice — which is what keeps a settled
   *  photo undecorated. `remove` is a 28pt visual grown to 44 by `hit.photoRemove`, and
   *  that square is anchored INSIDE the tile: 6.5 bounds horizontal slop by the neighbour,
   *  and at a 9pt gap an overhanging target would reach 40,5. */
  photoTile: {
    columns: 3,
    gap: 9,
    aspectRatio: 0.75, // 3:4 portrait — RN's aspectRatio is width / height
    strip: 18,
    progressBar: 4, // = size.bar
    progressInset: 6,
    remove: 28,
    addGlyph: 20,
    addGlyphStroke: 2,
  },
  /** The radius slider — 6.10. The ROW is the touch surface, not the thumb: a press
   *  anywhere on it moves the value there, which is what gets the control to 44 without a
   *  `hit` entry and without two more targets beside it.
   *
   *  The thumb is the level bar's mark idiom in a circle — a `night` disc inside a
   *  `surface` ring, because the fill behind it is `night` too and the ring is the whole
   *  reason it reads. The minimum, maximum, step and default are NOT here: they are served
   *  by `GET /player-profile/options`, exactly as the ring's ceiling is served on the
   *  result (7.8). */
  radiusSlider: {
    row: 44, // = minTouch
    trackHeight: 4, // = size.bar
    thumb: 20,
    thumbRing: 3,
  },
  balanceBar: 24,
  sportDot: 6,
  infoGlyph: 14,
  tabIcon: 16,
  fab: 28,
  grabber: { width: 36, height: 4 },
  sheetClose: 28,
  popoverWidth: 250,
  popoverArrow: 11,
  pagerDot: 5,
  pagerDotActive: 14,
  /** Horizontal page gutter, both sides. Content width = screen width - gutters. */
  gutter: space.lg,
  /** The card rail's peek IS the affordance. A RATIO, never 268pt — on a 320pt phone
   *  a fixed 268 leaves no peek at all. */
  railCardRatio: 0.74,
  /** Nothing tappable may have a reachable area smaller than this. Use hitSlop. */
  minTouch: 44,
} as const;

/** hitSlop presets that lift each control to a 44pt reachable height. Horizontal slop is
 *  bounded by the neighbour: in a row with a 6pt gap, at most 3 per side. */
const hit = {
  chip: { top: 9, bottom: 9, left: 3, right: 3 },
  chipSm: { top: 10, bottom: 10, left: 3, right: 3 },
  timeSquare: { top: 6, bottom: 6, left: 3, right: 3 },
  seg: { top: 9, bottom: 9 },
  btn: { top: 5, bottom: 5 },
  infoMark: { top: 12, bottom: 12, left: 12, right: 12 },
  /** Anchored inside the tile, not over its corner — see `size.photoTile`. All four sides
   *  are equal because none of them crosses an edge. */
  photoRemove: { top: 8, bottom: 8, left: 8, right: 8 },
} as const;

// ---------------------------------------------------------------------------
// Elevation — three shadows in the whole system, all for things that genuinely float.
// CARDS NEVER HAVE ONE: depth on paper comes from the surface change and the 1pt border.
//
// RN cannot express CSS spread, so these are calibrated approximations.
// ---------------------------------------------------------------------------

const shadow = {
  sheet: {
    shadowColor: '#0A2028',
    shadowOffset: { width: 0, height: -8 },
    shadowOpacity: 0.18,
    shadowRadius: 20,
    elevation: 16,
  },
  popover: {
    shadowColor: '#0B1F2A',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.24,
    shadowRadius: 15,
    elevation: 12,
  },
  toast: {
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.24,
    shadowRadius: 14,
    elevation: 10,
  },
} as const;

// ---------------------------------------------------------------------------
// Motion — one entrance, one sheet, one popover, one fade. Nothing else moves.
// Press feedback is immediate (Pressable's `pressed`), not animated: the prototype's
// 120ms is a mouse-hover transition and has no touch equivalent.
//
// Every one of these is skipped when AccessibilityInfo.isReduceMotionEnabled is true.
// ---------------------------------------------------------------------------

const motion = {
  fade: 200,
  rise: 300,
  sheet: 260,
  popover: 130,
  /** The prototype's cubic-bezier(.2,.8,.2,1) — decelerating. */
  easeDecel: { x1: 0.2, y1: 0.8, x2: 0.2, y2: 1 },
  /** How long a state is SHOWN — the one thing here that reduced motion does not skip.
   *
   *  Nested so the block above keeps its one-line contract (*the four things reduced
   *  motion skips*); a fifth flat key would have quietly broken it for whoever adds the
   *  next duration. A held duration is not an animation: nothing moves, and the player
   *  who asked the OS to calm things down is the last one who should get a 120ms flash
   *  where the rating comes into existence (docs/design-system.md 12.1, Part 13). */
  hold: {
    /** The calculating screen. Coupled to its copy staying ONE short line — a sentence a
     *  player cannot finish before the screen leaves is worse than no sentence at all, so
     *  if the copy grows this grows with it, as an amendment rather than a tweak. */
    calculating: 1200,
  },
} as const;

/** zIndex is scoped to the parent in RN, so overlays render from a single root-level
 *  overlay host — which is also what keeps a popover out of a dark card's repaint. */
const layer = { sheet: 20, toast: 40, popover: 60 } as const;

// ---------------------------------------------------------------------------

export const theme = {
  color,
  sport,
  band,
  font,
  type,
  num,
  tabular,
  space,
  radius,
  size,
  hit,
  shadow,
  motion,
  layer,
} as const;

export type Theme = typeof theme;
export type BandKey = keyof typeof band;
export type SportKey = keyof typeof sport;
