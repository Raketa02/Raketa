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
 *          foreground on paper it is ~1.3:1 and simply not there. Where volt's MEANING needs
 *          a stroke on paper, that is `voltStroke` — the same relationship `coralInk` has to
 *          `coral`, and never volt with a border width on it
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
  paper3: '#E2DED3', // the club card's tray — 1.20 on paper, where paper2 is 1.07 (#529)
  surface: '#FFFFFF', // cards, sheets, popovers, raised controls

  ink: '#101B20', // body text — 15.65 on paper, 17.50 on surface
  night: '#0A3441', // dark cards, avatars, fit badge, toast — white 13.29
  night2: '#12495B', // secondary dark — white 9.86
  /** (!) was #6E7F85 — `tiny` at 11pt was 3.73:1 on paper, the audit's own
   *  headline failure. Now 4.83 paper / 5.40 surface / 4.62 line2. */
  muted: '#5C6D73',
  muted2: '#4E5E64', // secondary text on paper3 — 5.02, where muted there is 4.02

  line: '#E5E1D8', // BOUNDS a thing: card borders, chip borders
  line2: '#F0EDE6', // a FOLD inside one thing: hairlines, tag backgrounds, tracks

  // --- Loading: a shape standing where a screen's content will be ---
  /** THE SKELETON'S SHAPE (PRD #867, #868; 1.5, 15.2, Part 16 2026-11-24): a block, a line or a
   *  circle drawn where a screen's content will be while its first read is out. **`paper3`'s value
   *  under a name of its own**, because the meaning is new and the value is not (15.2: no new
   *  colour). Computed from the hex values (WCAG 2.1): 1.20 on `paper` and 1.34 on `surface`, the
   *  two grounds a skeleton is drawn on, so it reads as a shape on both. **Refused** (the loading
   *  shimmer log's §2.2, Q23): `line`, the nearest value at 1.17 and 1.30, because it BOUNDS a
   *  thing; `paper2` (1.07 on paper) and `line2` (1.05), too faint on paper. 1.4.11's 3:1 is not
   *  asked of it: it is hidden from a listener and carries nothing a player needs to read. */
  skeleton: '#E2DED3',
  /** THE SKELETON'S SHEEN (PRD #867, #868; Q23): the band's peak, **`paper`'s value**. The band's
   *  gradient runs `skeleton` → this → `skeleton`, so at its brightest a shape lifts to the ground it
   *  stands on, and no opacity number is needed. On `surface` the peak is still 1.12 off the white,
   *  so a shape on a card never vanishes into it. */
  skeletonSheen: '#F4F2ED',

  // --- The tab bar: the one glass surface (1.1's exception, 10.2, ADR-0210 §2) ---
  /** THE DOCK'S GLASS (#883): white at .88, over a blur wherever the platform draws the glass
   *  (`theme.glass`), so the page passing under the dock shows as a soft wash. **88, not the
   *  brief's two-thirds**: idle words must hold 4.5:1 over the darkest ground that passes under
   *  the dock most often, Home's game card (`night`), and at .88 `tabIdle` reads **4.53** there and
   *  4.90 over paper (WCAG 2.1 from the hex values, ADR-0210 §2). It falls a hair short over `ink`
   *  (4.49) and black (4.44), which the blur's averaging is expected to close — #885 looks. Where
   *  the dock draws no glass, its fill is `surface`. */
  glass: 'rgba(255,255,255,0.88)',
  /** AN IDLE TAB'S ICON AND LABEL (#883): `ink` at .62, **not `muted`** — an alpha ink darkens
   *  with the ground under the glass, and a fixed `muted` doesn't (2.77 on two-thirds glass over
   *  `night`). 4.90 over paper, 4.53 over `night`, through 88% glass. */
  tabIdle: 'rgba(16,27,32,0.62)',

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
   *  volt hairline, ring or border there is a line nobody sees. On night it is 10.60.
   *  A stroke on paper that MEANS volt is `voltStroke`, below — never this value. */
  volt: '#D9F24B',

  /** VOLT'S STROKE — the same meaning at the ratio a border needs, and never a soft.
   *
   *  `coralInk` is to `coral` what this is to `volt`: one meaning, a second value, because the
   *  base colour cannot carry the role. Volt as a foreground on paper is 1.25 on `surface` and
   *  1.12 on `paper` — a line nobody sees — so the 2026-08-31 amendment refused a volt stroke
   *  on paper, and refused a darker companion with it on the grounds that *that is no longer
   *  volt*. #310's designs overrule the second half and keep the first: the card that says
   *  *Wants to play you* takes a green border, and volt itself still cannot draw one.
   *
   *  NOT `voltLine`, which is what that amendment called the refused companion and what every
   *  reader of `coralLine` / `mintLine` / `amberLine` / `infoLine` would take it for: in this
   *  palette a `*Line` is THE SOFT'S BORDER, and volt has no soft and needs none (`Tag.tsx`).
   *  Named for the role it fills instead, which is the half of `coralInk`'s analogy the suffix
   *  would otherwise have contradicted.
   *
   *  #698A0F is 76.1 deg — 7 deg off volt, so it reads as volt's own family, and 37 deg off
   *  `amber`, which is the only other dark warm hue it could be mistaken for. As a STROKE it is
   *  4.01 on surface, 3.58 on paper and 3.07 against the `line` border it replaces: all three
   *  clear 1.4.11's 3:1, the third being what makes the marked card differ VISIBLY from an
   *  ordinary one. NEVER A TEXT BED — white on it is 4.01 and `ink` on it 4.37, so a label
   *  belongs on the volt fill beside it. Derived in Tag.test.tsx. */
  voltStroke: '#698A0F',

  /** A STAGE STILL BEING ARRANGED — the dot on the Now card's tag while the game is in the
   *  players' hands: the plan before it is played (*Planning*), the result after it (*Needs
   *  result*, *Confirm the result*). Mint is the settled stage and `onDarkHair` the quiet
   *  endings; this is the third dot, and the meaning is named rather than the hue (#413).
   *
   *  ON DARK ONLY. It is drawn on `night`, inside the on-dark tag and as the Now card's *Fill
   *  the seat* fill (6.1's `arranging` button, #429), and nowhere on paper — so there is no
   *  soft and no line. Nothing borders it; the one thing that writes on it writes in `ink`,
   *  7,05:1, because white on it is 2,48:1 (Button.tsx).
   *
   *  (!) MEASURED, then lifted. Mock 1 draws the dot at #87641A — hue 40,7°, which is `amber`
   *  (39,5°) within a degree and within a step of lightness, at 2,45 on `night` and 1,61 on the
   *  tag it sits in. That is the value the ticket itself calls invisible on `night`, and a dot
   *  nobody can see carries no meaning there. So the hue and the saturation are the mock's and
   *  ONLY the lightness is raised, to the step past the first that clears 1.4.11's 3:1 on the
   *  tag's ground (.46 clears it at 3,12; a ratio one rounding from failing is one the next
   *  tuning takes under, `photoScrim`'s rule): 5,35 on `night`, 3,49 on `onDarkTag` over it,
   *  3,17 on `onDarkFill` over it. 31° off `coral` and 28° off `volt`, so it is neither's
   *  family. Derived in Tag.test.tsx. */
  arranging: '#D29B28',

  // --- On-dark-card child colours (the dark card repaints its children) ---
  onDarkTiny: 'rgba(255,255,255,0.68)', // 6.97 on night
  onDarkEyebrow: 'rgba(255,255,255,0.52)', // 4.74 on night
  onDarkHair: 'rgba(255,255,255,0.15)',
  onDarkFill: 'rgba(255,255,255,0.17)', // the on-dark button
  onDarkFillPressed: 'rgba(255,255,255,0.26)',
  onDarkTag: 'rgba(255,255,255,0.14)',

  scrim: 'rgba(10,52,65,0.45)', // the night colour at 45%, not black

  /** A HOTTEST GROUPS CARD'S BAND (#800; home rows 3–5, 21): the paler diagonal stripes over the
   *  group's own `MONOGRAM_HUES` colour. White at 0,12 over the hue rather than a second hue per
   *  key — eight keys would need eight, and the band says *this group's colour*, not a ninth one.
   *  Nothing is written on a stripe: the tag sits on its own `ink` pill. */
  groupBandStripe: 'rgba(255,255,255,0.12)',

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

  /** A PLAYER'S PHOTOGRAPH — the ground nothing can know, and the second pin.
   *
   *  The court's ground is generated, so it is one of four composites. A photograph is not
   *  generated by anybody: it can be a white wall, a floodlit court at noon or a silhouette,
   *  and no fixed pair in docs/design-system.md 2.5 can state the ratio behind a label on it.
   *  The court's answer works here for the same reason it worked there — PIN THE SCRIM, and
   *  the unbounded set collapses to its WORST CASE, which for white text is the brightest
   *  ground there can be: pure white.
   *
   *  PINNED at .70. White over `night` at 70% on a pure-white photograph is 5.24 — AA with
   *  room — and every darker photograph, and every poster stop, is better by construction.
   *  Derived in textOnMedia.test.ts, which computes the bound rather than asserting it.
   *
   *  Lighter than the court's .93 on purpose: the court is a drawing whose ground carries no
   *  information, and a photograph is a person. The arithmetic FLOORS at .65 (4.51, a figure
   *  with nothing left in it) and the pin is the next step that has room — a ratio one
   *  rounding away from failing is one the next tuning of anything takes under. */
  photoScrim: 'rgba(10,52,65,0.70)',

  /** THE YES SCREEN'S GROUND — the app's ONE dark screen, and no other surface's
   *  ([ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
   *  §2, docs/design-system.md Part 16 2026-09-14). The design system stays paper-only and
   *  15.4's *there is no dark mode* stands: this is one ground and not a theme, drawn as a
   *  radial glow from the centre value out to the edge value with the SVG the poster already
   *  uses. The record calls them the prototype's dropped stage colours, knowingly readmitted —
   *  the design wins — and the next dark surface argues for its own record rather than reusing
   *  these two. Sign-in's hero draws them in its *It's a game!* (#787), a picture of this screen —
   *  ADR-0167's note of 2026-11-08, and nothing else. Not a `Soft`, not an `Ink`, not a `Line`:
   *  nothing writes on them but the one screen's own children, which are the on-dark tokens above.
   *
   *  MEASURED off the three mocks at 1x, and NOT the stage colours' bytes: the spec expected
   *  `#08222B` `#071C24` `#0B2B36` `#24505E` to the byte, and the rendered mocks do not hold
   *  them — the brightest ground pixel is `#1F3B47`–`#203C48` in all three and the darkest
   *  `#14252C`–`#15252D`, which is what is recorded, since a value is written for what was
   *  drawn (the author confirms against the mock's source at the look). Hue 198°, which is
   *  `night`'s family (194°) at a lower saturation. What sits on them, computed: `volt` 9,30 on
   *  the centre and 12,59 on the edge; white 11,66 / 15,78; white on `onDarkFill` over the
   *  centre 6,94 (the *Later* label); `onDarkTiny` over the centre 6,34 and the edge 7,98 (the
   *  line under the word while one payment is awaited, #630); `onDarkEyebrow` over the centre 4,41,
   *  which is under AA and is carried by a word — `vs` — that is decorative and never spoken.
   *  Derived in yesGround.test.ts. */
  yesGroundCentre: '#203C48',
  yesGroundEdge: '#14252C',

  /** THE DRAWN SPLASH'S GROUND — the app's second dark surface, beside *It's a game!*, and the
   *  splash's alone ([ADR-0209](../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md),
   *  docs/design-system.md Part 16 2026-11-23). The centre and the edge of the radial glow every
   *  cold open fades out of (`shared/lib/bootstrap/DrawnSplash.tsx`): centred horizontally and 42 %
   *  down, `splashGroundEdge` from three quarters of the way to the edges and beyond.
   *
   *  The product owner's brief to the byte, NOT `night` (`#0A3441`) and NOT the yes screen's pair:
   *  a second dark surface argues for its own record, as `yesGround*`'s note asks. **The edge is
   *  also the OS launch window's colour** (`app.config.ts`, the splash-screen plugin), so the
   *  window and the splash read as one field from the tap. Hue 191–192°, `night`'s family (194°).
   *  What sits on them is the lockup's (#855): white and `volt`, computed in
   *  `splashGround.test.ts`. Nothing else is drawn on them, and no other surface uses them. */
  splashGroundCentre: '#134652',
  splashGroundEdge: '#0B2B33',

  /** THE PORTRAIT TILE'S WASH — what was the deck card's, and the one card that wears a wash
   *  ([#801](https://github.com/Raketa02/Raketa/issues/801); home rows 17–19; docs/design-system.md
   *  7.31, Part 16 2026-11-14). The deck card it was fenced to (ADR-0169 §7, Part 16 2026-09-15) left
   *  with Classic play (#576), so the value moved here whole rather than standing twice: New in
   *  Raketa's tile — and Top 10's portrait after it (#805) — is a face edge to edge with a name, a
   *  Level and a line over its foot, which is the deck card's own problem.
   *
   *  One gradient over the lower part of the tile, from nothing to this: `ink` at .94, so the foot
   *  is the app's own text colour over whatever photograph or poster is under it, and the words sit
   *  on `surface` and the on-dark tokens as they would on a dark card. NOT `photoScrim`,
   *  deliberately: the panel's scrim is a flat tint pinned so that white over the worst photograph is
   *  computable (5,24 at .70), and a face wants the whole tile — so the wash RAMPS, and its worst case
   *  is stated at the name's own top edge rather than over the whole box (`PortraitTile.tsx` holds
   *  the ramp and the arithmetic). Nothing else may draw it. */
  portraitWash: 'rgba(16,27,32,0.94)',

  /** THE TOP 10 NUMERAL'S GRADIENT ([#805](https://github.com/Raketa02/Raketa/issues/805); home rows
   *  25–26; docs/design-system.md 7.36, Part 16 2026-11-15) — the huge place standing behind each
   *  card, filled from `numeralTop` at its figures' top to `numeralFoot` at its baseline, inside a
   *  paper outline: the screens' *night-to-teal*. MEASURED off home rows 25 at 1×, down the figure
   *  *2*: #29444F at its top and #15252C at its foot, hue 197–199° — `night`'s family, as every dark
   *  ground here is. It is a picture of a number, not text: the card it stands behind names the place
   *  (`topTenCardLabel`), so no contrast is claimed for it. The reader's own numeral is `volt`.
   *  Nothing else may draw these. */
  numeralTop: '#29444F',
  numeralFoot: '#15252C',

  /** THE RADAR'S GROUND — the app's THIRD dark surface, and a field rather than a card or a
   *  screen ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
   *  §7, docs/design-system.md Part 16 2026-09-16). One radial glow from the centre value out
   *  to the edge value, drawn with the SVG the yes ground already uses, under the Players
   *  header, the field, the zoom cluster and the footer of the Radar pane and nothing else;
   *  the deck pane beside it is paper. Argued for its own record, as ADR-0167 §2 said the next
   *  dark surface would be: a map of the night rather than a screen.
   *
   *  MEASURED off mock 1 at 1x, as the yes ground was: the brightest ground pixel around the
   *  viewer's tile is `#1B323D` and the darkest at the bottom edge `#111C22`. Hue 199°–201°,
   *  which is `night`'s family (194°) at the yes ground's saturation — the two grounds are
   *  neighbours by design and are NOT one token, because a value is written for what was
   *  drawn. What sits on them, computed: white 13,37 on the centre and 17,31 on the edge; `volt`
   *  10,67 / 13,81 (the you tile's ring and the chip); `onDarkTiny` over the centre 7,05 (the
   *  counter, the footer's hint, a level under a face); `onDarkEyebrow` over the centre 4,80 (a
   *  ring's label); `onDarkHair` over it 1,61, which is a hairline and not text. `coral` and
   *  `mint` are 3,43 and 3,28 on the centre and are NOT drawn on it as text: the card is paper
   *  and every sport dot and tag line sits on that. Derived in radarGround.test.ts. */
  radarGroundCentre: '#1B323D',
  radarGroundEdge: '#111C22',

  /** THE ZOOM CLUSTER'S BED — `ink` at .5 over the radar's ground, and the one dark-on-dark
   *  tile in the app. Mock 15 draws the three squares DARKER than the ground they sit on
   *  (`#15222A` against `#192D37`), where every on-dark tile so far is lighter (`onDarkTag`,
   *  `onDarkFill`); `ink` at .5 composites to `#16262E` on the centre value, which is the mock
   *  within a step. White on it is 15,48 — the `+`, `−` and ◉ are white — and against the ground
   *  it is 1,16, which is a shape read by its contents and not by its edge. Nothing else may
   *  draw it. Derived in radarGround.test.ts. */
  radarControl: 'rgba(16,27,32,0.5)',

  /** THE GAME CARD'S GROUND — the app's FOURTH dark surface: a group's Games deck card and a
   *  game's details (#553; the screens A2.3, docs/design-system.md Part 16 2026-09-30). One linear
   *  gradient down the card from the top value to the foot value, under the ribbon, the tiles, the
   *  forecast, the overlap grid and the court block, and nothing else. Argued for its own record, as
   *  ADR-0167 §2 said the next dark surface would be: a card a player answers with a swipe, drawn
   *  the colour of the night the other three are.
   *
   *  MEASURED off mocks 2–10 at 1x, as the other grounds were: `#1C333F` under the ribbon and
   *  `#101B22` at the foot, hue 199–205°, which is `night`'s family. What sits on them, computed
   *  half-way down: white 15,34; `volt` 12,24; `gameGreen` 3,32 (the forecast's figure, large);
   *  `gameAmber` 8,71; `gameRed` 3,39 (the figure, large). Derived in gameGround.test.ts. Nothing
   *  else may draw these — but for sign-in's miniature copy of the card (#786, `MiniGameCard`),
   *  which is a picture of this card and draws its ground, its ribbon and its inks with it. */
  gameGroundTop: '#1C333F',
  gameGroundFoot: '#101B22',

  /** The ribbon's band on a pick and a challenge — the mock's dark teal, measured. White 11,66 on
   *  it; the countdown under an hour is `gameCoral` on it, 4,74. A rescue's ribbon is `coralInk`,
   *  white 5,89 on it, where the mock's `#D34D2E` carries white at 4,31. */
  gameRibbon: '#203C48',

  /** THE CARD'S GREEN — measured off the mocks' IN tag, *Book it now* tag and forecast figure, all
   *  one value. Hue 155°: between `mint` (163°) and `mintInk`, and neither of them, because on this
   *  ground `mintInk` carries a figure at 2,67 and white on `mint` is 4,07. As a FILL under white,
   *  4,62 (the two tags, and the Fill in ribbon sign-in's miniature card draws, #786); as the
   *  forecast's figure on the ground, 3,32 — large text only. */
  gameGreen: '#308361',

  /** The overlap grid's two unlit shades: DARK — fewer than all but one free — and DIM — all but
   *  one free (the olive). BRIGHT is `volt`. Measured; the dim cell against the dark is 2,07, which
   *  is a shade read beside its neighbours and never the only signal: every cell is also spoken
   *  (`overlapLabel`). */
  gameCellDark: '#28363C',
  gameCellDim: '#546A36',

  /** The court block's two beds: GREY where a yes is a free vote (*Court available*, a dashed
   *  border) and the GREEN-GREY of a court a yes books or has booked (*Book it now*, *Booked*, a
   *  solid `voltStroke` border). Measured. Volt on them 10,93 and 10,03; white 12,57 on the green. */
  gameCourt: '#242F35',
  gameCourtBooked: '#28372A',

  /** WARN ON THE CARD — *Slim overlap*, *no free cancellation*, and the forecast's figure between
   *  55 and 70. Measured off the two words in mocks 3 and 6; `amber` itself is 2,73 on this ground. */
  gameAmber: '#DFC072',

  /** BAD ON THE CARD — the forecast's figure under 55. The mock's `#9E3C2B` is 2,32 on the ground,
   *  under even large text's 3:1, so its hue is kept and ONLY the lightness is raised, to 3,44
   *  (`arranging`'s rule: measured, then lifted); 3,39 half-way down the gradient. */
  gameRed: '#C84F3A',

  /** THE COUNTDOWN UNDER AN HOUR — coral's hue (9°), lifted to carry *45 min* on the ribbon at
   *  4,74, where `coral` there is 2,99. A mark would take `coral`; these are words. */
  gameCoral: '#F08975',

  /** THE SOCIAL VIBE'S TWO LOWER BANDS ON THE CARD (#838; ADR-0207 §8–§9, docs/design-system.md
   *  7.38, Part 16 2026-11-22). The vibe's four bands are one hue family and never the forecast's
   *  green / amber / red: *Great* and *Good vibe* are `volt`, *Some common ground* this dimmed volt,
   *  *Fresh mix* this grey — each the bar's fill and the figure's colour at once, as `volt` is. No
   *  mock draws them: they are DERIVED. The dimmed volt is `volt` at 0,6 over the card's ground
   *  half-way down, 4,6° off volt's hue; the grey is `night`'s family (198°) at a luminance a
   *  shade under the dimmed volt's, so *Fresh mix* never reads brighter than *Some common ground*. What they carry,
   *  computed half-way down: the figure 5,31 and 5,05 (past AA, where `gameGreen` is large text
   *  only); `ink` — *Social vibe* inside the fill — 6,06 and 5,77 on them; against the track
   *  (`onDarkTag` over the ground) 3,43 and 3,26, a mark's 3:1. Derived in gameGround.test.ts. The
   *  paper card's inks are #840's, below. Drawn by `SocialVibeRow` on the game card's ground — and,
   *  as the band's FILL alone, by `SocialVibeCard`'s bar on paper (ADR-0207 §8: one fill per band,
   *  whatever the ground), where they stand 2,47 and 2,60 off its `line2` track and volt 1,07: a
   *  shade beside the track, never the only signal, since the % and its word are printed above. */
  gameVoltDim: '#8BA140',
  gameGrey: '#8A969B',

  /** THE SOCIAL VIBE CARD'S PAPER PAINT (#840; ADR-0207 §8–§9, docs/design-system.md 7.39,
   *  Part 16 2026-11-23) — the card a For-fun game's details open on, on `surface`. ADR-0207 §9's
   *  named exceptions, drawn by `SocialVibeCard` — and the three figure inks by a For-fun fit's %
   *  on Post a game's sheet, also on `surface` (#842, `SOCIAL_VIBE_CARD_FIGURE`), nowhere else.
   *
   *  `voltPale` — A SHARED ROW'S BAND, MEASURED off for fun 7 to the pixel. Against 1.2's *volt has
   *  no soft and needs none*: the mock's grid reads across a pale volt band, so the band is one,
   *  and it stays a bed for words and marks only — `ink` 16,82 on it, `oliveInk` dots 5,78.
   *
   *  `oliveInk` — THE OLIVE ON PAPER: the grid's dots and the big % in the two upper bands. It IS
   *  `gameCellDim`'s value, as ADR-0207 §9.2 names it — the overlap grid's olive, now an ink on
   *  paper (6,01 on `surface`); `socialVibeInks.test.ts` holds the two equal. The mock's own olive
   *  is a shade off (#5E7010), and the ADR's word stands.
   *
   *  `oliveInkDim` — *Some common ground*'s %: olive's hue lifted to a lighter step that still
   *  carries the figure past AA (4,91). DERIVED, since no mock draws the band.
   *
   *  `vibeGrey` — A ROW ONLY YOU HAVE, and *Fresh mix*'s %: the mock's row grey (#7C8B8D, 3,54 — not
   *  a text colour) at its own hue, darkened to the first step past AA (4,58), `muted`'s own history.
   *  A shade lighter than `oliveInkDim`, so *Fresh mix* never reads stronger than *Some common
   *  ground*, as `gameGrey` sits under `gameVoltDim` on dark. The row's dot is `line`, the mock's
   *  value to within a unit. Derived in socialVibeInks.test.ts. */
  voltPale: '#F9FDE2',
  oliveInk: '#546A36',
  oliveInkDim: '#617843',
  vibeGrey: '#6A787A',

  /** THE POSTING GRID'S TWO MIDDLE GREENS (#558; the Games & Fill in screens A5.2, A10;
   *  docs/design-system.md 7.28, Part 16 2026-10-02). The grid's ramp runs `paper2` (nobody who
   *  fits) → `mintSoft` (a few, no court) → `gridLight` (a full game's worth, no court) →
   *  `gridMid` (a court, fewer than a full game) → `mintInk` (a court and a full game, ringed in
   *  volt): brighter is more worth picking. The spec names the two middle values, and they are
   *  its own bytes; the ends are tokens the palette already had.
   *
   *  EACH WITH ITS INK, and no soft and no line: 15.2 asks for a soft where a colour has a pale bed
   *  and a line where that bed is bordered, and a cell IS the fill — the ramp's pale stage is
   *  `mintSoft` itself — so a soft would be a token nothing references (Part 14 #1). The number
   *  and the court glyph on each are its ink, never white: the mocks draw white, and white is
   *  1,51 on `gridLight` and 2,15 on `gridMid`, a figure nobody can read. Each ink is the green's
   *  own hue (152°, 156°) darkened to the first step that carries a figure: 4,65 and 4,68. As
   *  fills on paper they are 1,35 and 1,92 — a shade read beside its neighbours and never the only
   *  signal, `gameCellDim`'s rule: every cell carries its number and a glyph, and is spoken.
   *  Derived in postingGrid.test.ts. Nothing else may draw these. */
  gridLight: '#A9DEC5',
  gridLightInk: '#266447',
  gridMid: '#5EC39B',
  gridMidInk: '#1C4A38',

  /** THE STAGE'S GROUND — the dark hero over sign-in (and, from #785, sign-up), and the app's
   *  FIFTH dark surface: a hero over a screen's top four tenths, behind the paper sheet that holds
   *  the form ([#784](https://github.com/Raketa02/Raketa/issues/784); the design system's 12.2,
   *  Part 16 2026-11-08). Argued for its own record, as ADR-0167 §2 said the next dark surface
   *  would be: the first thing a person sees, drawn the colour of the night the yes screen is.
   *
   *  MEASURED off mocks 1–3 at 1x: the hero is ONE flat value, `#15252C`, from the status bar to
   *  the sheet's edge — not a radial — which is `yesGroundEdge` one step off in red, and is NOT
   *  that token, for the reason each ground before it gave: a value is written for what was
   *  drawn, and the yes ground is that screen's alone. Hue 198°, `night`'s family. What sits on
   *  it, computed: white 15,76 (the wordmark and the headline); `volt` 12,57 (the wordmark's dot,
   *  a mark). Derived in stageGround.test.ts. Nothing else may draw it. */
  stageGround: '#15252C',

  /** THE SAME LEVEL CARD'S GROUND — Home's *Same competitive level players* card, the app's SIXTH
   *  dark surface ([#802](https://github.com/Raketa02/Raketa/issues/802); the Home rows screens §4.2;
   *  design-system 7.34, Part 16 2026-11-14). A card whose one figure is a forecast, drawn in the
   *  game cards' three inks (`gameGreen`, `gameAmber`, `gameRed` — the ticket's *existing forecast
   *  tokens*), which `night` cannot carry: `gameGreen` on it is 2,88, under large text's 3:1.
   *
   *  MEASURED off home rows 7, 8, 10.3 and 15 at 1x: one flat `#15252C` at every corner — the stage's
   *  value, and NOT that token, for the reason each ground before it gave: a value is written for what
   *  was drawn, and the stage is sign-in's alone. Hue 198°, `night`'s family. What sits on it,
   *  computed: white 15,76 (You, the nickname, the mark); `volt` 12,57 (the fill, *2 sports*);
   *  `gameGreen` 3,41, `gameAmber` 8,94, `gameRed` 3,48 (the figure, large only); `onDarkTiny` over it
   *  7,97 (the levels, the gap, the sport, the bands). Derived in levelCardGround.test.ts. Nothing
   *  else may draw it. */
  levelCardGround: '#15252C',

  /** THE STAGE'S FOOT GLOW — a flat ellipse of light where the sheet meets the hero, brightest at
   *  the sheet's edge under the middle of the screen and gone a tenth of the hero above it.
   *  MEASURED off mock 1 three pixels above the sheet; hue 160°, a green the ground falls into
   *  rather than a second dark. White on it 12,95 — the headline's last line sits just above its
   *  reach. Derived in stageGround.test.ts; `StageGround.tsx` holds the shape. */
  stageGlow: '#23352F',

  /** THE PODIUM'S STEP ON THE STAGE — sign-up's hero (#788): the second and third steps, white
   *  over the ground at a seventh. MEASURED off mock 5 at 1x: #36444A over `stageGround`'s
   *  #15252C, which is white at 0,14 in each channel. The value `onDarkTag` holds and NOT that
   *  token: a step is not a tag, and a value is written for what was drawn. What sits on it, over
   *  the ground: white 10,15 (the step's number). Derived in stageGround.test.ts. Nothing off
   *  the stage may draw it. */
  stageStep: 'rgba(255,255,255,0.14)',

  /** THE RIM ROUND A FACE ON THE STAGE — the translucent edge round the two other players'
   *  tiles on sign-up's podium (#788), where You's is a volt ring. MEASURED off mock 5: #505C61
   *  over the ground, white at 0,25. A rim and never text: 2,27 against the ground, a line drawn
   *  to separate a poster's edge from the night rather than to be read (1.4.11 asks 3:1 of a
   *  mark that carries meaning, and this carries none). Derived in stageGround.test.ts. */
  stageRim: 'rgba(255,255,255,0.25)',
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

// ---------------------------------------------------------------------------
// The group monogram's hues — a second closed set, and for the poster's reason NOT in `color`
// ---------------------------------------------------------------------------

/**
 * THE EIGHT FILLS A GROUP'S MONOGRAM CAN BE — one per colour key the backend serves, 0 to 7
 * ([ADR-0183](../../../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)
 * §5, docs/design-system.md 7.20). The key is fixed for a group for ever — derived from its id —
 * and **the backend never names a colour**: this list is the one place a key becomes a hue, so
 * every screen that draws a group's tile draws the same one.
 *
 * Exported beside the theme and never inside it, as `POSTER_HUES` is: a monogram's hue is picked
 * by a hash of a group's id, so it means nothing, and a `theme.color.monogram…` would be a value
 * that means nothing sitting where every other one means something. `GroupMonogram` is the only
 * component that reads it.
 *
 * MEASURED where the mocks draw one — play 1's *Oo* `#308361` and *Kc* `#87641A`, play 9's *O3*
 * `#213E50`, play 40's *Mr* `#9E3C2B` — and four more chosen to sit between them on the wheel.
 * **White letters on every one clear 4.5:1**, the floor for the tile's letters, which are text;
 * the green is the tightest at 4,62. Derived in `monogramHues.test.ts`, which computes the ratio
 * rather than asserting it. Unlike the poster, a monogram DOES sit near the sport hues: the mocks
 * draw it so, and the tile always carries the group's name beside it, which is what tells a group
 * from a sport.
 */
export const MONOGRAM_HUES = [
  '#308361',
  '#87641A',
  '#213E50',
  '#9E3C2B',
  '#6A4C93',
  '#1E6B73',
  '#8C3F6E',
  '#3D5A99',
] as const;

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
  /** `h1` is the largest sans role a SURFACE reaches for. `display` (26 / 700) was added on
   *  2026-09-08 for one thing — the Now card's figure slot holding a weekday — and retired with
   *  that slot on 2026-09-12 (#413): the day is an `h2` row now. A token nothing references is a
   *  lie about the system (docs/design-system.md Part 14 #1), and the next sans word above 19 is
   *  a decision to make again rather than a role to reach for — which is what `yesWord` below is:
   *  a decision made for one word, with one use, and not `display` back under a new name. */
  h1: { fontFamily: font.sans[700], fontSize: 19, letterSpacing: -0.57, lineHeight: 24 },
  /** THE YES SCREEN'S ONE WORD — *Challenge!*, *Matched!* — and nothing else's
   *  ([ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
   *  §2). The heaviest weight the app loads, and a size measured off the mocks rather than taken
   *  from the record's *about 30*: `Challenge!` is 164–168pt wide with a 25–27pt cap in the two
   *  challenge mocks and `Matched!` 145 x 24 in the third, and Archivo 800 at 32 sets the first
   *  at 169 and the second at 147 — the width is matched, and the mock's face has a taller cap
   *  than Archivo's. Tracking continues the sans ramp past `display`'s -0.035em: -0.040em at 32
   *  is -1,28. Line height 36, on 3.3's own reasoning for a sans word with ascenders.
   *  ONE USE. A second surface that wants a word this size reopens ADR-0167 §2 rather than
   *  reaching for this role, which is the whole of why it is named for the screen. Sign-in's hero
   *  draws a picture of this screen (#787) and says its word in it: ADR-0167's note of 2026-11-08
   *  — the same word on a picture of the same screen, and not a second use. */
  yesWord: { fontFamily: font.sans[800], fontSize: 32, letterSpacing: -1.28, lineHeight: 36 },
  /** THE DECK CARD'S NAME — one ~24pt sans role, heavy, one use
   *  ([ADR-0169](../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
   *  §7). NOT the retired `display` back: 3.3's reasoning applies again and this is the word it
   *  applies to — a face you decide about wants the name at the size the mocks draw it, 24 / 700
   *  measured across the nine, with the sans ramp's -0.035em (-0,84) and a 28 line for the
   *  ascenders. `surface` over the wash, with the on-media shadow. A second surface that wants a
   *  name this size reopens ADR-0169 §7 rather than reaching for this role. */
  deckName: { fontFamily: font.sans[700], fontSize: 24, letterSpacing: -0.84, lineHeight: 28 },
  /** THE TOP 10 NUMERAL — 1 to 10, huge, tucked behind each card of Home's Top 10
   *  ([#805](https://github.com/Raketa02/Raketa/issues/805); home rows 25–26; 7.36, Part 16
   *  2026-11-15). Archivo at its heaviest loaded weight, whose figures stand 0,699 em over the
   *  baseline: at 108 that is 75pt, where home rows 25 and 26 MEASURE 70–79 at 1× beside a 154pt
   *  card. Tracked −16 (−0,15 em) so *10*'s two figures touch, the *0* over the *1*'s foot, as home
   *  rows 25.3 draws them. Drawn as SVG text — no line box — so it carries no `lineHeight`. ONE USE:
   *  a second surface that wants a figure this size reopens the Top 10 row in Part 16. */
  numeral: { fontFamily: font.sans[800], fontSize: 108, letterSpacing: -16 },
  /** THE SPLASH'S WORDMARK — *Rakieta*, white, over the drawn splash's ground, and nothing else's
   *  ([ADR-0209](../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)
   *  §5; [#855](https://github.com/Raketa02/Raketa/issues/855); 3.3, Part 16 2026-11-23). The
   *  product owner's brief to the point: Archivo at its heaviest loaded weight, 42, tracked −4 %
   *  (−1,68). A fixed size on every phone that ignores the OS text size, because a logo is a logo.
   *  **Not a text role**: its seven letters are placed one by one from Archivo 800's own advances
   *  and kerning (`shared/lib/bootstrap/domain/splashGeometry.ts`, pinned against the font by
   *  `splashWordmark.test.ts`), so the TRACKING IS THE GEOMETRY'S to apply between letters and is
   *  never set on a letter's text, and it has no `lineHeight`: each letter stands in the face's own
   *  line box, whose midline is the screen's. ONE USE: a second surface that wants a word this size
   *  reopens the splash's row in Part 16. */
  splashWord: { fontFamily: font.sans[800], fontSize: 42, letterSpacing: -1.68 },
  /** THE DECK'S TWO STAMPS — *LET'S PLAY* and *NOT TODAY*, outlined words rotated over the card
   *  under the thumb, invisible at rest (ADR-0169 §3, §7). The heaviest weight the app loads at
   *  22, TRACKED WIDE rather than tight — +0,05em, 1,1 — because a rubber stamp is set spaced
   *  and the mocks draw it so; uppercased by the stamp's style, never by the copy, which is the
   *  two buttons' own words. The outline, the tilt and the corner are the drawing's own
   *  (`DeckStage.tsx`). Feedback and never a control: nothing announces it. ONE USE. */
  deckStamp: { fontFamily: font.sans[800], fontSize: 22, letterSpacing: 1.1, lineHeight: 26 },
  /** THE STAGE'S TWO LARGE WORDS — the hero's headline in white and the sheet's title in `ink`,
   *  on sign-in and sign-up and nowhere else ([#784](https://github.com/Raketa02/Raketa/issues/784);
   *  12.2, Part 16 2026-11-08). MEASURED off mocks 2 and 3, and the two are one size there: the
   *  headline's first line is 256pt wide and *Sign in* 69pt, which Archivo 700 at 22 with the sans
   *  ramp's −0,035em (−0,77) sets at 259 and 65. Line 26, `deckStamp`'s at the same size. Not
   *  `deckName` at a second size and not `display` back: a decision made for the stage's two words,
   *  and a third surface that wants a word this size reopens the stage's row in Part 16. */
  stageTitle: { fontFamily: font.sans[700], fontSize: 22, letterSpacing: -0.77, lineHeight: 26 },
  /** THE STAGE'S BOX VALUE — what is typed into the sign-in stage's boxes, and their placeholder
   *  (#784; 6.13 as amended, Part 16 2026-11-08). MEASURED off mock 3: *tomek.k@gmail.com* is 129pt
   *  wide, which Archivo 400 at 14 sets at 129,1. Line 20, `tiny`'s 1,45 at 14. Every other box keeps
   *  `rlValue`; a second surface that wants this size reopens the stage's field row in Part 16. */
  stageValue: { fontFamily: font.sans[400], fontSize: 14, lineHeight: 20 },
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
  /** The segmented control's label — 6.3's own `10.5 / 700`, tokenised by the first screen
   *  that needed one. It is `chip`'s size at `flab`'s weight and neither's tracking: a
   *  segment names a VIEW rather than a filter, so it is not a chip, and it is not uppercase,
   *  so it is not a form label. 6.3 was specified and unbuilt, and this is the value it
   *  states — a new role rather than a new decision. */
  seg: { fontFamily: font.sans[700], fontSize: 10.5 },
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
  /** THE RADAR'S SMALL MONO — a ring's label, a level under a face, the counter between ± and
   *  the card's distance ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
   *  §7, docs/design-system.md Part 16 2026-09-16). `tiny`'s 11 / 16 box in the mono family at
   *  the inline weight, with the ramp's −0,035em (−0,385): the mocks set every one of those four
   *  figures at the size the sans secondary text is, and `xs` at 13 is a step too large for a
   *  label on a hairline. A size and not a scale of `xs`, for 15.3's reason — the pair changes
   *  together with the record. */
  tiny: { fontFamily: font.mono[500], fontSize: 11, letterSpacing: -0.385, lineHeight: 16 },
  /** A LEVEL IN A TAG — *Pad 2,44* under a Join request's name (#529, Part 16 2026-09-30).
   *  `type.tag`'s 9,5 / 12 box and weight in the mono family, with the ramp's −0,035em (−0,33):
   *  a figure is mono, and `tiny` at 11 puts two tags and a *+2* past the room a request row
   *  leaves beside ✕ and Approve on a 393pt phone. */
  tag: { fontFamily: font.mono[600], fontSize: 9.5, letterSpacing: -0.33, lineHeight: 12 },
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
  /** The tab's menu (9.5, #861) — the popover's 13, named for its role: an anchored card that picks
   *  rather than explains, and changing one must not change the other. */
  tabMenu: 13,
  bubble: 13,
  toast: 12,
  /** The tab bar's dock (10.2, #883) — 22 on all four corners, beside the sheet's 22 on its top
   *  two: the dock is the bottom chrome's other floating slab, and the brief's own corner. Its inner
   *  rim is this less the 1pt hairline, which is arithmetic the bar does rather than a second
   *  token. It took the retired ⚡Play disc's `fab` (11), which only the bar drew. */
  dock: 22,
  /** The guide's hole (9.4) — the window cut in its dim around one figure. A button's 10, named
   *  for its role: a hole is not a control, and changing one must not change the other. */
  spotlight: 10,
  btn: 10,
  note: 10,
  daySquare: 10,
  seg: 10,
  segThumb: 8,
  /** The week grid's cell. A fresh token beside the dead `daySquare`: the slot squares of the
   *  deleted 6.7 are NOT being restored, and a cell that borrowed their radius would be the
   *  first step back toward a booking grid. 6 on a 20pt hour cell — mock 36's corner, which
   *  at 10 would round the cell into a pill. */
  availabilityCell: 6,
  /** A posting grid cell (7.28, #558) — the mocks' rounded square, `daySquare`'s 10. */
  postingCell: 10,
  /** The door row's lead square. Between `btn` and `segThumb`: a 28pt square at 10 reads as a
   *  small button, which it is not — the row is the control and the square is its glyph's
   *  ground — and at 8 reads as a chip's thumb. Named for the object, as `availabilityCell` is. */
  rowLead: 9,
  /** **There is no avatar rule in this system, and this is not one.** The formula that
   *  derived a face's corner from its box — `round(size x 0.33)` — went with 7.4's seat
   *  avatar in the 2026-08-25 reset, and #338 refused to bring an avatar back: no Avatar
   *  element, no avatar hue, no avatar radius rule, and `POSTER_HUES` stays `CourtPoster`'s
   *  closed set unwidened. A face in a box is `CandidatePhoto`, which owns its 33 % share of
   *  its OWN width one folder over, and a row's face is a photograph or a poster.
   *  What is left here is a VALUE nothing draws — 4.2 keeps it named, because `court` below
   *  is named for its role rather than borrowing this one and that argument needs its foil. */
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
  /** The Social vibe row's bar — 7.38 (#838). MEASURED: mock 1's corner turns over 4–5 pixels of a
   *  21-pixel bar, mock 2's over 6–7 of 28, so 4 at 18. A soft corner, not the balance bar's near
   *  pill: the mocks draw a filled gauge, and its fill's square end is the value. */
  socialVibe: 4,
  fit: 7,
  /** The record block's run-of-form square — 7.13. Eight points wants a soft corner, not a
   *  rounded one: five of these in a row are a *run*, and at `tag`'s 6 they read as five
   *  separate pills. A fresh token rather than `bar`'s 2 borrowed, because a square that
   *  states an outcome is not a track. */
  recordSquare: 2,
  tag: 6,
  dot: 6,
  meter: 3,
  bubbleTail: 3,
  bar: 2,
  /** The chip is the only true pill. Compute as height / 2. */
  pill: 999,
} as const;

// ---------------------------------------------------------------------------
// Component metrics
// ---------------------------------------------------------------------------

/** The smallest round mark in the app — the sport dot's, and the typing indicator's. One size. */
const SPORT_DOT = 6;

/** How far a finger travels across before a swipe row — and the deck — claims the touch. See `swipeRow`. */
const SWIPE_INTENT = 12;

/**
 * An italic's slant, in degrees, where the app draws one — no italic face is loaded, so a word or a
 * mark that the mocks set in italics leans by a skew instead. One angle, so two italics never
 * disagree: Top 10's mark and count (`topTen.lean`) and the Social vibe's name (`socialVibe.lean`).
 */
const ITALIC_LEAN = -12;

const size = {
  btn: 34, // 32 tertiary-in-card · 34 default · 40 screen action · 42 result primary
  btnSm: 32,
  btnLg: 40,
  btnXl: 42,
  chip: 27,
  chipSm: 25,
  seg: 25,
  /** **A door segment's label** (6.3 as amended 2026-11-05, ADR-0201 §2) — the Games switch's kind
   *  the intent doesn't want: `muted` at .8, `#7A878A` over the `line2` track, **3,17:1**. Slightly
   *  dimmed and no further: past 3:1 still, where every step down reads as *disabled*, which is the
   *  one reading the door must not have. Under 1.4.3's 4,5:1, and recorded so: the state is said
   *  in words too — the door carries no number — and the label is the kind's name, which the live
   *  segment beside it prints whole. */
  segDoorOpacity: 0.8,
  /** **An option that owns a menu** (6.3 as amended 2026-11-24, #861; PRD #859): the group page's
   *  Friends tab, and Games' since #862. Selected, with its menu offered, it draws a Feather chevron
   *  `chevron` across, `inset` in from its right edge and `gap` clear of the label — and **widens by
   *  exactly that room**, `gap + chevron + inset` (21): its flex basis is the room where every other
   *  option's is nought, so the label keeps the same share of the track as every other tab's and the
   *  chevron is added beside it. Measured with Archivo against the four labels: at 320pt the shares
   *  are 63,5 against *You’re in*'s 44,3 (`groupTabsFit.test.ts`). 12 is a step under the tab
   *  bar's 16 icon — the label here is 10,5 where the bar's is 12 — and on the 3pt grid. */
  segMenu: { chevron: 12, gap: space.xxs, inset: space.xs },
  /** A segment's count — the tab bar's badge (`tabBar.badge`) at the segment's size (#529),
   *  `CornerBadge`: a group page's Games, Fill in and You’re in (#847) — on Fill in and You’re in
   *  what is new since the player last looked, never on the tab shown (#849) — and the group's
   *  tile on its page and on Info, counting the requests waiting on an Owner (Q125). **16, and it is
   *  `num.tiny`'s own line box**, the digit role one step under the tab bar's `num.xs` — the
   *  segment's label is 10,5 where the tab bar's is 12, so the mark comes down with it rather
   *  than standing a size above the word it sits on. The fill, the white digit, the pill and the
   *  missing cap are the tab bar badge's; only the size is the segment's. */
  segmentBadge: 16,
  /** **The tab's menu** (9.5, #861; PRD #859; tab menu mocks 3, 4 as illustrations) — a white card
   *  hanging `hang` under the tab that opens it, as wide as its lines. A line is at least `minTouch`
   *  tall (6.5), padded `padX` across, with `gap` between its marks; the card is padded `padY` above
   *  and below its lines. **The selected mark is a `tick`-across `coralInk` circle** with
   *  `Tick`'s drawn white tick in it (Archivo has no ✓) — 18 holds the 12 tick with 3 clear on every
   *  side — and the line not selected keeps that space empty, so the words line up. `drop` is how
   *  far it falls into place as it opens (`motion.tabMenu`). */
  tabMenu: {
    hang: space.xs,
    padX: space.md,
    padY: space.xxs,
    gap: space.sm,
    tick: 18,
    drop: space.xs,
  },
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
  /** The 3pt bar that carries a semantic — 5.4's note, and 5.4 as amended, the challenge
   *  row's urgency stripe. One number because there are now two drawings of it: the note
   *  wears it as a `borderLeftWidth` on a card, the row draws it as a full-height View
   *  beside its content and never becomes a Note. Two implementations of a 3 is exactly
   *  what a token is for. */
  semanticBar: 3,
  /** The run-of-form square — 7.13. Five of them plus four `space.xxs` gaps is 52pt, which
   *  fits the narrowest phone's third of a card with the block's label above it. It is a mark
   *  rather than a target: nothing in the record block is pressable, so 6.5's 44pt does not
   *  apply and there is no `hit` entry beside it. */
  recordSquare: 8,
  /** The confidence ring — a drawn object, dark card only. Stroke matches the level
   *  bar's band segments; the tick crosses the stroke and overshoots it outward.
   *  Geometry and reasoning: docs/design-system.md 7.8. The 30% ceiling the tick marks
   *  is a domain constant, NOT a design value — it does not belong here. */
  ring: 72,
  /** The ring's two other homes, both still inside a dark card (Part 16, 2026-09-17 — ADR-0179
   *  §1, §2): the You tab's header card draws the Player Score at 56, and the reliability
   *  screen draws it at 74 beside the band's word. Diameters only — the stroke, the tick
   *  and the overshoot are the one ring's, whichever size it is drawn at. */
  ringSm: 56,
  ringLg: 74,
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
  /** The week grid — 6.8. Seven days ACROSS and sixteen hours DOWN, as mock 36 draws it:
   *  16 rows at the 44pt minimum would be 704pt of grid, taller than any page, so the cell is
   *  20pt tall and a seventh of the width, the whole week fits a phone, and a press and drag
   *  paints a run instead of each hour being hit alone. `hit.availabilityCell` grants each
   *  cell half the gap on every side — the neighbour rule's most — so no point between two
   *  cells presses nothing. 6.5 records the departure from the minimum.
   *
   *  `paintIntent` is how far a finger travels on the cells before the touch is a paint rather
   *  than a tap. Below the scroll view's own slop, so a drag down a column is claimed by the
   *  grid before the page can take it as a scroll; and a tap that drifts that far paints only
   *  the cell it is on, which is the same as tapping it.
   *
   *  `labelMaxRatio` caps the hour-label column so Dynamic Type grows the labels without
   *  starving the cells. `footnoteMinHeight` is two lines of `type.rlLabel`, always laid out,
   *  so ticking the first hour never moves the grid out from under the finger; the hairline
   *  above it is drawn only when there are words to separate. `tick` and `tickStroke` are the
   *  12 x 12 mark family's box — the plus a search adds and the diff's plus and dash — which
   *  the tick box reads from here too. */
  availability: {
    cellHeight: 20,
    columns: 7, // the seven days, across
    gap: 4,
    paintIntent: 4,
    labelGutter: 9,
    labelMaxRatio: 0.25,
    cardPadding: space.md,
    tick: 12,
    tickStroke: 2,
    footnoteMinHeight: 2 * type.rlLabel.lineHeight,
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
   *  control to 44 without a `hit` entry, the way the radius slider's row does. A 22pt
   *  square with slop around it would be a target that stops at the words.
   *
   *  `box` is the mocks' rounded square (#785): 47 pixels across in mock 6 at 2,1 to the point,
   *  so 22, where it was 20; the corner stays the cell's 6, which mock 6 draws too (12 pixels).
   *  `picker` is the friends picker's circle, 6.11's box made round (#757) — kept at the 20 it was
   *  drawn at, because #785 changed sign-up's box and *Start playing*'s, not the picker's. Named for
   *  the object, as `availabilityCell` is. */
  tickBox: {
    box: 22,
    picker: 20,
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
  /** The Social vibe row — 7.38 (#838; ADR-0207 §9.4, for fun 1–2). MEASURED off the two mocks,
   *  with the figure at `num.xl` as the unit: in mock 1 its digits stand 18 pixels and the bar 21,
   *  which at `num.xl`'s 15,4pt figures is 18 — the forecast bar's `md`, so the card's rows stand
   *  where they stood. `inset` is where *Social vibe* starts inside the bar: 14 pixels of mock 2's
   *  28-pixel bar, so 9 (`space.sm`). `lean` is the slant the name takes as an italic would — no
   *  italic Archivo is loaded, so it is drawn, as Top 10's mark and count lean, at the one angle the
   *  app draws an italic at (`ITALIC_LEAN`). */
  socialVibe: { bar: 18, inset: space.sm, lean: ITALIC_LEAN },
  /** The Social vibe card — 7.39 (#840; ADR-0207 §6, for fun 7, which leads over 5 and 6).
   *  MEASURED off mock 7 and checked against mock 5, whose phone gives the scale (the card is the
   *  content width, 449 pixels for 360): the bar 21 (33 and 28 pixels), a face 24 (39 and 33), a
   *  column 36 (54 and 45 pixels apart), a row 24 (39) and a dot 12 (18). The bar is the card's
   *  own, thicker than the row's 18 because the % above it is bigger. */
  socialVibeCard: { bar: 21, face: 24, column: 36, row: 24, dot: 12 },
  /** The switch — 6.12. The track and the knob are UI §G1's measured 40 x 23 and 18, and the
   *  inset is the arithmetic between them rather than a fourth number. The ROW is the touch
   *  surface, exactly as 6.11's is: a 23pt track is well under the 44pt minimum, and a
   *  `hitSlop` around it would leave the words beside it inert. */
  switch: { track: 40, height: 23, knob: 18, row: 44 },
  /** THE GROUP'S MONOGRAM — its tile at the three places a group is drawn (7.20, #512), MEASURED
   *  off the mocks at 1×: 38 on a Groups list card (play 1, 38), 28 in a row inside a club's
   *  card (play 9, 24, 35) and 36 in the group page's header (play 39, 40).
   *
   *  `radius` and `letters` are SHARES of the tile's side, for `yesTile.initials`' reason: one
   *  drawn object at three sizes, and a point value per size is three numbers to keep in step.
   *  A 38 tile's corner is 10 and its letters 14; a 28 tile's are 8 and 10. The letters are the
   *  one font size in the app after the yes tile's that is computed from a box, and it is computed
   *  inside the tile that owns the box — the group's, and since #518 a club's (`ClubTile`), which
   *  is the same drawing at the same two sizes. `chip` is the profile switcher's face (#518, as
   *  slimmed 2026-10-01): the worn profile drawn small enough that the pill reads as a control
   *  rather than as a second avatar beside the header's. */
  monogram: {
    card: 38,
    row: 28,
    header: 36,
    chip: 22,
    /** A Hottest groups card's shield, overlapping its band (#800, home rows 3), and the group
     *  sheet's rounded badge (home rows 6) — the same tile at two more sizes, read off the mocks. */
    shield: 45,
    sheet: 48,
    radius: 0.27,
    letters: 0.37,
  },
  /** HOME'S HOTTEST GROUPS CARD ([#800](https://github.com/Raketa02/Raketa/issues/800); the Home
   *  rows screens §3.2; home rows 3–5, 21), read off the mocks at 1× and put on the 3pt grid:
   *
   *  - `band` — the striped band across the top, and `stripe` each stripe's width across, the gap
   *    between two the same;
   *  - `shieldTop` — how far below the card's top the shield (`monogram.shield`) starts, so it
   *    overlaps the band and the body; `shieldRing` its white ring, and `shieldFoot` the share of
   *    its side that rounds its two lower corners — a shield's, where a tile rounds all four;
   *  - `tagMark` — the drawn ▲ in the HOTTEST pill. The heat bar's `heatBar` (6) retired with the
   *    bar (#821). */
  hottest: {
    band: 39,
    stripe: 9,
    shieldTop: 15,
    shieldRing: 3,
    shieldFoot: 0.4,
    tagMark: 6,
  },
  /** THE PROFILE SWITCHER'S CHIP (club 7, #518; slimmed 2026-10-01) — a face at `monogram.chip`
   *  (22) beside a drawn ⇅, in PROPORTION to the product owner's mock rather than at its pixels: the
   *  face about three quarters of the pill's height, the arrows about two fifths of the face's. So
   *  the two arrows sit in a 14pt box (their strokes span 8,75 of it), drawn as geometry because
   *  Feather ships no up-and-down pair and Archivo is never asked for a mark. `markStroke` is the
   *  mock's hairline arrow, a step under the tick's 2pt because the arrows are two strokes side by
   *  side and at 2 they close into a block. */
  switcher: { mark: 14, markStroke: 1.5 },
  /** THE GROUP PAGE'S TWO DRAWN PIECES (#513), MEASURED off the mocks at 1×. `seat` is a face or
   *  an empty seat in the Games card's row under its headline — 34 in play 14–17 and 39, the
   *  radar card's identity face and a `btn` high. It is `PlayerPhoto`'s `face` box at that size,
   *  so its corner is the face's third and no second radius exists. `filterPad` is the white
   *  bar's inset around the sport pills it unfolds into (play 42): the pills are chips, and
   *  `chip` + 2 × 9 is 45 — so the bar is a reachable target tall and each pill's `hit.chip`
   *  ends at the bar's edge rather than past it, where Android would never deliver the touch.
   *
   *  Info's members row (#514, play 58–60) stacks up to five faces: `stackFace` is each
   *  one, 28 — the monogram's row size, and what the mocks draw beside the row's `cardTitle` —
   *  `stackOverlap` how far each slides under the one before it, about a third, and `stackRing`
   *  the card-coloured ring that keeps one face from merging into the next. */
  groupPage: { seat: 34, filterPad: 9, stackFace: 28, stackOverlap: 9, stackRing: 2 },
  /** RANKINGS ([#775](https://github.com/Raketa02/Raketa/issues/775); the rankings screens §1, §4,
   *  §5; Part 16, 2026-11-08). Read off rankings 1, 4 and 6 at 1x and put on the 3pt grid:
   *
   *  - `trophyPill` — Home's dark pill left of the bell, and `trophy` the drawn cup inside it at the
   *    tab icon's weight. Its reachable height is `hit.trophy`'s.
   *  - `place` — the rows' place column: *212* in `num.s` with room, so paging (#776) never reflows it.
   *  - the podium: the first's face a step larger than the others', and the three steps — first the
   *    tallest, third *slightly lower than second* (the screens §5.1).
   *  - `chipMark` — the drawn ▲ / ▼ in a chip, `chipDash` and `chipDashWeight` its drawn —. */
  rankings: {
    trophyPill: 30,
    trophy: 15,
    place: 33,
    podiumFirstFace: 57,
    podiumFace: 48,
    stepFirst: 72,
    stepSecond: 54,
    stepThird: 45,
    chipMark: 6,
    chipDash: 9,
    chipDashWeight: 2,
  },
  /** THE ARRIVED RING — the members card on an official group's page in the administrator area
   *  (#529): how much of the group has arrived, the players over the group size, round the
   *  percentage it draws inside. A drawn object on `surface`, the ring's light-card sibling: a
   *  `line2` track and a `mint` arc (4,07:1 on white, past 1.4.11's 3:1) — the club website's
   *  green bar for the same share. `diameter` holds *117%* in `num.xs` inside the stroke on the
   *  narrowest phone; `stroke` is the meter's weight grown to read at a ring's length. */
  arrivedRing: { diameter: 48, stroke: 4 },
  /** The yes screen's tile — a face at this screen's two sizes, and the initials over a poster
   *  ([ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
   *  §2, §3). MEASURED off the mocks at 1x: 64 x 64 in the singles mock, 54 x 54 in the doubles
   *  one — a step smaller, because four of them and a `vs` have to sit across the narrowest
   *  phone's 290pt of content (4 x 54 + 6 + 2 x 15 + the word is 262). The corner is NOT here:
   *  it fits at 19,6–20,8 on the 64 tile and 17,2–17,7 on the 54, which is a third of the box
   *  either way — `playerPhotoRadius`'s own ratio — so the tile is `PlayerPhoto`'s `face` box at
   *  these sizes and no second radius exists to drift from the first.
   *
   *  `initials` is the SHARE of the tile the two letters are set at — 22pt in the 64 tile and
   *  18–19 in the 54, both 0,34 of the box — kept as a ratio for `RADIUS_RATIO`'s reason: two
   *  sizes of one drawn object, and a point value per size is two numbers to keep in step. It
   *  is the one font size in the app computed from a box, and it is computed inside the tile
   *  that owns the box; a type role for it would be a role with a size per caller. The stage's
   *  hero draws the same tile (`StageFace`) on sign-in's picture of this screen and on sign-up's
   *  podium, the two places ADR-0167's notes extend §3's initials to, and sets its letters at this
   *  share of its poster. */
  yesTile: { singles: 64, doubles: 54, initials: 0.34 },
  /** The swipe row — 6.15. A list row that slides left to REVEAL one control behind it, and
   *  the two numbers that are the gesture's own rather than the row's.
   *
   *  `reveal` is the control's width and how far the card can travel: `btn` type at 12pt
   *  puts *Leave the game* at about 95pt, and `space.md` either side of it lands on the grid
   *  at 120. `intent` is how far a finger travels across before the row claims the touch —
   *  under it a tap is a tap and a drift is the list's scroll, which is the one thing this
   *  control must never take. Four steps of the grid, about a fingertip's width. */
  swipeRow: { reveal: 120, intent: SWIPE_INTENT },
  /** THE DECK'S DRAG — ADR-0169 §3, and the second gesture in the app after the swipe row's.
   *
   *  `commit` is the threshold: the stamp is full there and a release past it commits the
   *  answer in the drag's direction — the mock's 95, kept as measured. `intent` is how far a
   *  finger travels across before the stage claims the touch, and it is the swipe row's own
   *  number READ FROM THERE rather than a second 12: it is the same finger deciding between a
   *  tap, a scroll and a drag, and one rule about that is one number. `flight` is how far a
   *  committed card travels off the stage, past the widest phone's width so it leaves rather
   *  than stops; `tilt` is the most a card turns under the thumb, reached at twice the commit
   *  distance and measured off the two swipe mocks. */
  deckSwipe: { commit: 95, intent: SWIPE_INTENT, flight: 480, tilt: 12 },
  /** THE SHEET'S SWIPE DOWN — 9.1 as amended by [#816](https://github.com/Raketa02/Raketa/issues/816),
   *  the third gesture in the app, on a sheet that asks for it (`closesOnSwipe`), read on its head.
   *
   *  `intent` is the swipe row's number, READ FROM THERE for the deck's reason: the same finger
   *  deciding between a tap on the close and a drag. `close` is how far the sheet is pulled before a
   *  release closes it: about a third of a short sheet, so a nudge springs back. `fling` is the
   *  speed down that closes it however short the pull, in points per millisecond, `PanResponder`'s
   *  own `vy`: a flick, not a drift. `flingWindow` is how recently, in milliseconds, the finger must
   *  have moved for that speed to count — `vy` is the last move's and never decays, so a finger that
   *  stopped and held lifts with a speed it no longer has. Six frames at 60 Hz. */
  sheetSwipe: { intent: SWIPE_INTENT, close: 96, fling: 0.5, flingWindow: 100 },
  /** THE DECK'S THREE ROUND BUTTONS — ✕, i, the ball — measured off the mock at 1×: 54, 42 and
   *  66. Circles rather than 6.1's 10pt rectangle, through `Button`'s `pill` shape (4.2 as
   *  amended: the third user, fenced to this row); the i is under 6.5's 44 and takes `hit.btn`.
   *  The sizes say which of the three is which — the yes is the largest and coral, the pass a
   *  step smaller and white, the record smallest — which is the 1:2 ratio the two named
   *  buttons used to carry, read as diameters.
   *
   *  `ball` is the yes's mark's box: the tennis ball is DRAWN (`DeckBall.tsx`) since 2026-09-15,
   *  where it was the 🎾 as text at `num.levelLarge`'s 26 — and clipped above, because an
   *  emoji is taller than a line box the height of its font size. 26 is that footprint kept,
   *  so the disc's proportion is still the mock's; not a new number. */
  deckAnswer: { pass: 54, record: 42, accept: 66, ball: 26 },
  /** A group's Games card (#553, the screens A2.3), measured off mocks 2–10 at 1x. `ribbon` is
   *  the band's height.
   *
   *  **A tile has one shape per court** (#864; the tab menu log §6.2, 7.22, Part 16 2026-11-24),
   *  width over height, and the deck's tiles never stretch to fill the card (`deckCardGeometry`).
   *  The shapes are **evidence, not a mock** — mock 3's ~1.6 is not used:
   *  - `doublesTile` **1.75**, padel and badminton — the details' own ratio, now named for both
   *    screens. On the user's A32 (384 × 853 dp, read over adb) a deck tile was 160.5 × 84.3 (1.90),
   *    which left 32pt of face above the 52pt name strip; at 1.75 it is 160.5 × 92 there, 163.5 × 93
   *    on a 390 iPhone, 174.5 × 100 on a 412 × 915, and it fills its column on every phone but a 360
   *    Android (143 × 82, height-bound). 1.81 (the widest that fits from 360 up, the least face) and
   *    1.5 (11pt short of its column on a 390 iPhone) were refused.
   *  - `singlesTile` **3:4**, tennis and squash — the photo's own crop (`PROFILE_PHOTO_ASPECT`, and
   *    the 3:4 photo tile, `photoTile`), so on Android the whole photo shows: 160.5 × 214 on the
   *    A32. 1.75 would have left singles ~92pt strips with most of the card empty.
   *  A game's details keep `doublesTile` for both court shapes (out of #859's scope).
   *
   *  **A tile is a fixed box, so its foot's words are capped, and its floor is what they need**
   *  (#865; the tab menu log §6.4, §6.5; 7.22, Part 16 2026-11-24):
   *  - `footMaxScale` **1.3** is the tile foot's `maxFontSizeMultiplier` — the name, the IN and
   *    FRIEND tags, the level line and *paid*, *You complete it*, and the open seat's words — DERIVED
   *    by `gameTileFoot.test.ts` from Archivo's and IBM Plex Mono's real advance widths against the
   *    tile at its smallest drawn size, `tileNarrowest`: the largest step at which *2,71 · paid*
   *    still fits across it and a rescue's open seat still fits down it (both stop at 1.3), and a
   *    bound, not a freeze. *You complete it* fills that tile at 1.0 and its box cuts it above, as it
   *    does the name.
   *  - `tileNarrowest` **128.5** is that tile's width, and the floor: the narrowest phone's column
   *    ((320 − 2 × 15 − 2 × 12 − 9) / 2), 73.4 tall on doubles and 171.3 on singles. Where a short
   *    card shrinks its boxes in proportion the tiles stop here (`deckCardGeometry`), and where even
   *    that does not fit the deck scrolls. It replaced `tileMin` (54), a height fixed beside the
   *    tile's content and already short of a rescue's open seat (61).
   *
   *  The grid's cells
   *  are `cell` tall and `cellGap` apart — **4, off the grid on purpose**: 6.8's hour cells' own
   *  gap (`availability.gap`), so the week is drawn with one rhythm on both surfaces — and the
   *  game's own cell is ringed `ring` wide and grows `ringOut` (`space.xxs`) past its slot on every
   *  side, as the mocks draw it standing proud of its row. The court block's border is
   *  `courtStroke`, a stroke like `onCourtTick`'s, dashed on a free vote and solid on a booking. */
  gameCard: {
    ribbon: 30,
    doublesTile: 1.75,
    singlesTile: 3 / 4,
    footMaxScale: 1.3,
    tileNarrowest: 128.5,
    cell: 9,
    cellGap: 4,
    ring: 2,
    ringOut: space.xxs,
    courtStroke: 1.5,
  },
  /** A group's Fill in rows (7.27, #557; mocks 11–13): *Seats to fill* framed in `coral`, *You're
   *  In* in `mint`, each `stroke` wide — the mocks' 1.5pt, the game card's court stroke again. The
   *  posters in a row are the group page's own seat (`groupPage.seat`). */
  fillInRow: { stroke: 1.5 },
  /** POST A GAME — the posting grid (7.28, #558; the Games & Fill in screens A5.2; mocks 2-, 20–32).
   *  `cell` is a cell's height — its width is the column's, seven to the row after the range
   *  labels' `label` column — 48 on the 3pt grid, which keeps the mocks' 4:5 on a 390pt phone and
   *  clears 6.5's 44 on every one. `gap` is `space.xs` between cells both ways. The hot cell is
   *  ringed `ring` in volt inside an `outline` of `mintInk`, because volt on paper is a line nobody
   *  sees (2.2) and the mocks draw that dark edge; the pick stands `pickGap` off the cell in an
   *  `ink` outline `pickRing` wide, with its white `tick` badge. A game already happening is a `dot`
   *  in the top corner, ringed `dotRing` in `surface` so it reads on every green (coralInk is 1,01
   *  against `mintInk` by luminance). The court glyph is `glyph` — the mocks' small court, a
   *  rounded outline. A cell outside the poster's week is drawn at `outside` with a `dash` border;
   *  one earlier today at `past`. `pager` is the week chevrons' square. */
  postingGrid: {
    cell: 48,
    gap: space.xs,
    label: 66,
    ring: 2.5,
    outline: 1,
    pickRing: 2,
    pickGap: 2,
    tick: 24,
    dot: 11,
    dotRing: 1.5,
    glyph: { width: 17, height: 11, stroke: 1.5, radius: 3 },
    outside: 0.5,
    past: 0.15,
    dash: 1.5,
    pager: 36,
    /** How far a level stepper's box nudges on a bounce — `space.xs`. */
    bounce: space.xs,
    /** The pager's *This week* / *Next week* — the wider of the two at `cardTitle`, on the grid. */
    weekLabel: 84,
    /** The legend's mark column, and a swatch in it: a ramp of four swatches and their gaps fits. */
    legendMark: 54,
    swatch: 12,
  },
  /** YOU › PAYMENTS — the setup checklist and the method card (7.23, #552; mocks 41–47).
   *  `stepMark` is a step's round mark — its number, or the tick once finished — at `fit`'s 26,
   *  the size the mocks draw beside a `question` title. `badge` is the method card's brand square,
   *  42 as mock 47 measures it against the card's 15pt padding. `cardFields` is Stripe's field
   *  row, `textField.row`'s 42 plus the native border Stripe draws inside the box rather than
   *  around it — 44, which is also 6.5's minimum for the one target the row is. */
  payments: { stepMark: 26, badge: 42, cardFields: 44 },
  /** THE UNDO TOAST — 9.2's toast with a draining ring and one action (#555, the Games & Fill in
   *  screens A2.4, A10; Part 16 2026-10-01). `ring` is the ring's box, the toast's `inlineTitle`
   *  line height plus a step, so it sits in the line rather than growing it; `ringStroke` is the
   *  ring around a face on dark, 2. */
  undo: { ring: 20, ringStroke: 2 },
  /** THE RADAR — the sizes of the field's drawn objects, every one of them the spec's own
   *  ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
   *  §7, `the-radar.md` §7.2–7.4). Points; the kilometres, the ladder and the thresholds are
   *  the geometry's and live in `features/play/domain/radarGeometry.ts`, because a stop on a
   *  ladder is a rule about the map and not a size of anything drawn.
   *
   *  `you` is the viewer's tile; `faceWide` and `faceCloser` are a player's face above and at
   *  10 km across; `face` is the card's identity face — the same 34 the viewer's tile is, which
   *  is what makes the card read as the tile opened. `card` is the card's width, ~190 in the
   *  spec and 190 on the grid. `stroke` is the ring around a face and the volt ring around the
   *  viewer, 2 as the mocks draw it. `cluster` is one of the three squares on the right edge,
   *  `btn`'s 34 as mock 15 measures. The three rules that read as sizes and are not — a ring is
   *  drawn at 26 pt of radius or more, at 3,5 field widths or less, and the viewer sits at 42 %
   *  of the field's height at home — are the geometry's own constants, because each is a rule
   *  about where something is rather than how big it is drawn. */
  radar: {
    you: 34,
    faceWide: 24,
    faceCloser: 30,
    face: 34,
    card: 190,
    stroke: 2,
    cluster: 34,
  },
  /** THE ON-COURT MARK'S TICK — a small vector check before the words, everywhere the mark is
   *  drawn (ADR-0169 §7, 7.15 as amended). NOT 6.8's 12 × 12: that box beside *ON COURT* at
   *  `type.tag` does not fit a 74pt panel (`onCourtMarkFit.test.ts`). The tick is sized as a
   *  SHARE of the words' own font size — 0,72, about the cap height — so it reads as part of the
   *  line at every placement, and its stroke is 1,5 for the same reason 6.8's is 2: at 7pt a 2pt
   *  stroke is a blob. Same path as `Tick`, in a smaller box. */
  onCourtTick: { share: 0.72, stroke: 1.5 },
  /** AN OFFICIAL GROUP'S MARK — a seal with `Tick`'s path in it, beside the group's name in both
   *  searches and in its page's header, where the *official* tag was (#529). The product owner's
   *  bound: **no bigger than a lowercase letter**. So its box is a SHARE of the name's own font
   *  size, and the share is Archivo's x-height — 526 of 1000 units (`OS/2.sxHeight`), 6,84pt
   *  beside a row's `cardTitle` and 7,89 beside the header's `h2` — `onCourtTick`'s rule, read at
   *  the lowercase line rather than the capital one. */
  officialMark: { share: 0.526 },
  /** THE SCORE TAG'S SPARK — the four-pointed star before a Player Score on Members' rows, drawn
   *  because Archivo ships no U+2726. A SHARE of the figure's own font size, `onCourtTick`'s
   *  rule: 0,8 of `num.tag` is about the digits' cap height, so the spark reads as part of the
   *  figure rather than as a bullet beside it. */
  scoreSpark: { share: 0.8 },
  /** The text field — 6.13. `row` is the box at ONE line, and it is `btnXl`: the field and
   *  the button it sits above are the same control height, which is what four shipped auth
   *  boxes have drawn since sign-up. It is written as its own number rather than borrowed
   *  inline, because 6.13 is entitled to state its height; that the two agree is DERIVED in
   *  `TextField.test.tsx` rather than typed here twice.
   *
   *  There is no cap token and that is deliberate. A field that grows stops at a number of
   *  LINES, and the number is the caller's — the two surfaces that need one, the composer and
   *  the plan's *where*, have not been drawn on a phone, and #338 §1's rule is that a number
   *  is written only for what a device drew. What the component owns is the arithmetic: one
   *  `type.rlValue` line per step, and the box's vertical padding is `(row - lineHeight) / 2`
   *  rather than a fourth number. */
  textField: { row: 42 },
  /** The message bubble — the conversation's, and the one number this map's stream needed.
   *
   *  `maxShare` is how much of the stream's width one bubble may take, and it is a SHARE for
   *  `railCardRatio`'s reason: the stream is as wide as the phone is, so a point value would be
   *  a different sentence on every device. 0,78 is derived from both ends. The gap it leaves on
   *  the far side is what says which side spoke — on the narrowest stream this app draws, a 320pt
   *  column, that gap is 70pt, unmistakably a gap rather than a ragged edge. And what it holds is
   *  a readable line: 78 % of a 345pt column is 269pt, which at `type.rlValue` is roughly 47
   *  characters — inside the 45-to-75 band a column of prose is set in.
   *
   *  There is no height and no minimum. A bubble is as tall as what somebody typed, and a
   *  one-character message drawn to a floor would be a box with a letter rattling in it. */
  bubble: { maxShare: 0.78 },
  /**
   * The typing indicator's dots — three of them, in the other side's bubble. **A bubble's width
   * comes from its text and this one has none**, so these two are its own numbers: a dot the
   * sport dot's size, so the smallest round mark in the app is one size, and a gap of one step,
   * so three of them read as a group rather than as a row. Read off the mock's proportions;
   * no device has drawn them (Part 16).
   */
  typing: { dot: SPORT_DOT, gap: space.xs },
  /** The star row — 6.13. Five whole stars, and the two numbers are a target and a glyph.
   *
   *  `target` is 6.5's minimum reached BY GEOMETRY rather than by slop, the way 6.8's cell
   *  and 6.11's row are: five stars is five adjacent targets, and horizontal `hitSlop` is
   *  bounded by the neighbour, so a 24pt glyph with slop around it would be five targets
   *  overlapping each other. Five of them is 220pt against the 266pt a card leaves on the
   *  narrowest phone, so the row fits without a gap between the targets — and the gap is
   *  deliberately absent for that reason as well: a dead 6pt strip between two stars is a
   *  tap that answers nothing.
   *
   *  `glyph` is the drawing inside it. The star is GEOMETRY and not a glyph in a font
   *  (`Star.tsx`), so it does not scale with Dynamic Type and does not vary by platform
   *  font — the same decision 6.8's tick takes, and here it also settles a question a font
   *  could not answer: Archivo ships no U+2605, and Feather has no filled counterpart to
   *  its `star` (ADR-0135). */
  star: { target: 44, glyph: 24 },
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
    /**
     * The court a line-up is built on — **the width that makes a seat 60pt**, which is the
     *  size every rule about a seat is computed against: 7.12's *"sixty-four characters of
     *  handle in a 60pt seat is about five"*, and the clear badge's 44pt target standing half
     *  over a 60pt face's corner. 60 / `seatRatio` is 255,3.
     *
     *  **It was 46 (196) until 2026-11-07** (Part 16): on a device, the near-right seat's three
     *  letters ran across the bound line into *YOUR SIDE* on padel and badminton, and the ×'s
     *  44pt target covered a quarter of a 46pt face, so the face's own press — the swap — was
     *  hard to reach beside it. 60 is the smallest seat at which that caption clears the label.
     *
     *  It is a **fixed** width and not the content width, which is what it was: on a large
     *  phone the content width put the seat at 81pt and every one of those arguments was
     *  being made about a court nobody drew. A drawn object with a rule about its parts is
     *  sized by the part, not by the page — and 255 still fits the narrowest phone's 345.
     */
    build: 255,
    /** The court drawn as a **picture beside a sentence** rather than as a surface — the
     *  way onto the court on *Find a game*. It is deliberately under the width at which
     *  `seatRatio` clears `seatMin` (72), so every seat on it is the floor face: a thumbnail
     *  states the SHAPE of the court and the one seat that is yours, and nothing smaller
     *  than a dot is asked of it. Not derived from the content width — a court that grew
     *  with the phone would stop being a thumbnail on a large one. */
    thumb: 54,
    /**
     * The court **inside a card that is about the court** — the pool header's.
     *
     * The number is chosen against `seatMin` rather than by eye. Below 72 the ratio loses to
     * the floor, so a `thumb`'s seat is 17pt against a 54pt court: **31 % of the width where
     * the ratio asks for 23,5 %**, which is why faces on a thumbnail crowd the ground they
     * stand on. That is right for a picture beside a sentence, where the seat is a dot saying
     * a seat exists. It is wrong here, where the faces are the point and the player watches
     * them arrive.
     *
     * At 84 the seat is 20pt and the ratio governs again, so the court is a court with people
     * standing in it rather than a badge with four squares over it.
     */
    header: 84,
    /**
     * The court **on the Now card** — beside the three plan slots, with a face and three
     * letters in every seat (#413).
     *
     * **88, measured against mock 1 at 1×** — the card is 340pt wide in the mock and the
     * court's ground 88 × 116, which is the drawing's own 1,32 — and a number only for what
     * a device drew. It is not derived from `header`: at 88 the seat is 21pt by `seatRatio`,
     * which is what the mock's tiles measure, and the ratio governs rather than the floor.
     * Fixed rather than a share of the slots column beside it, for `build`'s reason — a
     * court that grew with the phone would put a different face size on every device.
     */
    card: 88,
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
  /** The seating ripple's box — `motion.ripple`'s ring at its widest, and the stroke it is
   *  drawn at. A 92pt ring under a 196pt court: big enough to read as the court's own wait
   *  rather than as a spinner beside it, and small enough that the two sentences under it
   *  stay the thing being read. */
  ripple: 92,
  rippleStroke: 2,
  sportDot: SPORT_DOT,
  infoGlyph: 14,
  tabIcon: 16,
  /** The door row's lead — 5.5 as amended for the You tab (Part 16, 2026-09-17): a `paper2`
   *  square before the title with a Feather glyph in it, the one new element on that tab. A
   *  square rather than a bare glyph so the thirteen rows' leads read as one column whatever
   *  each glyph's own extent is; 28 keeps the row at 6.5's minimum with `space.sm` above and
   *  below it, and the glyph is a step under `tabIcon` because it sits inside a fill. */
  rowLead: 28,
  rowLeadGlyph: 15,
  /** The tab bar — 10.2: **the dock**, a rounded slab floating over the screen's foot, in equal
   *  columns, an Ionicons icon over a `tag` label in each, and the selection marker under the lit
   *  one ([ADR-0210](../../../../docs/adr/0210-the-tab-bar-floats-as-glass-and-its-selection-travels.md)
   *  §2, §5, #883). The ⚡Play disc, its ring and their sizes (`fab` 30, `bolt` 15, `ringGap` and
   *  `ringStroke` 2) retired with it (§6).
   *
   *  **54 tall at every text size and in every state.** The column's content is centred in it, and
   *  the cap below is what keeps that content inside the marker: 18 + 3 + `tag`'s 12pt line at 1.6
   *  is **40.2** inside 42, where a 20pt icon would be 42.2. The bar's **reach**, the room it
   *  takes at the bottom, is the lift + 54 (`tabBarReach.ts`): 66 on the A32, 88 on a notched
   *  iPhone.
   *
   *  `labelMaxScale` is the only Dynamic Type mechanism this surface has: Part 13 names the
   *  tab bar as the fixed-height exception AND permits `allowFontScaling={false}` only
   *  inside the level bar, which leaves a bounded multiplier and nothing else. It was
   *  **derived** over five columns — 1.7 over *Around*, 1.6 over *Players* (ADR-0169 §1) — and
   *  the bar is three since the old loop's two columns left it (#576): at a third of the screen
   *  every word fits at more than twice this, so the width no longer decides it. It stays where
   *  the five left it, and it now holds the label inside the 42pt marker. `tabBarLabelCap.test.ts`
   *  measures the icon and the three shipped labels against the real Archivo 700 advances, inside
   *  the marker and inside the narrowest phone's column, so a fourth tab or a longer word goes red
   *  rather than truncating on somebody's phone. */
  tabBar: {
    /** The dock's height — the brief's 54, on the grid. */
    height: 54,
    /** Its distance from either side of the screen — the gutter's step below 15, so the page shows
     *  either side of it. */
    sideInset: space.md,
    /** **The least** it is lifted off the bottom: the dock stands the larger of this and the bottom
     *  inset above the phone's foot, so it rests on a notched iPhone's safe-area line and stands 12
     *  clear of three edges on an Android phone with no inset. The brief's 10 is off the grid; 12
     *  equals the side inset. */
    lift: space.md,
    /** THE SELECTION MARKER (#883, ADR-0210 §4): an opaque `coralSoft` capsule at `radius.pill`,
     *  centred in the lit column, under its icon and label. 75 rather than the brief's 76, which is
     *  off the grid. On the narrowest phone a column is (320 − 24) ÷ 3 = 98.7 wide, so the marker
     *  keeps the 97.5 its stretch will peak at (#884) inside it. */
    marker: { width: 75, height: 42 },
    /** The icon's box — Ionicons at 18, the largest that keeps icon + 3 + the capped label inside
     *  the marker (above). 16, `tabIcon`, is the fallback if 18 looks crowded on the phone (#885);
     *  everywhere else in the app a 16pt Feather glyph stays `tabIcon`. */
    icon: 18,
    labelMaxScale: 1.6,
    /** Home's badge — 10.2, and the one badge the bar carries.
     *
     *  **18, and it is the digit's own box rounded to the grid.** The count is mono and tabular
     *  (1.4: numbers are monospaced always), and the smallest mono role is `num.xs`, whose line
     *  box is 17 — the same borrowing 7.10's fit pill already made, for 15.3's reason: a
     *  seventh size step for one mark is what that section says not to add. Eighteen is 17 on
     *  the 3pt grid, and it is a MINIMUM width rather than a diameter, because the badge has no
     *  cap: a two-digit count spreads it into a lozenge at `radius.pill` and the digits stay
     *  tabular, so 1 -> 2 does not reflow the column.
     *
     *  `badgeRise` is how far it stands above the icon box — 16pt on the bell and the envelope,
     *  `tabBar.icon`'s 18 on the bar. It was the 4 the ⚡Play disc's ring took out of the old
     *  bar's 6pt top padding; the ring retired (#883) and **the 4 stays as the badge's own
     *  number**. Out of the layout, so the dock is 54 whatever the count: its top is 6.5 inside
     *  the dock's top edge at 1× and 2.9 at the cap.
     *
     *  Everything else is borrowed rather than invented: `coralInk` fill and a white mark at
     *  5,89, which is 6.1 `primary`'s treatment; the horizontal padding and the overlap over the
     *  icon are `space.xxs`. `tabBadgeFit.test.ts` holds the arithmetic a device would otherwise
     *  have to. */
    badge: 18,
    badgeRise: 4,
  },
  grabber: { width: 36, height: 4 },
  sheetClose: 28,
  popoverWidth: 250,
  popoverArrow: 11,
  /** 9.4: the narrowest a guide's bubble may stand **beside** its mark — *Skip* and *Next* side by
   *  side at `sm`, under the count, with the bubble's padding. Narrower than this, and it stands
   *  under or over the hole instead. */
  guideBesideMin: 180,
  /** The rail's page dots — 7.18, and Part 8's sizes before that. Five points resting; the
   *  one you are on keeps the height and grows to fourteen, so the state has a SHAPE channel
   *  and is never carried by tone alone (Part 13). Gap is `space.xxs`.
   *
   *  These two numbers did not move; what moved is what draws them. Part 8 had them as
   *  decoration on a strip, in `coral`. A full-width card leaves the rail with no peek, so the
   *  dots became the affordance — and the fill is `color.ink`, because 1.2's coral list closes
   *  at five plus the tab bar's badge and a coral FILL there means *attend to this*, which a page
   *  indicator is not. **Not pressable** — 7.9's own hitSlop arithmetic, one section over. */
  pagerDot: 5,
  pagerDotActive: 14,
  /** Horizontal page gutter, both sides. Content width = screen width - gutters. */
  gutter: space.lg,
  /** The PEEKING rail's card — 7.7's first geometry, where the peek IS the affordance. A
   *  RATIO, never 268pt: on a 320pt phone a fixed 268 leaves no peek at all.
   *
   *  There is a second rail and it has no ratio, because its card is the content width
   *  whole. What carries the affordance there is 7.18's dots. */
  railCardRatio: 0.74,
  /** THE REQUEST CARD in Needs your answer — a friend request, and the ask for a level drawn as
   *  one ([#816](https://github.com/Raketa02/Raketa/issues/816); home refactor 2; ADR-0205 §9.3):
   *  the peeking rail's card, WIDER, so the face, two lines of title, the chip and two buttons fit
   *  without the squeeze 0,74 gave them. MEASURED off home refactor 2: the tile is 450 of the
   *  content's 540 pixels, 0,833. A RATIO, for `railCardRatio`'s reason; the next card's edge is
   *  still the affordance, at 0,17 of the content less the gap. */
  requestCardRatio: 0.83,
  /** THE PHOTO CAROUSEL's card — all of a player's photos, sideways, on the record
   *  ([#799](https://github.com/Raketa02/Raketa/issues/799)) and the vibe sheet (home rows 23, #803),
   *  over Part 8's Strip (Part 16 2026-11-14). A card's share of the content width, for
   *  `railCardRatio`'s reason — a ratio, never a point value. **Half**: home rows 23 draws two photos
   *  side by side, the second running into the sheet's edge, so two stand on screen and a third's
   *  edge is the affordance. Its height is the photo panel's 4:5, read off `PHOTO_PANEL` — one owner
   *  of the shape. */
  photoCarouselRatio: 0.5,
  /** **FOR YOU's folding line** ([#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0205
   *  §5, §9.5; home refactor 3–13). A white card, `radius.card`, its 1pt border `line` closed and
   *  `ink` open. `pad` is the card's inset, the title's and the open content's — the gutter's 15,
   *  which is what the mocks measure (23 of the phone's 1,5 pixels to the point): a rail inside it
   *  starts its first tile there and bleeds to the card's inner edge, so a tile's share is of the
   *  card's content, not the page's. The header's `h2` line and `space.md` above and below it are
   *  `minTouch` exactly, the closed line's height in home refactor 4.
   *
   *  `count` is THE COUNT PILL's least height (#822; 7.37; home refactor 3, 4, 7): **16, and it is
   *  `num.tiny`'s own line box**, the figure's role — the corner badge's borrowing (`segmentBadge`),
   *  for 15.3's reason. MEASURED off home refactor 4 at the mocks' 1,5 pixels to the point: the pill
   *  20–22 pixels tall, about 14pt, and the digits' ink 12 pixels, `tiny`'s 11pt; 16 is the figure's
   *  box and the nearest the grid allows without clipping it. A least height, not a fixed one, so a
   *  larger OS text size grows the pill with its figure. Its width is the figures and `space.xs` each
   *  side — a lozenge at `radius.pill` even for one digit (the mock's *6* is 31 pixels wide, its *14*
   *  40). */
  foldingLine: { pad: space.lg, border: 1, count: 16 },
  /** THE PORTRAIT TILE (#801; home rows 17–19; 7.31) — a face edge to edge with its words over the
   *  wash. **Its width on a Home row is the peeking card's, `railCardRatio`** (2026-11-24): it was
   *  0,355 here, home rows 17's two whole and the third cut, and the words on a tile that narrow were
   *  hard to read beside the row above's cards — one ratio now, so the two rows cannot drift apart.
   *  `railAspect` and `gridAspect` are its height over its width — 11:8 standing on a row, 9:8 in See
   *  all's two columns (home rows 19), MEASURED off the mocks at 1× (384 × 528 and 266 × 297
   *  pixels). */
  portraitTile: { railAspect: 1.375, gridAspect: 1.125 },
  /** THE ROUND FRIEND BUTTON (#801; home rows 8, 10.3, 17, 18–18.3; 7.32) — MEASURED off the tiles at
   *  1× (72 pixels on a 384-pixel tile): a 24pt circle centred in its own 44pt press (`minTouch`) —
   *  a box, not a hitSlop, because a touch never lands past its parent on Android and a tile clips.
   *  `halo` is the envelope's paler ring outside it; `dot` and `dotGap` the **…**'s three dots;
   *  `glyph` the envelope's Feather size, the plus and the tick being 6.8's own 12pt box. */
  roundFriend: { face: 24, halo: 3, dot: 3, dotGap: 2, glyph: 12 },
  /** THE COMPARISON BAR (#802; home rows 7–16; 7.33) — the Skill passport's 1,00–5,00 and its four
   *  bands, a fill to the other player's level and a tall mark at the reader's. MEASURED off home rows
   *  8 at 1× (2,75 pixels to the point): an 8pt track, a 6pt mark 22 tall in a 2pt ring of the ground,
   *  its YOU 3 above. `onDarkBand` is a band's `tint` over the card's ground — #344B5A, #31514E and
   *  #534541 measured, each its tint at 0,26–0,31 — where the light bar takes 7.5's `inactiveOpacity`.
   *  `nameMinScale` is how far a band's name may shrink to stay on one line under its band on a Home
   *  row's card, where _ESTABLISHED_ has 30 % of 0,74 × content less the padding. */
  comparisonBar: {
    trackHeight: 8,
    markWidth: 6,
    markHeight: 22,
    markRing: 2,
    labelGap: 3,
    namesTop: 6,
    onDarkBand: 0.28,
    nameMinScale: 0.75,
  },
  /** THE SAME LEVEL CARD (#802; home rows 7, 8, 10.3; 7.34) — a face 44 on either side, MEASURED (120
   *  pixels at 2,75); the % between them at `num.xl`, the game card's figure. */
  sameLevel: { face: 44 },
  /** THE SAME VIBE TILE (#803; home rows 20, 22–22.3, 24; 7.35) — its face and the vibe %'s white
   *  circle, MEASURED off the mocks at 1×: on Home's row 120 and 95 pixels at 2,92 to the point (41
   *  and 33), in See all's two columns 60 and 48 at 1,74 (34 and 28), onto the 3pt grid. The vibe
   *  sheet's face is the row's. */
  sameVibe: { face: { row: 42, grid: 36 }, percent: { row: 33, grid: 30 } },
  /** TOP 10'S CARD ([#805](https://github.com/Raketa02/Raketa/issues/805); home rows 2, 25–27; 7.36)
   *  — MEASURED off home rows 2 at 1,5 to the point and 25–26 at 3:
   *
   *  - `railRatio` — a card's share of the content width, for `railCardRatio`'s reason: 104pt of 360
   *    in both mocks, narrower than New in Raketa's tile, because the numeral stands beside each one.
   *  - `aspect` — its height over its width: 154 over 104.
   *  - `overlap` — how much of the numeral's box the card covers, from the right: home rows 26 shows
   *    32pt of the *1*'s ink and 25 39pt of the *2*'s, which at `type.numeral` leaves 24 under the card.
   *  - `ring` — the reader's own card's volt ring, outside the card: 7 pixels at 3 (home rows 26.1).
   *  - `outline` and `edge` — the numeral's paper outline, and the hairline of `line` that lets it
   *    be seen on paper (home rows 25.3: about four pixels of paper and one of grey at 2).
   *  - `chipMark` — the drawn ▲ / ▼ beside a card's level, the level's own size; `lean` the slant, in
   *    degrees, the mark and its count take together as an italic would (no italic face is loaded).
   *  - `figure` — `type.numeral`'s face's own metrics, in ems, READ OFF `Archivo_800ExtraBold.ttf`: a
   *    figure's advance (tabular — every figure 625 of 1000 units), how far the figures stand over
   *    the baseline, and the deepest under it (the *9*'s tail). The numeral's box is worked out from
   *    them, so they change with the role's face or not at all. */
  topTen: {
    railRatio: 0.29,
    aspect: 1.48,
    overlap: 24,
    ring: 2.5,
    outline: 1.5,
    edge: 0.75,
    chipMark: 8,
    lean: ITALIC_LEAN,
    figure: { advance: 0.625, top: 0.699, foot: 0.012 },
  },
  /** Nothing tappable may have a reachable area smaller than this. Use hitSlop. */
  minTouch: 44,
  /** THE STAGE — sign-in's and sign-up's dark hero and the paper sheet over it
   *  ([#784](https://github.com/Raketa02/Raketa/issues/784); 12.2, Part 16 2026-11-08).
   *
   *  `heroShare` is where the sheet's top edge sits at rest, as a SHARE of the window's height:
   *  mock 1 puts it 366 of the screen's 885 pixels down, 0,41 — *a little under half*. Of the
   *  window and never of the laid-out screen, because Android's window shrinks for the keyboard
   *  and the hero must not move when it does.
   *
   *  `textMaxScale` is the hero's one Dynamic Type mechanism — the tab bar's `labelMaxScale`
   *  approach, second instance: the hero is a picture with a fixed room, so its words may neither
   *  be frozen nor grow without bound. DERIVED in `stageTextCap.test.ts` as the largest step at
   *  which every stage headline stays within three lines on the narrowest phone: sign-in's alone
   *  allowed 1,7, and sign-up's longer line (#785) holds it at 1,6. The form under it is not
   *  capped: it scrolls.
   *
   *  `mark` is the wordmark's volt dot: 22 pixels in mock 2 at 2,85 to the point.
   *
   *  `control` is the sheet's control height — its text boxes (6.13's stage look) and its two
   *  buttons (6.1's `stage` size) alike: 87–88 pixels in mock 3 at 1,82 to the point, so 48, where
   *  the app's own box is 42. The three are one height in the mock, as 6.13's box and `btnXl` are
   *  everywhere else.
   *
   *  `card` is sign-in's **miniature game card** (#786, 12.2) at the size it is DRAWN, before the
   *  deck is scaled into the hero's room: mock 2's front card is 385 × 488 pixels at 2,85 to the
   *  point, and its words measure the real card's own roles at almost exactly half their size — so
   *  the miniature is drawn at twice the mock's size, 270 × 342, with `gameCard`'s roles, and the
   *  deck is scaled by about a half on a 390pt phone. `ribbon` is the mock's band at that size, 45 —
   *  half again the real card's 30, the one proportion the mock draws chunkier.
   *
   *  `fan` is where the deal puts the two back cards, in the card's drawing points: their centres
   *  `across` either side of the front card's and `down` below it, turned `turn` degrees outwards —
   *  mock 2's 142 and 46 pixels at 2,85 to the point, doubled, on the 3pt grid, and its ten degrees.
   *  The front card stays where the three were stacked, straight (`stageDeckGeometry.ts`).
   *
   *  `swipe` is the loop's front card (#787), in the same drawing points: picked up `across` to the
   *  right and turned `turn` degrees — *a little right, a few degrees* — then swiped off turning on
   *  to `outTurn`, the real deck's own 12° past the pick-up's 6, and fading once it is `fadesFrom` of
   *  the way off — its last stretch. `stamp` is the **I'M IN** stamp on
   *  it: the real deck's 3pt outline (`stroke`) and 12° (`tilt`), but clockwise and top-right, where
   *  mock 2 draws it, `top` below the card's top edge — the mock's 50 pixels, astride the ribbon's
   *  foot. `splashTile` is a face on the hero's *It's a game!* (mocks 7–8): 44pt measured in both,
   *  45 on the 3pt grid, where the yes screen's own are 54 — the hero is under half a screen.
   *
   *  `podium` is sign-up's Rankings podium (#788), in its own drawing points, which are mock 5's
   *  at 2,1 pixels to the point (its 390pt phone) put on the 3pt grid — so on that phone it is
   *  drawn at about its own size, and it is scaled down whole into a smaller room, never up.
   *  `stepWidth` is each step's, `space.sm` between them; `step` their heights — the first the
   *  tallest, the third *slightly lower than the second* as the live podium draws them, but
   *  mock 5's own heights and NOT `size.rankings`', since a change there does not reach the hero
   *  by itself. `face` is each player's tile, outer edge to outer edge: You's the largest, the
   *  third's a step under the second's, as mock 5 draws it. `ring` is the volt ring round You's,
   *  `rim` the translucent edge round the others' (`stageRim`) — both drawn inside the tile. */
  stage: {
    heroShare: 0.41,
    textMaxScale: 1.6,
    mark: 8,
    control: 48,
    card: { width: 270, height: 342, ribbon: 45 },
    fan: { across: 99, down: 33, turn: 10 },
    swipe: { across: 24, turn: 6, outTurn: 18, fadesFrom: 0.6 },
    stamp: { top: 33, tilt: 12, stroke: 3 },
    splashTile: 45,
    podium: {
      stepWidth: 93,
      step: { first: 93, second: 66, third: 51 },
      face: { first: 63, second: 48, third: 45 },
      ring: 3,
      rim: 2,
    },
  },
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
  /** The people list's row (7.19): a 38pt face is the row's height, and the rows sit
   *  `space.sm` apart — so 3 a side lifts it to 44 and leaves 3 of the 9pt gap between two
   *  targets, which is the neighbour rule read vertically. No horizontal slop: the row is
   *  already the card's width. */
  peopleRow: { top: 3, bottom: 3 },
  /** Home's trophy pill (#775): 30 tall, lifted to 44. */
  trophy: { top: 7, bottom: 7 },
  /** *2 sports ›* on the Same level card's footer (#802; 7.34): a 16pt line in the footer's 44pt
   *  row, beside the round friend button's own 44 box — 14 above and below reach exactly the row's
   *  edges, so no touch lands past its parent on Android; 6 sideways keeps clear of the gap's words. */
  sportsLink: { top: 14, bottom: 14, left: 6, right: 6 },
  /** The week grid's hour cell (6.8): half the 4pt gap on every side, which is all the
   *  neighbour rule allows and exactly enough that the reachable areas tile the grid with no
   *  dead point between two cells. It does not reach 44 — see `size.availability`. */
  availabilityCell: { top: 2, bottom: 2, left: 2, right: 2 },
} as const;

// ---------------------------------------------------------------------------
// Elevation — seven shadows in the whole system, five for things that genuinely float, one
// for the club results of the two group searches and one for FOR YOU's open line, plus one TEXT
// shadow, which is a different mechanism and not an elevation at all.
// CARDS NEVER HAVE ONE: depth on paper comes from the surface change and the 1pt border.
// The deck card is here because it is not a card, not because the rule bent; the club result
// and the open line are the two amendments to the rule, each named rather than absorbed (4.3,
// Part 16).
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
  /** THE TAB BAR'S DOCK — the fifth (10.2, #883, ADR-0210 §6), in the slot the ⚡Play disc's
   *  coral-tinted `fab` left when the disc retired, so the inventory stays at seven and none of
   *  them is tinted any more. **The deck card's values**, the faintest of the shadows for things
   *  that float over the page — the dock is lifted off the page, not a card on it. `elevation`
   *  the deck card's 8: on Android's opaque dock it draws as it is (the A32 spike's T3, #880).
   *  **Where the dock draws the glass — always on the iPhone — it is shadowed by `glass.shadow`
   *  instead**, the same values as `boxShadow`, which is drawn outside the box only: a translucent
   *  fill would show `elevation` through it, and gives iOS's shadow props no opaque fill to work an
   *  outline from, so they would be drawn from the dock's pixels in an off-screen pass. */
  dock: {
    shadowColor: '#0B2B33',
    shadowOffset: { width: 0, height: 7 },
    shadowOpacity: 0.12,
    shadowRadius: 20,
    elevation: 8,
  },
  /** THE CLUB RESULT — the sixth, and the only card-shaped surface that casts one: one drawing
   *  (`ClubCard`), in New group's home-club search and in Join a group's.
   *
   *  The product owner's mocks (2026-09-27) lift every club a search answers off the page, because a club and the groups under it were one list with nothing to say where
   *  one club ended: on paper, a 1pt border between two white cards nine points apart is not
   *  enough to read a club and its groups as one object. It is the faintest and the tightest
   *  of the six — the result sits on the page it lifts from, it is not over anything — and its
   *  `elevation` is the lowest, below the dock's, because the bar passes over it. */
  clubResult: {
    shadowColor: '#0B2B33',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  /** THE OPEN LINE — the seventh, and the second card that casts one: FOR YOU's line while it is
   *  open ([#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0205 §5, §9.1; home refactor
   *  5, 6, 8, 10, 12), beside its `ink` border and its chevron turned down. A closed line casts
   *  none, as any card.
   *
   *  The mocks lift the one open line off the page so it is unmistakable among four closed ones.
   *  Soft: the club result's colour, a wider blur at the same faint opacity, and a lower drop — the
   *  line is over nothing, it only stands forward — so it reads as a halo round the border rather
   *  than a card floating. `elevation` the club result's 3: the bar passes over both. */
  openLine: {
    shadowColor: '#0B2B33',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 3,
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
// Motion — one entrance, one sheet, one popover, one fade, one ripple, one pulse, one settle, one
// unfold, one disclose, the yes screen's entrance, which is the first and the fade composed, and
// one sweep, the skeleton's band looping while a screen has nothing to draw yet (2026-11-24).
// Nothing else moves.
// Press feedback is immediate (Pressable's `pressed`), not animated: the prototype's
// 120ms is a mouse-hover transition and has no touch equivalent.
//
// Every one of these is skipped when AccessibilityInfo.isReduceMotionEnabled is true — but
// `kindSwap`, which crossfades there instead (its own note), and `skeleton`, which sweeps there
// unchanged, as the calculating screen's indicator and the busy spinner turn there unchanged:
// design-system Part 13's three exceptions, the two indicators having no token here (its own note).
// ---------------------------------------------------------------------------

/** The two durations the yes screen's entrance is composed from — see `motion.yesEntrance`. */
const FADE = 200;
const RISE = 300;

const motion = {
  fade: FADE,
  /**
   * One ring, expanding out of nothing and fading as it goes — one of **two looping animations
   * in the app**, and the first motion token whose duration is a cycle rather than a
   * transition. The second is `typing`, below.
   *
   * It is spent on the one thing in the product that is genuinely open-ended: the engine
   * seating a court, drawn under the court it is seating rather than over the screen. A
   * spinner would have done the same job and says *something is loading*; a ripple says
   * *something is being looked for*, which is what is happening.
   *
   * Skipped under reduced motion like the four above it, and there the ring is simply drawn
   * at rest — the sentence beneath it is what carries the state, so nothing is lost.
   */
  ripple: 1400,
  /**
   * The typing indicator's pulse — three dots, each brightest a third of a cycle after the one
   * before it — and **the one thing in this app that animates although §1.5 says nothing has
   * to**: three still dots are indistinguishable from a message that says `...`, and the motion
   * is the whole signal. The argument is in Part 16 and on `TypingBubble.tsx`; the number is a
   * cycle a reader sees as *now* rather than as a blink, and no device has drawn it.
   *
   * Skipped under reduced motion, where the dots are drawn still and the element's spoken name
   * carries the fact — stated as a trade rather than a save, because a sighted reader with
   * reduced motion gets the weaker of the two signals.
   */
  typing: 1200,
  /**
   * **The skeleton's sweep** (PRD #867, #868; 1.5, Part 13, Part 16 2026-11-24): one band of light,
   * `color.skeletonSheen` between two `color.skeleton`s, crossing every shape on a screen at once
   * while that screen has nothing to draw yet. It runs left to right across the screen's width once
   * every `sweep` milliseconds, at constant speed, with no pause, for as long as the shapes stand;
   * the band is tilted `tilt` degrees. `transform` alone, on the UI thread. A loop, argued in
   * Part 16 against 1.5.
   *
   * **Both numbers are Facebook Shimmer's Android defaults, read from its source** (`Shimmer.java`:
   * `animationDuration = 1000L`, no repeat delay, `RESTART`, `INFINITE`, `LEFT_TO_RIGHT`,
   * `tilt = 20f`), the loading shimmer log's Q24. It refused the iOS library's 230 pt/s with its
   * 0,4 s pause, and any number picked without a source.
   *
   * **It sweeps under reduced motion** (`ReduceMotion.Never`, without which Reanimated cuts the
   * timing): the third named exception, beside the calculating screen's indicator and the busy
   * spinner, for their reason (Q2). A still loading screen reads as frozen, and this is progress,
   * not decoration.
   */
  skeleton: { sweep: 1000, tilt: 20 },
  rise: RISE,
  sheet: 260,
  popover: 130,
  /**
   * **The tab's menu** folding out of its tab and back (9.5, #861; PRD #859's *about 150ms*): the
   * card fades in from `size.tabMenu.drop` above its place, and the chevron on the tab turns over —
   * opacity and transform only, on the native driver. The selected tab's widening rides the same
   * beat as a layout transition. All of it is skipped under reduced motion, where the menu is simply
   * open or shut.
   */
  tabMenu: 150,
  /**
   * **The Games deck swapped to its other kind in place** (#863; PRD #859's *about 200ms* and *about
   * 250ms*, *about 24pt*): picked from the tab's menu, the stack goes `rise` down and fades out over
   * `out`, then the other kind's stack comes up from `rise` below into the same place and fades in
   * over `in` — the cards alone, opacity and transform on the native driver, `easeDecel`, the stage
   * never scaled. The buttons under it fade over the same beats where one side has none. **Under
   * reduced motion it is a crossfade, not skipped**: nothing travels, and the two fades run — a cut
   * from one kind's cards to the other's would not say the deck changed.
   */
  kindSwap: { out: 200, in: 250, rise: 24 },
  /**
   * The swipe row's card coming to rest once the finger lifts (6.15) — to revealed or to closed,
   * never in between. Short enough to read as the card *landing* rather than travelling, since the
   * finger has already done the travelling, and long enough that a card released a few points
   * short of the threshold is seen to go back rather than to blink. Skipped under collapsed
   * presentation, where the card is drawn at rest.
   */
  settle: 160,
  /**
   * The group page's fast filter unfolding from its pill (play 41–42, #513): the white bar grows
   * leftwards from the pill over the group's name while the other sports slide out one by one
   * from under the current one, each over half of this and each starting a step after the one
   * nearer the pill. Between `sheet` and `rise`, because three words have to be seen arriving
   * in turn and a `popover` is over before the second has moved. `easeDecel`, on the UI thread.
   * **Folding is not animated**: the finger has already chosen, and the pill it folds back to is
   * a state the eye already knows. Skipped under reduced motion, where the bar is simply open.
   */
  unfold: 280,
  /** A level bound pushed past the engine's own (7.28, #558): the stepper's box nudges sideways
   *  and back in four legs over this long, beside *You can narrow it, not widen it*. Skipped under
   *  reduced motion — the words carry it alone. */
  bounce: 240,
  /**
   * The record sheet's *Full record* opening and closing under its three blocks: the fold's
   * height runs to the content's measured height while the content fades in and slides down a
   * `space.md` into place, and the chevron turns over. **Both ways**, unlike `unfold`: closing
   * hands the space back to the sheet, and a sheet that jumped a card's height shorter would
   * read as a different surface. `unfold`'s pace, `easeDecel`, on the UI thread. Skipped under
   * reduced motion, where the fold is simply open or shut.
   */
  disclose: 280,
  /**
   * **FOR YOU's line unfolding** ([#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0205
   * §5; the brief's *about a quarter of a second, fast at the start and settling at the end*): the
   * fold's height runs to the content's measured height in one layout transition, the lines below
   * sliding down on the same beat, while the content fades in from a `space.md` above its place and
   * the chevron turns down — `disclose`'s mechanics, `easeDecel`, on the UI thread.
   */
  lineUnfold: 250,
  /**
   * **And folding back**, *over a slightly shorter moment* (the brief): the content fades and the
   * lines below slide up, and only then is the content let go — a closed line draws nothing. A
   * switch runs this first and `lineUnfold` after it, never both at once. Both are skipped under
   * Reduce motion (ADR-0205 §8), where a line is simply open or shut.
   */
  lineFold: 200,
  /**
   * The radar's flight — a tap on a face carries the view to them, centred, at the 3 km stop
   * ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
   * §7: *about 400 ms*). One beat on the field's own transform, `easeDecel`, and skipped whole
   * under collapsed presentation, where the view is simply there. The pinch and the drag are not
   * here: a finger does its own travelling, and only the release back from past the reach's edge
   * borrows `settle`.
   */
  flyTo: 400,
  /**
   * The yes screen's entrance — **one beat, composed of the durations above and no new one**
   * ([ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
   * §2). The two sides slide in from the edges and meet at the centre over one `rise`; the word
   * rises in over a second `rise`, starting half-way through the first so it lands as the sides
   * meet; the buttons fade in last over one `fade`, once the word has landed. 650 ms end to end,
   * which is the record's *about 600*, and the one success haptic fires as the word lands.
   * Nothing loops. Skipped whole under reduced motion, where everything is simply there and
   * nothing buzzes — and under a running screen reader (§20.11's collapse), where the haptic
   * still fires once, because a buzz is not a picture.
   */
  yesEntrance: {
    sides: RISE,
    word: RISE,
    /** When the word starts, after the sides do. */
    wordAfter: RISE / 2,
    buttons: FADE,
    /** When the buttons start: the moment the word lands. */
    buttonsAfter: RISE / 2 + RISE,
  },
  /**
   * **Sign-in's hero loop** ([#786](https://github.com/Raketa02/Raketa/issues/786),
   * [#787](https://github.com/Raketa02/Raketa/issues/787), 12.2) — the hero's picture, and the one
   * thing on the stage that moves; the **third looping animation in the app**, after `ripple` and
   * `typing`, argued in Part 16 against 1.5. One cycle, about nine seconds:
   *
   * - `stacked` — the three miniature cards exactly on top of each other, read as one card;
   * - `deal` — the two back cards slide out to their turned places, `easeDecel`;
   * - `still` — nothing moves, so the cards can be read;
   * - `pickUp` — the front card lifts a little right and turns, and *I'M IN* comes up on it,
   *   `easeDecel`;
   * - `swipe` — it accelerates off past the right edge, fading in its last stretch;
   * - `splash` — *It's a game!* over the hero, from the moment the card is gone until it fades: its
   *   own entrance is the yes screen's (`yesEntrance`'s sides and word, under a `fade`);
   * - `reset` — the splash fades over the cards, restacked under it, and the next cycle deals.
   *
   * Only while sign-in is the screen in view and the app is not in the background (iOS's `inactive`
   * leaves it running); it starts again from the deal on return. Skipped whole under collapsed presentation, where the cards are dealt from the
   * first frame, nothing moves and the splash is never drawn.
   */
  stageDeck: {
    stacked: 400,
    deal: 500,
    still: 2000,
    pickUp: 700,
    swipe: 600,
    splash: 4000,
    reset: 400,
  },
  /**
   * **Sign-up's podium rising** ([#788](https://github.com/Raketa02/Raketa/issues/788), 12.2) —
   * played **once** when sign-up opens, and never again until it opens again: a statement, not a
   * gesture, so it does not loop (argued in Part 16 against 1.5). About a second and a half:
   *
   * - `empty` — the wordmark and the headline alone, the steps flat and nobody on them; as long
   *   as the native stack's cross-fade from sign-in (react-native-screens' 350 on iOS, the
   *   default `(auth)/_layout` keeps), so nothing moves before the screen has landed;
   * - `step` — one step growing up to its height, `easeDecel`: a quick start and a soft landing;
   * - `stagger` — how long after one step starts the next does: the third, then the second, then
   *   the first, last and tallest;
   * - `player` — each player arriving as their step settles, from a little below, fading in,
   *   `easeDecel`: `ines.d`, `stas.w`, then You with the volt ring.
   *
   * Ends at `empty + 2 × stagger + step + player`, 1 500. Skipped whole under collapsed
   * presentation, where the podium stands risen with its players from the first frame.
   */
  stagePodium: {
    empty: 350,
    step: 450,
    stagger: 200,
    player: 300,
  },
  /** The prototype's cubic-bezier(.2,.8,.2,1) — decelerating. */
  easeDecel: { x1: 0.2, y1: 0.8, x2: 0.2, y2: 1 },
  /** Accelerating — cubic-bezier(.4,0,1,1), a thing thrown off: slow away, then faster. Sign-in's
   *  hero card leaving on its swipe (#787) and nothing else; `easeDecel` is the app's curve for a
   *  thing arriving, and this is its one leaving. */
  easeAccel: { x1: 0.4, y1: 0, x2: 1, y2: 1 },
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
    /** The pool's minimum display floor — §J6's *"so a fast answer does not flash past"*.
     *  A floor with no stagger over it, so reduced motion changes nothing here: it is not
     *  skipped, because the concern is legibility rather than movement, and the player who
     *  asked for calm is the last one to be given a flash. */
    pool: 1100,
    /** The engine fill's floor — the **held** half of the fill's `650 plus 550 per seat`.
     *
     *  The split is the whole point. This number survives reduced motion for `pool`'s
     *  reason; the 550-per-seat **stagger** is motion, collapses to zero, and lands every
     *  seat together after this same beat. The stagger is not here because it is the
     *  **court's own** and belongs beside the animation it drives; these two are here
     *  because two screens share them, and a floor typed twice is a floor that drifts. */
    fill: 650,
    /** A toast — 9.2. The prototype's 2600, kept: it is the read time of the longest of the
     *  nineteen sentences this app fires, and it is what the QUEUE spends per message, so
     *  shortening it is a decision about how long a listener waits rather than a tidy-up.
     *  Nothing surrounds it: the toast neither arrives nor leaves on an animation (1.5), so
     *  this is the whole of that component's timing and there is no reduced-motion branch. */
    toast: 2600,
    /** The in-app banner a push draws while the app is open (#559, Part 16 2026-10-02). Long
     *  enough to read a notice's two lines **and** reach for it — it is a control, unlike the
     *  toast — and it closes on a press too, so a player in a hurry is not held by it. */
    notice: 6000,
  },
} as const;

/** zIndex is scoped to the parent in RN, so overlays render from a single root-level
 *  overlay host — which is also what keeps a popover out of a dark card's repaint. */
const layer = { sheet: 20, toast: 40, popover: 60 } as const;

// ---------------------------------------------------------------------------
// The glass — where the tab bar's dock draws `color.glass` over a blur, and how strong the blur
// is (10.2, ADR-0210 §7). The one glass surface in the app (1.1), so one switch for it.
// ---------------------------------------------------------------------------

const glass = {
  /** **Whether Android draws the glass — no** (the A32 spike, #880, ADR-0210 §7 amended
   *  2026-11-25). `expo-blur`'s Android blur redraws everything behind the dock on the UI thread
   *  whenever anything under it or on it changes, and it added frames over 16.7 ms to a scroll and
   *  to the marker's slide on the A32, against a pass mark of none. So Android's dock is opaque
   *  `surface` with the same shape, rim, hairline, shadow and marker. The iPhone draws the glass
   *  always. Turning this on is a new measurement, not a taste call. */
  android: false,
  /** The blur's strength, `expo-blur`'s `intensity` (1–100): **100**, the brief's *strong blur*.
   *  Picked over Home's dark card and its white rows on the A32 at the product owner's call, who had
   *  no iPhone at hand; it has not been seen on an iPhone (#885). */
  blur: 100,
  /** `shadow.dock` as React Native's `boxShadow`, for a dock that draws the glass — the iPhone's,
   *  and Android's if `android` is ever turned on. Drawn outside the box only, so nothing shows
   *  through the translucent fill (the spike's T3, on Android). On the iPhone it also spares the
   *  dock a shadow worked out from its pixels: iOS's shadow props on a view with no opaque fill take
   *  an off-screen pass whenever the page moves under the blur, which can stop the blur drawing. The
   *  iPhone has not drawn it yet (#885). */
  shadow: [{ offsetX: 0, offsetY: 7, blurRadius: 20, color: 'rgba(11,43,51,0.12)' }],
} as const;

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
  glass,
} as const;

export type Theme = typeof theme;
export type BandKey = keyof typeof band;
export type SportKey = keyof typeof sport;
