/**
 * **The notices' workflows** (#559) — pass-throughs, the uniform-strict escape hatch, for every read
 * and write: the choices are the server's to keep, a phone is the server's to push, and the list is
 * the server's words. The one rule is where a pushed payload opens, which is the schema's check and
 * the domain's answer, composed here.
 */

import {
  getChoices,
  getNotices,
  postDevice,
  putChoices,
  type Cancellable,
} from '../api/notificationsApi';
import type { NotificationChoices } from '../domain/choices';
import type { Notice, NoticeTarget } from '../domain/notice';
import { toChoices, toChoicesRequest, toNotice, toTarget } from '../mappers/notificationMappers';
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

export async function readNotices(options: Cancellable = {}): Promise<readonly Notice[]> {
  return (await getNotices(options)).notices.map(toNotice);
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
