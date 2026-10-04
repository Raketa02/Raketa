import { Banner } from '@/ui/Banner';
import { Button } from '@/ui/Button';

import { ADMINISTRATORS_COPY } from '../copy';
import type { Sent } from '../mappers';

import styles from './SentBanner.module.css';

const COPY = ADMINISTRATORS_COPY.sent;

/** **"Invitation sent · valid 72 hours"** (club mock 4), naming whom it went to, with *Done*. */
export function SentBanner({ sent, onDone }: { sent: Sent; onDone: () => void }) {
  const words = COPY[sent.kind];

  return (
    <Banner
      kicker={words.kicker}
      title={
        <>
          <strong>{sent.name}</strong>
          <span aria-hidden="true"> · </span>
          <span className={styles.email}>{sent.email}</span>
        </>
      }
      lead={'lead' in words ? words.lead : undefined}
      action={
        <Button type="button" tone="inverse" onClick={onDone}>
          {COPY.done}
        </Button>
      }
    />
  );
}
