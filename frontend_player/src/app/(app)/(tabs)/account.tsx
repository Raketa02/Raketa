/**
 * The account screen — the `user` tab.
 *
 * It moved off `index` when Now became the home screen. **Nothing navigates here
 * yet**, and that is stated rather than hidden: the tab bar is
 * `Raketa02/Raketa#93` and is what reaches it. Keeping the route means sign-out is
 * addressable rather than deleted, which is the only way back to the beginning.
 */

import { AccountScreen } from '@/features/auth/types';

export default function AccountRoute() {
  return <AccountScreen />;
}
