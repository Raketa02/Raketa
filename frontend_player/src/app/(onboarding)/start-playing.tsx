import { StartPlayingScreen } from '@/features/auth/types';

/**
 * ***Start playing*'s first step, the Adult attestation** (ADR-0185 §3–§5), where the entry gate
 * sends an account that holds no profile at all. Under `(onboarding)` for the naming's reason: the
 * gate redirects into it. The administrator's You tab pushes the same screen inside its own area.
 */
export default function StartPlayingRoute() {
  return <StartPlayingScreen />;
}
