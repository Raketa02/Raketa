import type { Metadata } from 'next';

import { CheckIn } from '@/features/check-in/components/CheckIn';
import { CHECK_IN_COPY } from '@/features/check-in/copy';
import { getWayAndSettings } from '@/features/raketa-settings/queries';

export const metadata: Metadata = { title: CHECK_IN_COPY.title };

/** **Check in** (the screens B6): the desk, while the club's settings say it checks players in. */
export default async function CheckInPage() {
  const settings = await getWayAndSettings();
  return <CheckIn checksIn={settings.checkIn} />;
}
