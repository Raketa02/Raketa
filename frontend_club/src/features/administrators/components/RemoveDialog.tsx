'use client';

import { Button } from '@/ui/Button';
import { Dialog } from '@/ui/Dialog';

import { ADMINISTRATORS_COPY } from '../copy';
import type { Administrator } from '../mappers';

import { ActFields } from './ActFields';
import styles from './RemoveDialog.module.css';

const COPY = ADMINISTRATORS_COPY.confirmRemove;

/**
 * **"Remove Marta Wójcik?"** (#500 story 104): what a removal does, then *Cancel* or *Remove*.
 * Confirming posts the removal and closes the question at once; the row goes when the page is
 * drawn again.
 */
export function RemoveDialog({
  administrator,
  action,
  onClose,
}: {
  /** Whom the question is about, or `null` while nobody is being removed. */
  administrator: Administrator | null;
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  return (
    <Dialog
      open={administrator !== null}
      title={administrator === null ? '' : COPY.title(administrator.name)}
      onClose={onClose}
    >
      <p className={styles.lead}>{COPY.lead}</p>
      {administrator === null ? null : (
        <form action={action} onSubmit={onClose} className={styles.buttons}>
          <ActFields act="remove" administrator={administrator} />
          <Button type="button" tone="secondary" onClick={onClose}>
            {COPY.cancel}
          </Button>
          <Button type="submit" tone="danger">
            {COPY.remove}
          </Button>
        </form>
      )}
    </Dialog>
  );
}
