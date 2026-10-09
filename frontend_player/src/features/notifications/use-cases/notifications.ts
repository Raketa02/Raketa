/**
 * **The notices' workflows** (#559) — pass-throughs, the uniform-strict escape hatch, for every read
 * and write: the choices are the server's to keep, a phone is the server's to push, the list is the
 * server's words, and what counts as seen is the server's to keep (#627). The one rule is where a
 * pushed payload opens, which is the schema's check and the domain's answer, composed here.
 */

import {
  getChoices,
  getNotices,
  postDevice,
  postVisit,
  putChoices,
  type Cancellable,
} from '../api/notificationsApi';
import type { NotificationChoices } from '../domain/choices';
import type { NoticeTarget, RecentNotices } from '../domain/notice';
import {
  toChoices,
  toChoicesRequest,
  toRecentNotices,
  toTarget,
} from '../mappers/notificationMappers';
import { parsePushNotice } from '../schemas/pushNotice';

export async function readChoices(options: Cancellable = {}): Promise<NotificationChoices> {
  return toChoices(await getChoices(options));
}

/** Save all three. Answers what is now saved. */
export async function saveChoices(choices: NotificationChoices): Promise<NotificationChoices> {
  return toChoices(await putChoices(toChoicesRequest(choices)));
}

/** Push this phone every notice given to the signed-in player. */
export function registerPhone(token: string): Promise<void> {
  return postDevice({ token });
}

/** The list behind the bell, newest first, and the bell's number. */
export async function readNotices(options: Cancellable = {}): Promise<RecentNotices> {
  return toRecentNotices(await getNotices(options));
}

/** The list was opened: what it holds by now is seen, and the bell is nought (Q101). */
export function recordVisit(): Promise<void> {
  return postVisit();
}

/** A pushed notice, read: its id, and where it opens — when it opens anywhere this build can name. */
export interface PushRead {
  readonly noticeId: string;
  readonly target?: NoticeTarget;
}

/** The push's notice — `undefined` for a payload that is not a notice's. */
export function noticeOfPush(data: unknown): PushRead | undefined {
  const pushed = parsePushNotice(data);
  if (pushed === undefined) return undefined;
  const target = toTarget(pushed);
  return { noticeId: pushed.noticeId, ...(target === undefined ? {} : { target }) };
}
