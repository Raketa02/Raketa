'use client';

import { Button } from '@/ui/Button';
import { Dialog } from '@/ui/Dialog';

import { COURTS_COPY } from '../copy';
import type { Court } from '../mappers';

import { CourtActFields } from './CourtActFields';
import styles from './CourtsAndPrices.module.css';

/** The two acts on a court that ask first. */
export interface Confirming {
  readonly act: 'switch-off' | 'delete';
  readonly court: Court;
}

/**
 * **"Switch Court 2 off?"** and **"Delete Court 2?"**: what the act does, then *Cancel* or the
 * act. Confirming posts it and closes the question at once; the table changes when the page is
 * drawn again.
 */
export function CourtDialog({
  confirming,
  action,
  onClose,
}: {
  /** What the question is about, or `null` while nothing is asked. */
  confirming: Confirming | null;
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  const copy =
    confirming?.act === 'delete' ? COURTS_COPY.courts.confirmDelete : COURTS_COPY.courts.confirmOff;
  return (
    <Dialog
      open={confirming !== null}
      title={confirming === null ? '' : copy.title(confirming.court.name)}
      onClose={onClose}
    >
      <p className={styles.lead}>{copy.lead}</p>
      {confirming === null ? null : (
        <form action={action} onSubmit={onClose} className={styles.dialogButtons}>
          <CourtActFields act={confirming.act} court={confirming.court} />
          <Button type="button" tone="secondary" onClick={onClose}>
            {copy.cancel}
          </Button>
          <Button type="submit" tone="danger">
            {copy.confirm}
          </Button>
        </form>
      )}
    </Dialog>
  );
}
