/**
 * **The groups feature's only public surface** — Play › Groups, New group, Join a group, a
 * group's page, its Friends screen, Info (Q125), Members and Edit group
 * ([#512](https://github.com/Raketa02/Raketa/issues/512),
 * [#513](https://github.com/Raketa02/Raketa/issues/513),
 * [#514](https://github.com/Raketa02/Raketa/issues/514), PRD #500).
 *
 * The Play tab's segment is the shell's, and it draws `GroupsSection` under *Groups*; the seven
 * screens are mounted by their route files under `play/`, and the page's routes check their params
 * here first. What is exported is what has a caller outside this folder.
 */

export { GroupsSection } from './components/GroupsSection';
export { NewGroupScreen } from './components/NewGroupScreen';
export { JoinGroupScreen } from './components/JoinGroupScreen';
export { GroupScreen } from './components/GroupScreen';
export { FriendsScreen } from './components/FriendsScreen';
export { GroupInfoScreen } from './components/GroupInfoScreen';
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
 * **A rating pass begun on a group returns to it** ([#729](https://github.com/Raketa02/Raketa/issues/729),
 * ADR-0200 §3, §5): the tab the pass began on is this feature's word, and onboarding carries it as
 * the pass's origin; the picker's route reads a group's tab off its params; the result's route names
 * the group; and the app's gate lays the page back down on that tab, on the sport rated last.
 */
export type { GroupTab } from './domain/groupPage';
export { parseGroupPlace } from './schemas/groupRouteParams';
export { useGroupName } from './hooks/useGroups';
export { groupReturnRoute } from './components/groupRoutes';

/**
 * **Home's *Get your level*** ([#731](https://github.com/Raketa02/Raketa/issues/731), ADR-0200 §7):
 * the door where play begins, drawn on Home for a member of a group rated in nothing. The shell
 * places it; whether it is drawn is this feature's rule.
 */
export { HomeLevelCard } from './components/HomeLevelCard';
/** The reads behind it — what a notice opening Home on its card marks stale (#731). */
export { groupKeys } from './hooks/groupKeys';

/**
 * **The home-club search, for a Location area** ([#733](https://github.com/Raketa02/Raketa/issues/733),
 * ADR-0200 §10): a player who refuses the phone's location picks a club near where she plays, from
 * the same search New group's home club uses — by name or district, A–Z with no area yet — drawn
 * as the same card with the caller's own pill. `player_profile` owns what the pick means.
 */
export { useHomeClubSearch, type ClubSearchState } from './hooks/useClubSearch';
export { ClubCard } from './components/ClubCard';
export { clubLine, noClubCalled } from './components/groupsPresentation';
export type { SearchedClub } from './domain/group';

/**
 * **What the administrator area draws with** ([#516](https://github.com/Raketa02/Raketa/issues/516),
 * [#517](https://github.com/Raketa02/Raketa/issues/517)): an official group is a Group, so its tile,
 * its dots, its club's tile, its form cards, its request row, who a switch to Anyone let in, a failed
 * read and the words they share are this feature's, used there rather than drawn twice. The
 * dependency points one way — `administrator` reads `groups`, never the reverse.
 */
export { GroupMonogram } from './components/GroupMonogram';
/**
 * One of the reader's groups' tiles by id — the Add friends sheet's, handed to `friends` by the
 * shell (#754).
 */
export { MyGroupMonogram } from './components/MyGroupMonogram';
/** Members, pushed — where the Add friends sheet lands on a group (#754). */
export { groupMembersRoute } from './components/groupRoutes';
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
