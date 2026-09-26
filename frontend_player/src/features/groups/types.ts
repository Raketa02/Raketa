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
 * **What the administrator area draws with** ([#516](https://github.com/Raketa02/Raketa/issues/516),
 * [#517](https://github.com/Raketa02/Raketa/issues/517)): an official group is a Group, so its tile,
 * its dots, its form cards, its request row, who a switch to Anyone let in, a failed read and the
 * words they share are this feature's, used there rather than drawn twice. The
 * dependency points one way — `administrator` reads `groups`, never the reverse.
 */
export { GroupMonogram } from './components/GroupMonogram';
export { SportDots } from './components/SportDots';
export { GroupNameCard, WhoCanJoinCard } from './components/GroupFormCards';
export { RequestRow } from './components/RequestRow';
export { AdmittedCard } from './components/AdmittedCard';
export { FaceStack } from './components/FaceStack';
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
