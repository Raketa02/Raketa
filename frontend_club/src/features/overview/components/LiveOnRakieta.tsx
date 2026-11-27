import { ButtonLink } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { SectionHeader } from '@/ui/SectionHeader';

import { OVERVIEW_COPY } from '../copy';

const COPY = OVERVIEW_COPY.liveOnRakieta;

/**
 * **Live on Rakieta** (the screens B2, Q121): what Overview says in the checklist's place once the
 * club is live, with the way to today's Bookings.
 */
export function LiveOnRakieta() {
  return (
    <Card labelledBy="live-on-rakieta-title">
      <SectionHeader
        id="live-on-rakieta-title"
        title={COPY.title}
        lead={COPY.lead}
        aside={<ButtonLink href="/bookings">{COPY.today}</ButtonLink>}
      />
    </Card>
  );
}
