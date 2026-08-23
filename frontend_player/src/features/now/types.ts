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
  OffersRegion,
  PersonCard,
  Place,
  Shelf,
  ShelvesRegion,
} from './domain/ComposedScreen';

export { DEFAULT_SPORT_FILTER, SPORT_BAR, SPORT_CHIP_COPY } from './mappers/sportBar';
export { DOOR_COPY, doorCopy, type DoorContext, type DoorEntry } from './mappers/doors';

/**
 * The chip a questionnaire begun at Now's door lands back on (`ADR-0084`).
 *
 * The one write another feature may make to this screen. See the store for why
 * it is a function rather than the store itself.
 */
export { selectSportFilter } from './store/sportFilter.store';
