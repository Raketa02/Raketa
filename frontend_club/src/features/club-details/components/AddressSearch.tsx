'use client';

import { useId, useState, useTransition, type KeyboardEvent } from 'react';

import { Button } from '@/ui/Button';
import fieldStyles from '@/ui/Field.module.css';

import { findAddress } from '../actions';
import { ADDRESS_REFUSALS, DETAILS_COPY } from '../copy';
import type { MapPoint } from '../mappers';
import { addressQuery } from '../schemas';

import styles from './AddressSearch.module.css';

type Said = { readonly found: string } | { readonly refused: string } | null;

/**
 * **The address over the map**: the desk types where the club is and presses Enter or _Find_, and
 * the best match is handed to `onFound`, which takes the map and the pin there. The place the
 * geocoder found is said under the box, so the desk can check it; the pin can still be dragged.
 *
 * **It sits inside the details form and is not one of its fields**: the box has no `name`, so the
 * form never sends it, and Enter searches rather than submitting the form around it — a sign-up
 * sent by the key that was meant to find the address is the failure it is built against.
 *
 * Too short a query is said at once and never sent; the server checks it again.
 */
export function AddressSearch({ onFound }: { onFound: (point: MapPoint) => void }) {
  const id = useId();
  const hintId = `${id}-hint`;
  const saidId = `${id}-said`;
  const [address, setAddress] = useState('');
  const [said, setSaid] = useState<Said>(null);
  const [pending, startTransition] = useTransition();

  const search = () => {
    if (pending) return;
    const query = addressQuery(address);
    if (query === null) {
      setSaid({ refused: ADDRESS_REFUSALS.place_query_invalid! });
      return;
    }
    startTransition(async () => {
      const answer = await findAddress(query);
      if (answer.found) {
        setSaid({ found: answer.name });
        onFound(answer.point);
      } else {
        setSaid({
          refused: ADDRESS_REFUSALS[answer.code] ?? ADDRESS_REFUSALS.geocoder_unreachable!,
        });
      }
    });
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== 'Enter' || event.nativeEvent.isComposing) return;
    event.preventDefault();
    search();
  };

  const refused = said !== null && 'refused' in said;

  return (
    <div className={fieldStyles.field}>
      <label htmlFor={id} className={fieldStyles.label}>
        {DETAILS_COPY.address}
      </label>
      <div className={styles.row}>
        <input
          id={id}
          type="search"
          enterKeyHint="search"
          autoComplete="street-address"
          className={fieldStyles.input}
          value={address}
          onChange={(event) => {
            setAddress(event.target.value);
            setSaid(null);
          }}
          onKeyDown={onKeyDown}
          aria-invalid={refused ? true : undefined}
          aria-describedby={`${hintId} ${saidId}`}
        />
        <Button type="button" tone="secondary" onClick={search} disabled={pending}>
          {pending ? DETAILS_COPY.finding : DETAILS_COPY.find}
        </Button>
      </div>
      <p id={hintId} className={fieldStyles.hint}>
        {DETAILS_COPY.addressHint}
      </p>
      {/* Always drawn, so a screen reader is already listening when the answer lands. */}
      <p id={saidId} aria-live="polite" className={refused ? fieldStyles.error : styles.found}>
        {said === null ? null : 'found' in said ? (
          <>
            {DETAILS_COPY.found} <span className={styles.place}>{said.found}</span>
          </>
        ) : (
          said.refused
        )}
      </p>
    </div>
  );
}
