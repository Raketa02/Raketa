import { WaitingRequests } from '@/features/bookings/components/WaitingRequests';
import type { WaitingRequest } from '@/features/bookings/mappers';
import type { Club } from '@/features/club-details/mappers';
import { RESET_COPY } from '@/features/sign-in/copy';
import { SITE_COPY } from '@/ui/copy';
import { Notice } from '@/ui/Notice';
import { PageHeader } from '@/ui/PageHeader';

import { OVERVIEW_COPY } from '../copy';
import type { Setup } from '../mappers';

import { LiveLine } from './LiveLine';
import { SetupChecklist } from './SetupChecklist';

/**
 * **Overview** (the screens B2): the setup checklist until the club is live; then, once, *You're
 * live*, and after that **only what waits for the club's answer** (the mechanics §16.1). It
 * greets the club by name, and says so when the club has just set a new password, since that is
 * where *Set a new password* lands, or when Stripe's pages could not be opened from a link.
 */
export function Overview({
  club,
  setup,
  requests,
  toldLive,
  passwordSet,
  stripeFailed,
}: {
  club: Club;
  setup: Setup;
  /** What waits for the club's answer: read only once the club is live. */
  requests: readonly WaitingRequest[];
  /** Whether this browser has been told the club is live already. */
  toldLive: boolean;
  passwordSet: boolean;
  /** `/payments/continue` could not open Stripe's pages. */
  stripeFailed: boolean;
}) {
  return (
    <>
      <PageHeader caption={club.name} title={SITE_COPY.frame.pages.overview} />
      {passwordSet ? <Notice tone="success">{RESET_COPY.done}</Notice> : null}
      {stripeFailed ? <Notice tone="error">{OVERVIEW_COPY.stripeFailed}</Notice> : null}
      <LiveLine live={setup.live} told={toldLive} />
      {setup.live ? <WaitingRequests requests={requests} /> : <SetupChecklist setup={setup} />}
    </>
  );
}
