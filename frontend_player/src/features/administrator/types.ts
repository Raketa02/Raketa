/**
 * **The administrator feature's only public surface** — the administrator area: its two tabs,
 * **Groups · You**, New official group, an official group's page and its settings
 * ([#516](https://github.com/Raketa02/Raketa/issues/516),
 * [#517](https://github.com/Raketa02/Raketa/issues/517), PRD #500, ADR-0184, ADR-0185).
 *
 * The screens are mounted by the route files under `src/app/(administrator)/`, which check their
 * params here first; the entry gate reaches for `administratorHome` to send an account that only
 * administers to its area. What is exported is what has a caller outside this folder.
 */

export { AdministratorArea } from './components/AdministratorArea';
export { AdministratorGroupsScreen } from './components/AdministratorGroupsScreen';
export { AdministratorYouScreen } from './components/AdministratorYouScreen';
export { GroupSettingsScreen } from './components/GroupSettingsScreen';
export { NewOfficialGroupScreen } from './components/NewOfficialGroupScreen';
export { OfficialGroupScreen } from './components/OfficialGroupScreen';
export { administratorHome } from './components/administratorRoutes';
export {
  parseClubRouteParams,
  parseOfficialGroupRouteParams,
} from './schemas/administratorRouteParams';
