/**
 * The player record feature's only public surface.
 *
 * `src/app/` and other features import from here and from nowhere else inside this folder —
 * ESLint blocks the deep paths.
 *
 * **`features/play/` imports `PlayerRecordSheet` and nothing else**, which is the same seam
 * `challenges` already has with the builder's send: the surface composes and the feature owns
 * the act. The arrow runs one way — Play is what opens this sheet — which is why the drawing it
 * shares with the candidate card (the photo panel, the run of form, the Social tag row) lives
 * in `shared/ui` rather than being imported sideways.
 */

export { PlayerRecordSheet, type PlayerRecordSheetProps } from './components/PlayerRecordSheet';

export type { PlayerRecord, RatedSport, RecordSubject, SkillPanel } from './domain/playerRecord';

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
 * walk reads: the two titles, the close control's name, the pairing row's spoken name, and the
 * one line a record that cannot be opened draws.
 */
export {
  OWN_RECORD_TITLE,
  RECORD_TITLE,
  RECORD_UNAVAILABLE,
  fitRowLabel,
  recordCloseLabel,
} from './components/recordPresentation';
