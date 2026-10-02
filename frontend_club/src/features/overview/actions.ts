'use server';

import { saveToldLive } from '@/server/marks';

/**
 * **Overview said *You're live***, or the club is not live any more: remember which, in this
 * browser, so the line is said once each time the club goes live.
 */
export async function noteToldLive(told: boolean): Promise<void> {
  await saveToldLive(told === true);
}
