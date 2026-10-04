/**
 * The player record feature's only public surface.
 *
 * `src/app/` and other features import from here and from nowhere else inside this folder —
 * ESLint blocks the deep paths.
 *
 * **`features/play/` imports the sheet and the one type that addresses it**, and nothing else:
 * `PlayerRecordSheet`, and `RecordSubject`, which is what a seat carries to say whose record it
 * opens and through which of the two routes. That is the same seam `challenges` already has with
 * the builder's send — the surface composes and the feature owns the act. The arrow runs one
 * way, Play being what opens this sheet, which is why the drawing it shares with the candidate
 * card (the photo panel, the run of form, the Social tag row) lives in `shared/ui` rather than
 * being imported sideways.
 */

export { PlayerRecordSheet, type PlayerRecordSheetProps } from './components/PlayerRecordSheet';

/**
 * **A Player Score drawn as a tag**, for Members' rows in `groups` — the one surface that tints
 * the figure itself. The tint is `scoreBand`'s, which this feature owns beside the ladder it
 * refines, so a group's list and the record it opens cannot band one number two ways.
 */
export { PlayerScoreTag, type PlayerScoreTagProps } from './components/PlayerScoreTag';

export type {
  Opinion,
  OpponentVariety,
  PlayerRecord,
  RatedSport,
  RecordSubject,
  Reliability,
  ReliabilityStrand,
  SkillPanel,
  StrandRow,
} from './domain/playerRecord';

/**
 * The record's query keys, exported for the one thing outside this feature that needs them:
 * clearing the cache. Nothing else reaches for a key it did not mint.
 */
export { playerRecordKeys } from './hooks/playerRecordKeys';

/**
 * **The reader's own face**, for the yes screen
 * ([ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §3): the photograph off their own record, or nothing, and whether the read is in. The one
 * surface that draws the reader as a tile rather than as a seat, and the one read `challenges`
 * makes of this feature — a new edge, held open by `scripts/test-import-boundaries.sh`. A URL
 * crosses and nothing else about the record does.
 */
export { useOwnFace, type OwnFace } from './hooks/useOwnFace';

/**
 * **This feature on the You tab**
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1–§2): the header card that summarises your own record and opens it, the sheet it opens,
 * the two rows a player cannot change and the door to the sheet, and the two read-only screens
 * behind those rows — the passport, which is the result card once per rating with the record's
 * blocks under each, and reliability, which is the record card under a ring. The shell composes
 * the tab and holds whether the sheet is up; the route files under `(app)/(tabs)/you/` mount
 * the screens. The words are exported for the suites that hold the tab to them.
 */
export { YouHeaderCard, type YouHeaderCardProps } from './components/YouHeaderCard';
export { OwnRecordSheet, type OwnRecordSheetProps } from './components/OwnRecordSheet';
export {
  HowOthersSeeYouRow,
  PlayerReliabilityRow,
  SkillPassportRow,
  type HowOthersSeeYouRowProps,
  type YouRowProps,
} from './components/YouRows';
export { SkillPassportScreen } from './components/SkillPassportScreen';
export { PlayerReliabilityScreen } from './components/PlayerReliabilityScreen';

/**
 * **Where the passport is**, for the one caller outside this feature that lands on it: the
 * entry gate's route file, which puts a pass begun at *Add a sport* back on the passport as
 * the pass ends ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3). The same seam `NAMING_STEP` and `SOCIAL_STEPS_ENTRY` cross: the feature that owns the
 * screen spells its address, and the route file turns a decision into it.
 */
export { YOU_PASSPORT_ROUTE } from './components/youRecordRoutes';
export {
  ADD_A_SPORT,
  HOW_OTHERS_SEE_YOU_LINE,
  HOW_OTHERS_SEE_YOU_TITLE,
  NOTHING_COUNTED,
  OUT_OF_100,
  PLAYER_RELIABILITY_TITLE,
  SCORE_LABEL,
  SCORE_TONE_WORD,
  SKILL_PASSPORT_TITLE,
  THE_LADDER,
  passportLine,
  rateSportChip,
  reliabilityLine,
  scoreRingLabel,
} from './components/youRecordPresentation';

/**
 * The sheet's own words, exported for its suite.
 *
 * A test asserting a sentence it has spelled itself is a test that passes the day the sentence
 * changes and the screen stops saying what it meant — `findAGamePresentation`'s rule, and the
 * one every copy deck in this app is read through. What is exported is what the **builder's**
 * walk reads: the two titles, the close control's name, the pairing row's spoken name, the one
 * line a record that cannot be opened draws, the one clause a client is licensed to write from
 * two area codes — which the walk asserts is **absent** from your own record — the record
 * card's heading with the two figures it prints, and the sportsmanship row's label with the
 * figure it draws for everybody. The three band words it used to draw for the subject are
 * exported by nothing, because nothing draws them
 * ([#473](https://github.com/Raketa02/Raketa/issues/473)).
 */
export {
  IN_YOUR_AREA,
  OWN_RECORD_TITLE,
  YOU_MARK,
  RECORD_TITLE,
  FIT_ROW_NAME,
  FULL_RECORD,
  fitRowLabel,
  PLAYER_SCORE_BLOCK,
  RECORD_UNAVAILABLE,
  SPORTSMANSHIP_LABEL,
  STRAND_NAME,
  opinionFigure,
  recordCloseLabel,
  strandFraction,
  varietyValue,
} from './components/recordPresentation';
