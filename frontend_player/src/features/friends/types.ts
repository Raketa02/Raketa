/**
 * The friends feature's only public surface
 * ([#753](https://github.com/Raketa02/Raketa/issues/753), PRD #743;
 * [ADR-0202](../../../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)).
 *
 * **The acts are this feature's; the surfaces are their own.** Members (`groups`) draws its rows and
 * hands each to `RowWithFriendEnd`, which puts the pill or the tag on its right. The record
 * (`player_record`) reads `recordFootOf` and draws `FriendButton` beside `blocks`' Block. The shell
 * composes `FriendRequestsRow` and `LevelAsksRow` into Home above Your games. Each surface hands its
 * own re-read in, so this feature never names another's keys.
 *
 * **You › Friends** (#754) is a frame and a body: `FriendsPage` draws the header, *+ Add friends* and
 * its sheet; `FriendsTabs` is what it holds from You, and the picker (#757) what it holds from a
 * group. **PLAYED WITH** is drawn here and fed by `proposals`, whose booking it lists.
 */

export { RowWithFriendEnd, type RowWithFriendEndProps } from './components/RowWithFriendEnd';

/**
 * **You › Friends and the result's PLAYED WITH** (#754). The shell composes the page — the frame
 * (`FriendsPage`) holding the three tabs (`FriendsTabs`), with `groups`' tiles and Members route
 * handed in as `GroupDoors` and the record a row opens drawn beside it — and puts `FriendsRow` on
 * the You tab. The result route hands `PlayedWithCard` to `proposals`, which builds what it draws
 * off the booking (`PlayedWithInput`, its own shape — `proposals` imports nothing of this feature)
 * and draws it between the score and the star card.
 */
export { FriendsPage, type FriendsPageProps } from './components/FriendsPage';
export { FriendsTabs, type FriendsTabsProps } from './components/FriendsTabs';
export { FriendsRow, type FriendsRowProps } from './components/FriendsRow';
export type { GroupDoors } from './components/AddFriendsSheet';
/**
 * **The Add friends sheet on its own** — your groups and your friend link — for a surface that offers
 * **Add friends** without the Friends page: Rankings' Friends cards (#777). The caller hands in the
 * doors, as the shell does for the page, and draws it as a sibling of its own root.
 */
export { AddFriendsSheet, type AddFriendsSheetProps } from './components/AddFriendsSheet';
/**
 * **The picker** (#757) — the frame's other body, from a group's Friends tab: every friend with
 * their Level in the group's sport, the picks the composer's. `useFriendsIn` is the same read, for
 * the faces the group's court draws once they are seated, so a face is the row it was picked from.
 */
export { FriendsPicker, type FriendsPickerProps } from './components/FriendsPicker';
export { useFriendsIn } from './hooks/useFriendLists';
/**
 * **This feature's reads** — what *Level got* marks stale as it opens the picker (#758): the friend's
 * Level arrived, so the picker's list and every other that names their sports are out of date.
 */
export { friendKeys } from './hooks/friendKeys';
export { levelIn, type Friend } from './domain/friendList';
export { PlayedWithCard, type PlayedWithCardProps } from './components/PlayedWithCard';
export { FriendButton, type FriendButtonProps } from './components/FriendButton';
export { FriendRequestsRow, type FriendRequestsRowProps } from './components/FriendRequestsRow';
/**
 * **ASKED FOR A LEVEL** (#765) — Home's row of a friend's asks for a level, after FRIEND REQUESTS:
 * the shell composes it, handing in the record a face opens, the bell's re-read and the *level
 * asked* notice's toast for a start that failed.
 */
export { LevelAsksRow, type LevelAsksRowProps } from './components/LevelAsksRow';

export {
  recordAskedWhere,
  recordFootOf,
  type AskedWhere,
  type FriendButton as FriendButtonKind,
  type RecordFoot,
} from './domain/friendship';
export type { FriendRelation } from './domain/vocabulary';

/**
 * **A friend link** (#756): its code's shape, which the links feature reads `f/<code>` by, and the
 * opening, which answers the link where the player's app is reached. The card that shows your own
 * link is the Add friends sheet's, inside `FriendsPage`.
 */
export { parseFriendLinkCode } from './schemas/friendLinkCode';
export { useOpenFriendLink } from './hooks/useFriendWrites';

/**
 * The feature's words, exported for the suites that walk Members, the record and Home: a test
 * asserting a sentence it spelled itself passes the day the screen stops saying it.
 */
export {
  FRIENDS_COPY,
  acceptLabel,
  addLabel,
  cancelTitle,
  linkOpeningMessage,
  notNowLabel,
  removeTitle,
  requestsHeading,
  wantsToBeYourFriend,
  whereLine,
} from './components/friendsCopy';
