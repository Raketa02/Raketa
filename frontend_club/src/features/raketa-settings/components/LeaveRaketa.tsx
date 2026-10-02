'use client';

import { Button } from '@/ui/Button';
import { Dialog } from '@/ui/Dialog';
import { sentenceFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';

import { SETTINGS_COPY, SETTINGS_REFUSALS } from '../copy';

import styles from './RaketaSettingsForm.module.css';

const COPY = SETTINGS_COPY.leave;

/** What the dialog says: what leaving is, that the pause is on, or that there is nothing to leave. */
function leadOf(confirmed: boolean, paused: boolean): string {
  if (!confirmed) return COPY.notSelling;
  return paused ? COPY.paused : COPY.lead;
}

/**
 * ***Leave Raketa***, a quiet link at the bottom of the settings (the screens B5): what leaving
 * is, and its first step, the pause. Disconnecting payments has no door here yet, so the dialog
 * says when it can happen and does what can be done now. A club that has not confirmed its
 * settings sells nothing, so it is told there is nothing to leave, and offered no pause, which
 * would confirm them. Pausing posts and closes the question at once; a refusal is said beside
 * the link.
 */
export function LeaveRaketa({
  open,
  confirmed,
  paused,
  refusal,
  action,
  pending,
  onOpen,
  onClose,
}: {
  open: boolean;
  /** Whether the club has confirmed its settings. */
  confirmed: boolean;
  paused: boolean;
  refusal: string | null;
  action: () => void;
  pending: boolean;
  onOpen: () => void;
  onClose: () => void;
}) {
  const sentence = sentenceFor(refusal, SETTINGS_REFUSALS);
  return (
    <div className={styles.leave}>
      <button type="button" className={styles.leaveLink} onClick={onOpen} disabled={pending}>
        {COPY.open}
      </button>
      {sentence === null ? null : <Notice tone="error">{sentence}</Notice>}
      <Dialog open={open} title={COPY.title} onClose={onClose}>
        <p className={styles.lead}>{leadOf(confirmed, paused)}</p>
        {paused || !confirmed ? (
          <div className={styles.dialogButtons}>
            <Button type="button" tone="secondary" onClick={onClose}>
              {COPY.close}
            </Button>
          </div>
        ) : (
          <form action={action} onSubmit={onClose} className={styles.dialogButtons}>
            <Button type="button" tone="secondary" onClick={onClose}>
              {COPY.cancel}
            </Button>
            <Button type="submit" tone="danger">
              {COPY.pause}
            </Button>
          </form>
        )}
      </Dialog>
    </div>
  );
}
