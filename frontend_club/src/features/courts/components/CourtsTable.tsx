import { Button } from '@/ui/Button';
import tableStyles from '@/ui/Table.module.css';
import { Tag } from '@/ui/Tag';
import { sportName } from '@/features/club-details/mappers';

import { COURTS_COPY } from '../copy';
import type { Court } from '../mappers';

import { CourtActFields } from './CourtActFields';
import styles from './CourtsAndPrices.module.css';

const COPY = COURTS_COPY.courts;

/**
 * **The courts table** (the screens B3): each court's name, sport, indoor or outdoor, whether Raketa sells it,
 * and what the club may do about it. *Switch on* is a form that is only its button; *Switch off*
 * and *Edit* only say which court, since the first asks and the second opens a form. Every act
 * waits while one is under way.
 */
export function CourtsTable({
  courts,
  action,
  pending,
  onSwitchOff,
  onEdit,
}: {
  courts: readonly Court[];
  action: (form: FormData) => void;
  pending: boolean;
  onSwitchOff: (court: Court) => void;
  onEdit: (court: Court) => void;
}) {
  return (
    <table className={tableStyles.table}>
      <thead className={tableStyles.head}>
        <tr>
          <th scope="col">{COPY.columns.court}</th>
          <th scope="col">{COPY.columns.sport}</th>
          <th scope="col">{COPY.columns.indoor}</th>
          <th scope="col">{COPY.columns.raketa}</th>
          <th scope="col">
            <span className="visually-hidden">{COPY.columns.actions}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        {courts.map((court) => (
          <tr key={court.id}>
            <th scope="row" className={styles.name}>
              {court.name}
            </th>
            <td>{sportName(court.sport)}</td>
            <td>{court.indoor ? COPY.indoorOrOutdoor.indoor : COPY.indoorOrOutdoor.outdoor}</td>
            <td>
              <Tag tone={court.offered ? 'green' : 'neutral'}>
                {court.offered ? COPY.offered.on : COPY.offered.off}
              </Tag>
            </td>
            <td>
              <div className={styles.rowActions}>
                {court.offered ? (
                  <Button
                    type="button"
                    tone="secondary"
                    disabled={pending}
                    onClick={() => onSwitchOff(court)}
                  >
                    {COPY.switchOff}
                  </Button>
                ) : (
                  <form action={action}>
                    <CourtActFields act="switch-on" court={court} />
                    <Button type="submit" tone="secondary" disabled={pending}>
                      {COPY.switchOn}
                    </Button>
                  </form>
                )}
                <Button
                  type="button"
                  tone="secondary"
                  disabled={pending}
                  onClick={() => onEdit(court)}
                >
                  {COPY.edit}
                </Button>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
