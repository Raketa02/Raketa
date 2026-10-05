'use client';

import { Button } from '@/ui/Button';
import { Dialog } from '@/ui/Dialog';
import fieldStyles from '@/ui/Field.module.css';
import { Form } from '@/ui/Form';

import { COURTS_COPY } from '../copy';
import type { Court } from '../mappers';

import styles from './CourtsAndPrices.module.css';

const COPY = COURTS_COPY.hours.copyDialog;

/**
 * **"Copy Court 1's week"**: the club's other courts to tick, and *Copy*, which saves the week
 * as the grid shows it on this court and on each court ticked. Its boxes start unticked every
 * time it opens.
 */
export function CopyHoursDialog({
  open,
  court,
  others,
  cells,
  action,
  onClose,
}: {
  open: boolean;
  court: Court;
  others: readonly Court[];
  cells: ReadonlySet<string>;
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  return (
    <Dialog open={open} title={COPY.title(court.name)} onClose={onClose}>
      <p className={styles.lead}>{COPY.lead(court.name)}</p>
      {open ? (
        <Form action={action} onSent={onClose} className={styles.form}>
          <input type="hidden" name="court" value={court.id} />
          {[...cells].map((key) => (
            <input key={key} type="hidden" name="hour" value={key} />
          ))}
          <fieldset className={fieldStyles.group}>
            <legend className={fieldStyles.legend}>{COPY.to}</legend>
            <ul className={styles.ticks}>
              {others.map((other) => (
                <li key={other.id}>
                  <label className={styles.tick}>
                    <input type="checkbox" name="court" value={other.id} className={styles.box} />
                    {other.name}
                  </label>
                </li>
              ))}
            </ul>
          </fieldset>
          <div className={styles.dialogButtons}>
            <Button type="button" tone="secondary" onClick={onClose}>
              {COPY.cancel}
            </Button>
            <Button type="submit">{COPY.confirm}</Button>
          </div>
        </Form>
      ) : null}
    </Dialog>
  );
}
