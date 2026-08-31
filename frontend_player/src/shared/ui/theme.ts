/**
 * Raketa Player App — design tokens.
 *
 * THE source of colour, type, spacing, radius, elevation and motion values for
 * frontend_player. Components read from here; a literal hex, font size or gap in a
 * component is a bug, not a shortcut.
 *
 * Rules — see docs/design-system.md for the reasoning behind each:
 *   line   BOUNDS a thing        line2  is a FOLD inside one thing
 *   volt   a FILL anywhere, carrying `ink` (13.96:1); a STROKE only on dark, because as a
 *          foreground on paper it is ~1.3:1 and simply not there
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

  /** A FILL ANYWHERE, a STROKE ONLY ON DARK. `ink` on it is 13.96 wherever it is drawn, so
   *  a volt tag or button reads on paper; volt AS A FOREGROUND on paper is ~1.3:1, so a
   *  volt hairline, ring or border there is a line nobody sees. On night it is 10.60. */
  volt: '#D9F24B',

  // --- On-dark-card child colours (the dark card repaints its children) ---
  onDarkTiny: 'rgba(255,255,255,0.68)', // 6.97 on night
  onDarkEyebrow: 'rgba(255,255,255,0.52)', // 4.74 on night
  onDarkHair: 'rgba(255,255,255,0.15)',
  onDarkFill: 'rgba(255,255,255,0.17)', // the on-dark button
  onDarkFillPressed: 'rgba(255,255,255,0.26)',
  onDarkTag: 'rgba(255,255,255,0.14)',

  scrim: 'rgba(10,52,65,0.45)', // the night colour at 45%, not black

  /** THE COURT'S GROUND, and the system's only rule for text over a GENERATED fill.
   *
   *  The court is drawn from the selected sport's hue, so the ratio behind a white label
   *  would otherwise depend on which sport a player picked — every pair in
   *  docs/design-system.md 2.5 is a fixed pair and none of them can state that. PINNED at
   *  .93 (the prototype's two call sites disagreed at .92 and .94), which leaves the hue at
   *  most 7% of the ground: the dark end is `night` whatever the sport, and the light end is
   *  one of four known composites, 12.29-13.03 for white. Derived in textOnMedia.test.ts.
   *
   *  The night colour rather than a black, exactly as `scrim` is — the dim matches the
   *  palette, and the prototype's rgba(6,26,33) is a hex this palette does not have. */
  courtScrim: 'rgba(10,52,65,0.93)',
} as const;

/**
 * Sport identity deliberately reuses the semantic palette rather than extending it —
 * four more hues would make every screen with a sport dot noisier, and the dot is always
 * accompanied by the sport name in text. A FIFTH SPORT FORCES A REAL DECISION.
 *
 * That premise is TESTED, not asserted: it was checked against every Play site that draws a
 * sport hue — the sport chips, the sport tags on the player record, and the court gradient —
 * and every one carries the sport name on screen (docs/design-system.md 2.3). A surface that
 * draws one of these with no name beside it reopens the question as surely as a fifth sport.
 */
const sport = {
  padel: color.coral,
  tennis: color.mint,
  squash: color.night2,
  badminton: color.amber,
} as const;

// ---------------------------------------------------------------------------
// The generated poster's hues — a closed set, and deliberately NOT in `color`
// ---------------------------------------------------------------------------

/**
 * THE SIXTEEN HUES A GENERATED POSTER CAN BE (docs/design-system.md 6.9, ADR-0134).
 *
 * Exported beside the theme and never inside it. Colour in this system is picked by MEANING;
 * a poster hue is picked by a hash of a player id, so it is not a semantic colour and must
 * not be reachable where one is expected — a `theme.color.poster…` would be the first value
 * in the palette that means nothing, sitting where every other one means something.
 * `CourtPoster` is the only component that takes one, as a prop of this type: the exception
 * to *a literal hex in a component is a bug* is this list, and nothing else.
 *
 * **No poster can claim a Sport, by construction rather than by hope.** Every stop below is
 * at least 25° from `red`, `coral`, `mint`, `amber`, `volt` and every `sport` value, which
 * excludes two arcs — 341°→94° and 138°→220° — and leaves 44° and 121° to design in. That is
 * what keeps 2.3's premise true on a surface that draws a hue with no name beside it.
 *
 * **One pair of stops, and the pair is fixed in CIE LCh(uv) rather than in sRGB HSL.** Two
 * requirements bind it from opposite sides: white text over the poster needs 4.5:1 against
 * the LIGHT stop, and the `ink` figure — a graphical object, not text — needs 3:1 against the
 * DARK stop. Together they confine the whole ground to one narrow band of luminance, and
 * sixteen hues at one HSL `S`/`L` pair vary across that band by a factor of three between the
 * greens and the blues: there is no such pair that clears both, and the only sets that do are
 * grey. At one LCh lightness and chroma per stop every hue has the SAME luminance, so 2.5
 * publishes two ratios instead of thirty-two. Derived and held in `posterHues.test.ts`.
 *
 * The ramp is deliberately gentle — 1,21–1,23 between the stops is the most those two bounds
 * allow. A deeper one is not a tuning; it is one of the two ratios.
 */
export const POSTER_HUES = [
  { light: '#41840F', dark: '#3E741E' },
  { light: '#36851E', dark: '#357526' },
  { light: '#2A8628', dark: '#2D762C' },
  { light: '#1B8730', dark: '#247631' },
  { light: '#5174BA', dark: '#4B66A0' },
  { light: '#6370BB', dark: '#5963A1' },
  { light: '#6F6CBB', dark: '#6360A1' },
  { light: '#7A68BB', dark: '#6C5DA1' },
  { light: '#8664B9', dark: '#755A9F' },
  { light: '#915FB6', dark: '#7E569D' },
  { light: '#9C5BB2', dark: '#87529A' },
  { light: '#A556AC', dark: '#8F4F95' },
  { light: '#AD52A4', dark: '#964C8E' },
  { light: '#B45098', dark: '#9B4A84' },
  { light: '#B75088', dark: '#9F4A77' },
  { light: '#B85377', dark: '#9F4C69' },
] as const;

/** One member of the closed set. `CourtPoster` takes this and never a string. */
export type PosterHue = (typeof POSTER_HUES)[number];

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
  /** The deck card — the one surface that is NOT a card. It animates in, and translates and
   *  rotates out under the thumb, so it is a transient object being manipulated: a fourth
   *  member of the floating family (see `shadow.deckCard`), not a fifth exception to 4.3's
   *  rule about cards. The competitive candidate card in the pool stays a card at 13. */
  deckCard: 18,
  cardDark: 15,
  card: 13,
  popover: 13,
  toast: 12,
  /** The ⚡Play disc. Not the avatar rule — `round(30 x 0.33)` lands on 10 and the disc is
   *  not a face; 11 is the prototype's measured value, kept (docs/design-system.md 10.2).
   *  The active state's RING is this grown by `size.tabBar.ringGap + ringStroke` on every
   *  side, which is arithmetic the bar does rather than a second radius token. */
  fab: 11,
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
  /** The court's ground. A card at 13 is a surface a finger rests on; a court is a picture
   *  inside one, and 4.2's rule reads the other way for it — the smaller the surface, the
   *  tighter the corner. Named for its role beside the two nines already here rather than
   *  borrowing `avatar`, because a court is not a face and the next reader must not be able
   *  to change one by changing the other. */
  court: 9,
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
  /** The fit pill — 7.10. **26, which is the height every call site drew.** The prototype's
   *  class defaulted to 23 and was overridden inline at all five sites; UI §G1 records that
   *  the defaults are used nowhere, so the arrival takes the USED value and the unused one
   *  stops existing. The number inside is `num.xs`, the nearest mono role to the 12pt those
   *  same sites wrote — a seventh size step for one pill is what 15.3 says not to add. */
  fit: 26,
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
  /** The tick box — 6.11. 6.8's availability cell at the size a line of text wants, and
   *  the same 12 x 12 tick inside it: `availability.tick` and `availability.tickStroke`
   *  are read from there rather than restated, because it is the same mark and two copies
   *  of it are two marks to keep in step.
   *
   *  The ROW is the touch surface — box and label together — which is what gets the
   *  control to 44 without a `hit` entry, the way the radius slider's row does. A 20pt
   *  square with slop around it would be a target that stops at the words. */
  tickBox: {
    box: 20,
    row: 44, // = minTouch
  },
  /** The balance bar — 7.11. Three heights, and the segment labels are tied to them: at
   *  `lg` and `md` a label fits beside the fold, at `sm` it does not and the bar draws none.
   *  #219 B4 raised the type floor to 9,5pt, so the prototype's 8 / 8,5 / 9,5 collapse to one
   *  role (`tag`) and the size decides WHETHER there is a label rather than how small it is.
   *
   *  The bar's SCALE is not here, for 7.5's reason: the level bar's fixed 1,00-5,00 lives in
   *  the component that draws it, and this one's mapping-and-clamp lives in `BalanceBar.tsx`
   *  the same way. What is here is geometry. */
  balanceBar: { sm: 16, md: 18, lg: 24 },
  /** The switch — 6.12. The track and the knob are UI §G1's measured 40 x 23 and 18, and the
   *  inset is the arithmetic between them rather than a fourth number. The ROW is the touch
   *  surface, exactly as 6.11's is: a 23pt track is well under the 44pt minimum, and a
   *  `hitSlop` around it would leave the words beside it inert. */
  switch: { track: 40, height: 23, knob: 18, row: 44 },
  /** The court — 7.12, and the drawn object whose numbers cannot be derived.
   *
   *  `space` is the drawing's own box and every coordinate below is in it. The 1,32 aspect
   *  IS 132 / 100, kept as the two numbers the line-sets are drawn against rather than as a
   *  ratio, so a path and a seat are read against one grid.
   *
   *  **`seats` are per Sport and are not a mirror.** Squash has no net: both players stand on
   *  the same half (H-25), so seat 3 is not where seat 3 is in padel, and deriving the far
   *  side by reflecting the near one produces the wrong court for one sport in four. They are
   *  listed in SEAT ORDER — your side first, their side second — which is the order the court
   *  hands its children, and the order `{side}` is read off in `the-words.md` 20.4.
   *
   *  `line` is the chrome, as OPACITIES of one white rather than as five rgba values: the
   *  court's ground is generated, so its lines are a single colour at a set of weights, and
   *  spelling them as colours would put five near-identical whites in a palette that picks by
   *  meaning. `sideLabelOpacity` is 2.5's own recorded value — white at .6 is 5,46 against the
   *  worst of the four grounds, which already clears AA, so it is not raised.
   */
  court: {
    space: { width: 100, height: 132 },
    /** The seat face against the court's width, with a floor: below it a face is a dot. */
    seatRatio: 0.235,
    seatMin: 17,
    sideLabelOpacity: 0.6,
    line: {
      bound: 0.3,
      boundWidth: 1.6,
      inner: 0.24,
      innerWidth: 1.1,
      net: 0.85,
      netWidth: 1.8,
      netGlow: 0.35,
      netGlowWidth: 5,
      /** Squash's front wall — a band, not a line, and the only filled mark on any court. */
      wall: 0.16,
    },
    seats: {
      padel: [
        [30, 96],
        [70, 110],
        [30, 22],
        [70, 36],
      ],
      badminton: [
        [32, 98],
        [68, 110],
        [32, 22],
        [68, 34],
      ],
      tennis: [
        [50, 104],
        [50, 28],
      ],
      squash: [
        [34, 92],
        [66, 66],
      ],
    },
  },
  sportDot: 6,
  infoGlyph: 14,
  tabIcon: 16,
  /** The ⚡Play disc — 28 until the bar was built, unreferenced by anything, and off the
   *  3pt grid at both values. **30**, which is what #227 drew and measured. */
  fab: 30,
  /** The tab bar — 10.2. The bar's own geometry is 10.2's and is read from `space`:
   *  paddingTop `xs`, paddingBottom `md` + the bottom inset, an icon at `tabIcon`, and the
   *  smallest step on the grid between the icon and its label. What is here is the four
   *  values the grid and 10.2 do not between them supply.
   *
   *  `ringGap` and `ringStroke` are the ACTIVE state, kept as the two numbers 10.2 states
   *  rather than pre-added into a 38pt ring: the ring is `size.fab` grown by both on every
   *  side and its radius is `radius.fab` grown by both, and the bar does that arithmetic —
   *  the same reason the level bar keeps 7.5's y coordinates as coordinates. The ring is
   *  ABSOLUTELY positioned, so the 4pt it adds above the disc comes out of the bar's
   *  existing 6pt top padding and the bar's height does not change between screens.
   *
   *  `labelMaxScale` is the only Dynamic Type mechanism this surface has: Part 13 names the
   *  tab bar as the fixed-height exception AND permits `allowFontScaling={false}` only
   *  inside the level bar, which leaves a bounded multiplier and nothing else. **Derived,
   *  never chosen** — `tabBarLabelCap.test.ts` measures the five shipped labels against the
   *  real Archivo 700 advances in the narrowest phone's column and recomputes it, so a
   *  sixth tab or a longer word goes red rather than truncating on somebody's phone. */
  tabBar: {
    /** ADR-0135: Feather `zap`, inside the disc, smaller than the 16pt box the flanks use. */
    bolt: 15,
    ringGap: 2,
    ringStroke: 2,
    labelMaxScale: 1.7,
  },
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
// Elevation — five shadows in the whole system, all for things that genuinely float, plus
// one TEXT shadow, which is a different mechanism and not an elevation at all.
// CARDS NEVER HAVE ONE: depth on paper comes from the surface change and the 1pt border.
// The deck card is here because it is not a card, not because the rule bent.
//
// RN cannot express CSS spread, so these are calibrated approximations: the blur halves,
// the offset shrinks toward the negative spread, and the opacity comes down with it.
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
  /** The deck card, from `0 18px 40px -26px rgba(11,43,51,.45)`. The largest negative spread
   *  of the four — 26 of 40 blur — so it is the FAINTEST: the offset comes down hardest and
   *  the opacity with it. Not the tightest — its blur ties the sheet's, because 40px halves
   *  to 20 whatever the spread was. It floats least of the four, and its `elevation` says
   *  so. */
  deckCard: {
    shadowColor: '#0B2B33',
    shadowOffset: { width: 0, height: 7 },
    shadowOpacity: 0.12,
    shadowRadius: 20,
    elevation: 8,
  },
  /** THE ⚡PLAY DISC — the fifth, and the only one that is a colour rather than a dimming.
   *
   *  From the prototype's `0 6px 14px -6px rgba(232,72,43,.7)`, and CALIBRATED rather than
   *  copied: that rule carries a -6px spread against a 14px blur, so 6 of the 14 never
   *  reach the paper and RN has no way to say so.
   *
   *    blur 14   -> radius 7    the halving the other four do
   *    offset 6  -> 3           the spread eats the drop: 6 x (1 - 6/14) = 3,4
   *    opacity .7 -> .40        and the same fraction of the ink: .7 x (1 - 6/14)
   *
   *  `coral` rather than a bespoke dark hex, because the tint is the whole point — the disc
   *  is the one thing in the bottom chrome that floats, and it floats in its own colour.
   *  ON ANDROID IT DOES NOT: `elevation` draws the platform's black shadow and RN exposes
   *  no way to tint it, so the disc is raised on both platforms and glows on one. 6 seats it
   *  below the deck card, which is right — the bar is chrome and every overlay passes over
   *  it. */
  fab: {
    shadowColor: color.coral,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.4,
    shadowRadius: 7,
    elevation: 6,
  },
  /** TEXT ON GENERATED MEDIA — a textShadow, not an elevation, and the only one in the app.
   *
   *  Carried by EVERY label drawn over the court, both sets: the ratios `color.courtScrim`
   *  guarantees are the ground's light end, and a label can sit anywhere on the ramp. The
   *  prototype gave it to the seat labels and not to the side labels, which are the
   *  lower-contrast of the two. */
  textOnMedia: {
    textShadowColor: 'rgba(0,0,0,0.6)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
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
    /** A toast — 9.2. The prototype's 2600, kept: it is the read time of the longest of the
     *  nineteen sentences this app fires, and it is what the QUEUE spends per message, so
     *  shortening it is a decision about how long a listener waits rather than a tidy-up.
     *  Nothing surrounds it: the toast neither arrives nor leaves on an animation (1.5), so
     *  this is the whole of that component's timing and there is no reduced-motion branch. */
    toast: 2600,
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
