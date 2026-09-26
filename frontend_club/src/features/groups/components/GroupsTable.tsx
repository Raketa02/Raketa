'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';

import { Bar } from '@/ui/Bar';
import { Card } from '@/ui/Card';
import tableStyles from '@/ui/Table.module.css';
import { Tag } from '@/ui/Tag';

import { GROUPS_COPY as COPY } from '../copy';
import type { GroupRow } from '../mappers';

import styles from './GroupsTable.module.css';
import { RunBy } from './RunBy';

function handOverPath(group: GroupRow): string {
  return `/groups/${group.id}`;
}

/**
 * **The Groups table** (club mocks 15–16): each official group, who runs it, its players and
 * how many are waiting, how much of its WhatsApp crowd has arrived, and the games it gave birth
 * to. Anywhere on a row opens its Hand over page: the group's name is the link a keyboard and a
 * screen reader follow, and a click elsewhere on the row goes where it goes. (A link stretched
 * over the row would need the row to hold it, which Safari's table rows never do.) On a phone
 * each row stacks, and a figure says what it counts, since the column heads are gone.
 */
export function GroupsTable({ groups }: { groups: readonly GroupRow[] }) {
  const router = useRouter();
  return (
    <Card>
      <table className={tableStyles.table}>
        <thead className={tableStyles.head}>
          <tr>
            <th scope="col">{COPY.columns.group}</th>
            <th scope="col">{COPY.columns.administrator}</th>
            <th scope="col">{COPY.columns.players}</th>
            <th scope="col">{COPY.columns.fromWhatsApp}</th>
            <th scope="col">{COPY.columns.games}</th>
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => (
            <tr
              key={group.id}
              className={styles.row}
              onClick={(event) => {
                // The name's own link has gone already.
                if (event.target instanceof Element && event.target.closest('a') !== null) return;
                router.push(handOverPath(group));
              }}
            >
              <th scope="row" className={styles.name}>
                <Link href={handOverPath(group)} className={styles.open}>
                  {group.name}
                </Link>
              </th>
              <td>
                <RunBy administrator={group.administrator} />
              </td>
              <td className={styles.labelled} data-label={COPY.columns.players}>
                <span className={styles.players}>
                  {group.players}
                  {group.waiting > 0 ? (
                    <>
                      {' '}
                      <Tag tone="amber">{COPY.waiting(group.waiting)}</Tag>
                    </>
                  ) : null}
                </span>
              </td>
              <td className={styles.labelled} data-label={COPY.columns.fromWhatsApp}>
                <div className={styles.whatsApp}>
                  <span className={styles.figure}>
                    {COPY.fromWhatsApp(group.players, group.whatsApp.size, group.whatsApp.percent)}
                  </span>
                  <Bar value={group.players} max={group.whatsApp.size} />
                </div>
              </td>
              <td className={styles.labelled} data-label={COPY.columns.games}>
                {group.games}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
