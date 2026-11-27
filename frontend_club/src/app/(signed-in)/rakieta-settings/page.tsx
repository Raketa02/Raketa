import type { Metadata } from 'next';

import { RakietaSettingsForm } from '@/features/rakieta-settings/components/RakietaSettingsForm';
import { SETTINGS_COPY } from '@/features/rakieta-settings/copy';
import { getSettingsPage } from '@/features/rakieta-settings/queries';
import { PageHeader } from '@/ui/PageHeader';

export const metadata: Metadata = { title: SETTINGS_COPY.title };

export default async function RakietaSettingsPage() {
  const { settings, confirmed } = await getSettingsPage();
  return (
    <>
      <PageHeader caption={SETTINGS_COPY.caption} title={SETTINGS_COPY.title} />
      <RakietaSettingsForm settings={settings} confirmed={confirmed} />
    </>
  );
}
