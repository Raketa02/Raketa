'use client';

import { Button } from '@/ui/Button';
import { Dialog } from '@/ui/Dialog';

import { GROUPS_COPY } from '../copy';
import type { Choice, GroupRow } from '../mappers';

import styles from './HandOver.module.css';

const COPY = GROUPS_COPY.handOver.confirm;

/**
 * **"Hand Ogrody 33 Club over to Tomek K.?"** (#500 story 108): what a handover changes, then
 * *Cancel* or *Hand over*. Its form is the only one that posts a handover, and it holds nothing
 * but whom to: confirming posts it and closes the question at once.
 */
export function HandOverDialog({
  group,
  to,
  action,
  onClose,
}: {
  group: GroupRow;
  /** Whom the question is about, or `null` while nobody is being asked about. */
  to: Choice | null;
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  return (
    <Dialog
      open={to !== null}
      title={to === null ? '' : COPY.title(group.name, to.name)}
      onClose={onClose}
    >
      {to === null ? null : (
        <>
          <p className={styles.lead}>{COPY.lead(to.name, group.administrator?.name ?? null)}</p>
          <form action={action} onSubmit={onClose} className={styles.dialogButtons}>
            <input type="hidden" name="group" value={group.id} />
            <input type="hidden" name="administrator" value={to.id} />
            <input type="hidden" name="name" value={to.name} />
            <Button type="button" tone="secondary" onClick={onClose}>
              {COPY.cancel}
            </Button>
            <Button type="submit">{COPY.submit}</Button>
          </form>
        </>
      )}
    </Dialog>
  );
}
