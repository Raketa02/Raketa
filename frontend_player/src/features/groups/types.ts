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
export { parseFriendsRouteParams, parseGroupRouteParams } from './schemas/groupRouteParams';
