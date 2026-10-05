/**
 * **The groups feature's only public surface** — Play › Groups, New group, Join a group, a
 * group's page, its Friends screen, Members and Edit group
 * ([#512](https://github.com/Raketa02/Raketa/issues/512),
 * [#513](https://github.com/Raketa02/Raketa/issues/513),
 * [#514](https://github.com/Raketa02/Raketa/issues/514), PRD #500).
 *
 * The Play tab's segment is the shell's, and it draws `GroupsSection` under *Groups*; the six
 * screens are mounted by their route files under `play/`, and the page's routes check their params
 * here first. What is exported is what has a caller outside this folder.
 */

export { GroupsSection } from './components/GroupsSection';
export { NewGroupScreen } from './components/NewGroupScreen';
export { JoinGroupScreen } from './components/JoinGroupScreen';
export { GroupScreen } from './components/GroupScreen';
export { FriendsScreen } from './components/FriendsScreen';
export { MembersScreen } from './components/MembersScreen';
export { EditGroupScreen } from './components/EditGroupScreen';
/** ***Post a game*** over a group's page (#558) — `proposals`' screen, handed what the group knows. */
export { PostAGamePage } from './components/PostAGamePage';
export {
  parseFriendsRouteParams,
  parseGroupRouteParams,
  parseJoinRouteParams,
} from './schemas/groupRouteParams';
/**
 * **Join a group, opened by a group link** ([#520](https://github.com/Raketa02/Raketa/issues/520)):
 * where the links feature sends a link it has read, with the code the screen fills its field with.
 */
export { joinGroupRouteFor } from './components/groupRoutes';
/**
 * **A group's deck, opened at a card** ([#559](https://github.com/Raketa02/Raketa/issues/559)): where
 * the notifications feature sends a notice about a card waiting for the player — the page on Games,
 * in the card's sport and kind, the card first.
 */
export { groupDeckRoute } from './components/groupRoutes';
export type { DeckArrival } from './schemas/groupRouteParams';

/**
 * **What the administrator area draws with** ([#516](https://github.com/Raketa02/Raketa/issues/516),
 * [#517](https://github.com/Raketa02/Raketa/issues/517)): an official group is a Group, so its tile,
 * its dots, its club's tile, its form cards, its request row, who a switch to Anyone let in, a failed
 * read and the words they share are this feature's, used there rather than drawn twice. The
 * dependency points one way — `administrator` reads `groups`, never the reverse.
 */
export { GroupMonogram } from './components/GroupMonogram';
export { ClubTile } from './components/ClubTile';
export { SportDots } from './components/SportDots';
export { GroupNameCard, WhoCanJoinCard } from './components/GroupFormCards';
export { RequestRow } from './components/RequestRow';
export { AdmittedCard } from './components/AdmittedCard';
export { OpenToAnyoneSheet } from './components/OpenToAnyoneSheet';
export { FaceStack } from './components/FaceStack';
/** A pull's spinner — the Groups tab and a group's page pull as the player's do (#529). */
export { usePull } from './hooks/usePull';
/** Members, as an official group's Administrator opens it from the members card (#529). */
export { AdministeredMembersScreen } from './components/MembersScreen';
export { ReadFailure } from './components/ReadFailure';
export { ROW_FACE } from './components/peopleRow';
export { GROUPS_COPY } from './components/groupsCopy';
export {
  linkLabel,
  linkShown,
  membersLine,
  personName,
  shareMessage,
  wantToJoin,
} from './components/groupsPresentation';
export { GroupNameSchema, JoinPolicySchema } from './schemas/newGroupForm';
export {
  GROUP_NAME_MAX,
  type GroupPerson,
  type JoinRequest,
  type Monogram,
  type SportLevel,
} from './domain/group';
export type { JoinPolicy } from './domain/vocabulary';
