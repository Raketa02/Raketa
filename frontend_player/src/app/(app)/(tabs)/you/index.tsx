import { YouScreen } from '@/features/shell/types';

/**
 * **You** — the tab's root, composed by the shell
 * ([ADR-0179](../../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)).
 * A directory rather than a file since the tab grew screens: every row's screen is pushed over
 * this one under the same first segment, so the You column stays lit.
 */
export default function YouRoute() {
  return <YouScreen />;
}
