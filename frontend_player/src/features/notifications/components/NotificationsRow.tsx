/**
 * **Notifications, on the You tab** — the ACCOUNT group's third row, under *Payments*: its title, the
 * choices that are on in one line, and the door to the screen (#559; the screens A7; mock 50).
 *
 * *You complete it · Challenges · Fill in alerts* — the three chosen notices that are on, in the
 * screen's order, off the screen's own read, so a tap there is on the row the moment the player
 * comes back. With none on, the ones always on are what is left, and the line says so.
 */

import { useRouter } from 'expo-router';

import { liveLine } from '@/shared/errors';
import { DoorRow, type DoorRowProps } from '@/shared/ui';

import { choicesOn } from '../domain/choices';
import { useNotificationChoices } from '../hooks/useNotificationChoices';

import { YOU_NOTIFICATIONS_ROUTE } from './noticeRoutes';
import { NOTIFICATIONS_TITLE, notificationsRowLine } from './notificationsCopy';

export type NotificationsRowProps = Pick<DoorRowProps, 'divided'>;

export function NotificationsRow({ divided }: NotificationsRowProps) {
  const router = useRouter();
  const read = useNotificationChoices();

  return (
    <DoorRow
      glyph="bell"
      title={NOTIFICATIONS_TITLE}
      line={liveLine(read, (choices) => notificationsRowLine(choicesOn(choices)))}
      divided={divided}
      onPress={() => router.push(YOU_NOTIFICATIONS_ROUTE)}
    />
  );
}
