import type { ReactNode } from 'react';

import { Button } from '@/ui/Button';
import { Card } from '@/ui/Card';
import tableStyles from '@/ui/Table.module.css';
import { Tag } from '@/ui/Tag';

import { ADMINISTRATORS_COPY as COPY, lastUsed } from '../copy';
import type { AdministeredGroup, Administrator, Status } from '../mappers';
import type { Act } from '../schemas';

import { ActFields } from './ActFields';

import styles from './AdministratorsTable.module.css';

/** *2 groups*, opening onto their names; or *none yet* (club mock 14). */
function Groups({ groups }: { groups: readonly AdministeredGroup[] }) {
  if (groups.length === 0) return <span className={styles.muted}>{COPY.noGroups}</span>;
  return (
    <details className={styles.groups}>
      <summary className={styles.summary}>{COPY.groupCount(groups.length)}</summary>
      <ul className={styles.groupList}>
        {groups.map((group) => (
          <li key={group.id}>{group.name}</li>
        ))}
      </ul>
    </details>
  );
}

const TONES = { active: 'green', invited: 'amber', expired: 'red' } as const;

function whenOf(status: Status): string | null {
  switch (status.kind) {
    case 'active':
      return status.idleDays === null ? null : lastUsed(status.idleDays);
    case 'invited':
      return COPY.expiresIn(status.daysLeft);
    case 'expired':
      return COPY.expiredAgo(status.daysAgo);
  }
}

/** *active · this week*, *invited · expires in 3 d*, *expired · 2 d ago* (club mock 4). */
function StatusCell({ status }: { status: Status }) {
  const when = whenOf(status);
  return (
    <span className={styles.status}>
      <Tag tone={TONES[status.kind]}>{COPY.status[status.kind]}</Tag>
      {when === null ? null : <span className={styles.when}>{when}</span>}
    </span>
  );
}

/** One of a row's acts that needs no question first: a form that is only its button. */
function ActButton({
  act,
  administrator,
  action,
  pending,
  children,
}: {
  act: Exclude<Act, 'remove'>;
  administrator: Administrator;
  action: (form: FormData) => void;
  pending: boolean;
  children: ReactNode;
}) {
  return (
    <form action={action}>
      <ActFields act={act} administrator={administrator} />
      <Button type="submit" tone="secondary" disabled={pending}>
        {children}
      </Button>
    </form>
  );
}

/**
 * **The Administrators table** (club mocks 2 and 14): who each person is, the groups they run,
 * where they stand and what the club may do about it. On a phone each row stacks. The acts post
 * to `action`, one at a time: every act waits while one is under way. *Remove* asks first, so
 * it only says whom through `onRemove`.
 */
export function AdministratorsTable({
  administrators,
  action,
  pending,
  onRemove,
}: {
  administrators: readonly Administrator[];
  action: (form: FormData) => void;
  pending: boolean;
  onRemove: (administrator: Administrator) => void;
}) {
  return (
    <Card>
      <table className={tableStyles.table}>
        <thead className={tableStyles.head}>
          <tr>
            <th scope="col">{COPY.columns.name}</th>
            <th scope="col">{COPY.columns.email}</th>
            <th scope="col">{COPY.columns.groups}</th>
            <th scope="col">{COPY.columns.status}</th>
            <th scope="col">
              <span className="visually-hidden">{COPY.columns.actions}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {administrators.map((administrator) => (
            <tr key={administrator.id}>
              <th scope="row" className={styles.name}>
                {administrator.name}
              </th>
              <td>
                <span className={styles.email}>{administrator.email}</span>
              </td>
              <td>
                <Groups groups={administrator.groups} />
              </td>
              <td>
                <StatusCell status={administrator.status} />
              </td>
              <td>
                <div className={styles.actions}>
                  {administrator.status.kind === 'active' ? null : (
                    <ActButton
                      act="resend"
                      administrator={administrator}
                      action={action}
                      pending={pending}
                    >
                      {COPY.resend}
                    </ActButton>
                  )}
                  {administrator.canResetPassword ? (
                    <ActButton
                      act="reset"
                      administrator={administrator}
                      action={action}
                      pending={pending}
                    >
                      {COPY.resetPassword}
                    </ActButton>
                  ) : null}
                  <Button
                    type="button"
                    tone="danger"
                    disabled={pending}
                    onClick={() => onRemove(administrator)}
                  >
                    {COPY.remove}
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
