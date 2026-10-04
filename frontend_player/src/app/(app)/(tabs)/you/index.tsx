import { ProfileChip } from '@/features/administrator/types';
import { PLAYER_PROFILE } from '@/features/auth/types';
import { YouScreen } from '@/features/shell/types';

/**
 * **You** — the tab's root, composed by the shell
 * ([ADR-0179](../../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)).
 * A directory rather than a file since the tab grew screens: every row's screen is pushed over
 * this one under the same first segment, so the You column stays lit.
 *
 * **The header carries the profile switcher's chip** (#518, club 7), which this file composes: it is
 * the administrator feature's, and the shell reading it would close an import cycle through `auth`.
 * It draws nothing for an account with one profile.
 */
export default function YouRoute() {
  return <YouScreen headerRight={<ProfileChip worn={PLAYER_PROFILE} />} />;
}
