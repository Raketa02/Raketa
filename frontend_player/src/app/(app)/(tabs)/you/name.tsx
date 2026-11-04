import { NicknameScreen } from '@/features/auth/types';

/**
 * *Nickname* — the naming, pre-filled, pushed over the You tab; `features/auth`'s own screen. The
 * path keeps the word *name*, as `PUT /users/me/name` does (ADR-0199, *Neutral*).
 */
export default function NicknameRoute() {
  return <NicknameScreen />;
}
