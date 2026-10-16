import { ButtonLink } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { SectionHeader } from '@/ui/SectionHeader';

import { OVERVIEW_COPY } from '../copy';

const COPY = OVERVIEW_COPY.liveOnRaketa;

/**
 * **Live on Raketa** (the screens B2, Q121): what Overview says in the checklist's place once the
 * club is live, with the way to today's Bookings.
 */
export function LiveOnRaketa() {
  return (
    <Card labelledBy="live-on-raketa-title">
      <SectionHeader
        id="live-on-raketa-title"
        title={COPY.title}
        lead={COPY.lead}
        aside={<ButtonLink href="/bookings">{COPY.today}</ButtonLink>}
      />
    </Card>
  );
}
