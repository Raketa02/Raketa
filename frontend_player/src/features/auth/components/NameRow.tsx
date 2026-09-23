/**
 * **The *Name* row on the You tab** — the name and the handle as `GET /users/me` holds them,
 * and the door to the naming screen pre-filled
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7).
 *
 * It is this feature's because the act behind it is: `PUT /users/me/name` is the users
 * context's one act on the player, the naming step is this feature's screen, and the line is
 * read off the player this feature reads. The name and the handle are absent only on an
 * account held at the naming step, which never reaches this tab — so the line waits for the
 * read and never draws half a pair.
 */

import { useRouter } from 'expo-router';

import { liveLine } from '@/shared/errors';
import { DoorRow, type DoorRowProps } from '@/shared/ui';

import { useCurrentUser } from '../hooks/useCurrentUser';

import { NAME_ROW_TITLE, nameLine } from './namePresentation';

/** Where the row leads — spelled here, as every feature spells its own `/you/…` address. */
export const YOU_NAME_ROUTE = '/you/name';

/** 5.5's `index > 0` — the shell says where in its card the row sits. */
export type NameRowProps = Pick<DoorRowProps, 'divided'>;

export function NameRow({ divided }: NameRowProps) {
  const router = useRouter();
  const user = useCurrentUser();

  // The pair, or nothing: a name without its handle is not the line, and an account with
  // neither is one the gate never lets this far.
  const named =
    user.data?.name === undefined || user.data.nickname === undefined
      ? undefined
      : { name: user.data.name, nickname: user.data.nickname };

  return (
    <DoorRow
      glyph="user"
      title={NAME_ROW_TITLE}
      line={liveLine({ data: named, error: user.error }, (pair) =>
        nameLine(pair.name, pair.nickname),
      )}
      divided={divided}
      onPress={() => router.push(YOU_NAME_ROUTE)}
    />
  );
}
