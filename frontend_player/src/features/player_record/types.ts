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

export type {
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
 * The sheet's own words, exported for its suite.
 *
 * A test asserting a sentence it has spelled itself is a test that passes the day the sentence
 * changes and the screen stops saying what it meant — `findAGamePresentation`'s rule, and the
 * one every copy deck in this app is read through. What is exported is what the **builder's**
 * walk reads: the two titles, the close control's name, the pairing row's spoken name, the one
 * line a record that cannot be opened draws, the one clause a client is licensed to write from
 * two area codes — which the walk asserts is **absent** from your own record — and the record
 * card's heading with the two figures it prints.
 */
export {
  IN_YOUR_AREA,
  OWN_RECORD_TITLE,
  YOU_MARK,
  RECORD_CARD_TITLE_DRAWN,
  RECORD_TITLE,
  PLAYER_SCORE_NAME,
  RECORD_UNAVAILABLE,
  STRAND_NAME,
  fitRowLabel,
  recordCloseLabel,
  strandFraction,
  varietyValue,
} from './components/recordPresentation';
