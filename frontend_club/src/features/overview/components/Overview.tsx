import type { Club } from '@/features/club-details/mappers';
import { RESET_COPY } from '@/features/sign-in/copy';
import { Card } from '@/ui/Card';
import { SITE_COPY } from '@/ui/copy';
import { Notice } from '@/ui/Notice';
import { PageHeader } from '@/ui/PageHeader';

import { OVERVIEW_COPY } from '../copy';
import type { Setup } from '../mappers';

import { LiveLine } from './LiveLine';
import styles from './Overview.module.css';
import { SetupChecklist } from './SetupChecklist';

/**
 * **Overview** (the screens B2): the setup checklist until the club is live; then, once, *You're
 * live*, and nothing else yet: what waits for the club's answer arrives with Bookings (#563). It
 * greets the club by name, and says so when the club has just set a new password, since that is
 * where *Set a new password* lands.
 */
export function Overview({
  club,
  setup,
  toldLive,
  passwordSet,
}: {
  club: Club;
  setup: Setup;
  /** Whether this browser has been told the club is live already. */
  toldLive: boolean;
  passwordSet: boolean;
}) {
  return (
    <>
      <PageHeader caption={club.name} title={SITE_COPY.frame.pages.overview} />
      {passwordSet ? <Notice tone="success">{RESET_COPY.done}</Notice> : null}
      <LiveLine live={setup.live} told={toldLive} />
      {setup.live ? (
        <Card>
          <p className={styles.empty}>{OVERVIEW_COPY.empty}</p>
        </Card>
      ) : (
        <SetupChecklist setup={setup} />
      )}
    </>
  );
}
