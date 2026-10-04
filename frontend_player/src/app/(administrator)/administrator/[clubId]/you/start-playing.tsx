import { StartPlayingScreen } from '@/features/auth/types';

/**
 * ***Start playing*'s first step, pushed over the You tab** — `auth`'s screen at its second address
 * (the other is `(onboarding)/start-playing`, where the entry gate sends an account that holds no
 * profile at all). Inside the area's own stack, under the tab's segment, so *back* is the You tab:
 * the root is a `Slot`, and a push out of the area would unmount it and lose the stack under it.
 */
export default function AdministratorStartPlayingRoute() {
  return <StartPlayingScreen />;
}
