/**
 * The friends feature's only public surface
 * ([#753](https://github.com/Raketa02/Raketa/issues/753), PRD #743;
 * [ADR-0202](../../../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)).
 *
 * **The acts are this feature's; the surfaces are their own.** Members (`groups`) draws its rows and
 * hands each to `RowWithFriendEnd`, which puts the pill or the tag on its right. The record
 * (`player_record`) reads `recordFootOf` and draws `FriendButton` beside `blocks`' Block. The shell
 * composes `FriendRequestsRow` into Home above Your games. Each surface hands its own re-read in, so
 * this feature never names another's keys.
 */

export { RowWithFriendEnd, type RowWithFriendEndProps } from './components/RowWithFriendEnd';
export { FriendButton, type FriendButtonProps } from './components/FriendButton';
export { FriendRequestsRow, type FriendRequestsRowProps } from './components/FriendRequestsRow';

export {
  recordFootOf,
  type AskedWhere,
  type FriendButton as FriendButtonKind,
  type RecordFoot,
} from './domain/friendship';
export type { FriendRelation } from './domain/vocabulary';

/**
 * The feature's words, exported for the suites that walk Members, the record and Home: a test
 * asserting a sentence it spelled itself passes the day the screen stops saying it.
 */
export {
  FRIENDS_COPY,
  acceptLabel,
  addLabel,
  cancelTitle,
  notNowLabel,
  removeTitle,
  requestsHeading,
  wantsToBeYourFriend,
  whereLine,
} from './components/friendsCopy';
