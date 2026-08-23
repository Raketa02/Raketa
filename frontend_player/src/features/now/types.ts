/**
 * The Now feature's public surface.
 *
 * The result route imports this vocabulary rather than promoting it to
 * `shared/` (`ADR-0075`): the situation vocabulary is Now's, and one
 * cross-feature import is cheaper than inviting the club console's table to land
 * beside it later. A **third** reader is the signal to promote.
 *
 * Nothing else in this feature is public. A screen reaches the tables through
 * here, and never through a deep import — ESLint blocks the deep import anyway.
 *
 * `NowScreen` is the screen `src/app/(app)/(tabs)/index.tsx` renders, and
 * `nowKeys` is how an action elsewhere reaches it — `ADR-0054`'s third ask. The
 * hooks, the store and the regions are internal: a caller that wanted one of them
 * would be building a second Now.
 *
 * Three things below are exported **for the departure route** (`Raketa02/Raketa#91`),
 * and each is here because the alternative was a second copy of something this
 * feature owns:
 *
 * - `writeNowUpdate` and `toNowUpdate` — `ADR-0074`'s update, applied. Where a
 *   card sits on Now is Now's knowledge and nobody else's, so an action hands the
 *   update over rather than reaching into the cache with its own opinion.
 *   `applyNowUpdate`, the pure half, stays internal: it is the rule about *where a
 *   card goes*, and it has no reader outside this feature.
 * - the countdown — `ADR-0053` leaves the phone **one** derivation, and a second
 *   screen subtracting its own moments would be a second place it lives. The
 *   *timer* is not exported: a repaint cadence belongs to the screen that arms it,
 *   and `NowClockProvider` is shaped around a composed screen.
 *
 * The leaver's own line is **not** here. It is resolved into the card during a
 * compose, like every other sentence, so a card arrives already saying what it
 * says and no caller can resolve it a second way.
 */

export type {
  ActCopy,
  ActSurface,
  Audience,
  DoorCopy,
  FindClaim,
  ShelfCopy,
  SituationCopy,
  Tag,
  Tone,
} from './domain/presentation';

export type {
  ActCode,
  CaptionCode,
  CardHoldReason,
  Cause,
  DoorCode,
  FitReason,
  HoldNote,
  ShelfCode,
  Situation,
  SituationFacts,
  SportFilter,
  TermCode,
} from './mappers/codes';

export { ACT_COPY, actCopy, type ActContext, type ActEntry } from './mappers/acts';
export { CAPTION_COPY, captionCopy } from './mappers/captions';
export {
  FIT_BADGE_WITHHELD,
  FIT_REASON_COPY,
  FIT_UNSURE_WARNING,
  fitReasonSentence,
  type FitReasonEntry,
} from './mappers/fitReasons';
export { HOLD_REASON_COPY, holdReasonClause, type HoldReasonEntry } from './mappers/holdReasons';
export { SHELF_COPY, findPreFilter, shelfTitle, type FindPreFilter } from './mappers/shelves';
export {
  SITUATION_COPY,
  situationCopy,
  type SituationContext,
  type SituationEntry,
} from './mappers/situations';

export { NowScreen } from './components/NowScreen';
export { nowKeys } from './hooks/nowKeys';

export type {
  Block,
  ClubCard,
  ComposedScreen,
  Cover,
  DebtLine,
  Door,
  EnrolledRegion,
  MatchCard,
  Moment,
  NowCard,
  NowUpdate,
  OffersRegion,
  PersonCard,
  Place,
  Shelf,
  ShelvesRegion,
} from './domain/ComposedScreen';

/**
 * The one derivation this client is allowed, and the cadence that repaints it.
 *
 * `ADR-0053` gives the phone exactly one — subtracting a moment it was handed
 * from the current time — and `domain/countdown.ts` is the whole of it. A second
 * screen that counted down would otherwise hold a second `Date.parse` and, in
 * time, a second format: `4:37` here and `4 min 37 s` there, on two screens about
 * the same deadline.
 */
export { SECONDS_BAND_MS, countdownLabel, remainingMs, repaintDelayMs } from './domain/countdown';

export { toNowUpdate } from './mappers/nowMappers';
export { writeNowUpdate } from './hooks/writeNowUpdate';

export { DEFAULT_SPORT_FILTER, SPORT_BAR, SPORT_CHIP_COPY } from './mappers/sportBar';
export { DOOR_COPY, doorCopy, type DoorContext, type DoorEntry } from './mappers/doors';

/**
 * The chip a questionnaire begun at Now's door lands back on (`ADR-0084`).
 *
 * The one write another feature may make to this screen. See the store for why
 * it is a function rather than the store itself.
 */
export { selectSportFilter } from './store/sportFilter.store';
