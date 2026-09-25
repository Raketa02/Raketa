/**
 * **The groups feature's only public surface** — Play › Groups, New group, Join a group and a
 * group's page ([#512](https://github.com/Raketa02/Raketa/issues/512), PRD #500).
 *
 * The Play tab's segment is the shell's, and it draws `GroupsSection` under *Groups*; the three
 * screens are mounted by their route files under `play/`, and the page's route checks its id
 * here first. What is exported is what has a caller outside this folder.
 */

export { GroupsSection } from './components/GroupsSection';
export { NewGroupScreen } from './components/NewGroupScreen';
export { JoinGroupScreen } from './components/JoinGroupScreen';
export { GroupScreen } from './components/GroupScreen';
export { parseGroupRouteParams } from './schemas/groupRouteParams';
