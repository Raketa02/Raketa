import { DETAILS_COPY } from '@/features/club-details/copy';
import type { Club } from '@/features/club-details/mappers';
import { RESET_COPY } from '@/features/sign-in/copy';
import { ButtonLink } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { SITE_COPY } from '@/ui/copy';
import { Notice } from '@/ui/Notice';
import { PageHeader } from '@/ui/PageHeader';

import { OVERVIEW_COPY } from '../copy';

import styles from './Overview.module.css';

/**
 * **Overview**: empty for now (#522). It greets the club by name, and says so when the club has
 * just set a new password, since that is where *Set a new password* lands.
 */
export function Overview({ club, passwordSet }: { club: Club; passwordSet: boolean }) {
  return (
    <>
      <PageHeader caption={club.name} title={SITE_COPY.frame.pages.overview} />
      {passwordSet ? <Notice tone="success">{RESET_COPY.done}</Notice> : null}
      <Card>
        <p className={styles.empty}>{OVERVIEW_COPY.empty}</p>
        <div>
          <ButtonLink href="/details">{DETAILS_COPY.title}</ButtonLink>
        </div>
      </Card>
    </>
  );
}
