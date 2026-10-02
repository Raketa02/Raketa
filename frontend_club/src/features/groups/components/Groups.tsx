import type { RaketaSettings } from '@/features/raketa-settings/mappers';
import { Card } from '@/ui/Card';
import { SITE_COPY } from '@/ui/copy';
import { PageHeader } from '@/ui/PageHeader';
import { TextLink } from '@/ui/TextLink';

import { GROUPS_COPY as COPY } from '../copy';
import type { GroupRow } from '../mappers';

import styles from './Groups.module.css';
import { GroupsTable } from './GroupsTable';

/** Where the setting is: Raketa settings, at *Offer our groups other clubs' courts*. */
const OTHER_CLUBS_SETTING = '/raketa-settings#other-clubs';

/**
 * **Groups** (#500 stories 105–107, the screens B8): the club's official groups, which its
 * administrators make in the app, so there is nothing to create here; over the table, whether
 * they are offered other clubs' courts when the club's are full, and the way to the setting.
 * Before the first group, the page says so.
 */
export function Groups({
  club,
  groups,
  otherClubs,
}: {
  club: string;
  groups: readonly GroupRow[];
  otherClubs: RaketaSettings['otherClubs'];
}) {
  const other = COPY.otherClubs;
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
        <>
          <p className={styles.otherClubs}>
            {other.lead(otherClubs.offered, otherClubs.withinKm)}{' '}
            <TextLink href={OTHER_CLUBS_SETTING}>{other.settings}</TextLink>
            {other.end}
          </p>
          <GroupsTable groups={groups} />
        </>
      )}
    </>
  );
}
