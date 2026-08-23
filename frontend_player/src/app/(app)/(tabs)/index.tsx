/**
 * Now — the app's home, and where onboarding lands.
 *
 * A route file and nothing else: the screen, its four asks and its rules live in
 * the feature. What used to be here was the authenticated placeholder; that screen
 * is genuinely the auth feature's own surface and has moved to `account`, which is
 * the `user` tab the tab bar will reach (`Raketa02/Raketa#93`).
 */

import { NowScreen } from '@/features/now/types';

export default function HomeRoute() {
  return <NowScreen />;
}
