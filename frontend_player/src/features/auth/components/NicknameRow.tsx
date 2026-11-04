/**
 * **The *Nickname* row on the You tab** — the nickname as `GET /users/me` holds it, and the door
 * to the naming screen pre-filled
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7; [ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3).
 *
 * It is this feature's because the act behind it is: `PUT /users/me/name` is the users
 * context's one act on the player, the naming step is this feature's screen, and the line is
 * read off the player this feature reads. The nickname is absent only on an account held at the
 * naming step, which never reaches this tab — so the line waits for the read.
 *
 * **The route keeps the word *name***, as the act's path does: `/you/name` is what a player is
 * called, which is the nickname (ADR-0199, *Neutral*).
 */

import { useRouter } from 'expo-router';

import { liveLine } from '@/shared/errors';
import { DoorRow, type DoorRowProps } from '@/shared/ui';

import { useCurrentUser } from '../hooks/useCurrentUser';

import { NICKNAME_ROW_TITLE } from './nicknamePresentation';

/** Where the row leads — spelled here, as every feature spells its own `/you/…` address. */
export const YOU_NICKNAME_ROUTE = '/you/name';

/** 5.5's `index > 0` — the shell says where in its card the row sits. */
export type NicknameRowProps = Pick<DoorRowProps, 'divided'>;

export function NicknameRow({ divided }: NicknameRowProps) {
  const router = useRouter();
  const user = useCurrentUser();

  return (
    <DoorRow
      glyph="user"
      title={NICKNAME_ROW_TITLE}
      line={liveLine({ data: user.data?.nickname, error: user.error }, (nickname) => nickname)}
      divided={divided}
      onPress={() => router.push(YOU_NICKNAME_ROUTE)}
    />
  );
}
