import { Card } from '@/ui/Card';
import { SITE_COPY } from '@/ui/copy';
import { PageHeader } from '@/ui/PageHeader';

import { GROUPS_COPY as COPY } from '../copy';
import type { GroupRow } from '../mappers';

import styles from './Groups.module.css';
import { GroupsTable } from './GroupsTable';

/**
 * **Groups** (#500 stories 105–107): the club's official groups, which its administrators make
 * in the app, so there is nothing to create here. Before the first, the page says so.
 */
export function Groups({ club, groups }: { club: string; groups: readonly GroupRow[] }) {
  return (
    <>
      <PageHeader
        caption={COPY.caption(club)}
        title={SITE_COPY.frame.pages.groups}
        aside={<p className={styles.madeInTheApp}>{COPY.madeInTheApp}</p>}
      />
      {groups.length === 0 ? (
        <Card>
          <p>{COPY.none}</p>
        </Card>
      ) : (
        <GroupsTable groups={groups} />
      )}
    </>
  );
}
