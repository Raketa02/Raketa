'use client';

import dynamic from 'next/dynamic';
import { useId, useRef } from 'react';

import { Button } from '@/ui/Button';
import { Chips } from '@/ui/Chips';
import fieldStyles from '@/ui/Field.module.css';
import { TextField } from '@/ui/TextField';

import { DETAILS_COPY } from '../copy';
import { SPORT_OPTIONS, SPORTS, type MapPoint, type MapSettings, type Sport } from '../mappers';
import type { DetailsDraft, DetailsField } from '../schemas';

import styles from './ClubDetailsFields.module.css';
import type { PinMapHandle } from './PinMap';

const PinMap = dynamic(() => import('./PinMap').then((module) => module.PinMap), {
  ssr: false,
  loading: () => <div className={styles.mapLoading} aria-hidden="true" />,
});

function formatPoint(point: MapPoint): string {
  return `${point.latitude.toFixed(5)}, ${point.longitude.toFixed(5)}`;
}

/**
 * **The five details as boxes, chips and a map**: Club details' whole form, and the top of the
 * sign-up form. Controlled by its owner, who holds the draft; `onEdit` names the field that
 * changed, so the owner can take that field's refusal away.
 */
export function ClubDetailsFields({
  draft,
  onChange,
  refusals,
  map,
}: {
  draft: DetailsDraft;
  onChange: (draft: DetailsDraft, field: DetailsField) => void;
  refusals: Partial<Record<DetailsField, string>>;
  map: MapSettings;
}) {
  const hintId = useId();
  const pinErrorId = useId();
  const handle = useRef<PinMapHandle | null>(null);

  const toggle = (sport: Sport) => {
    const chosen = new Set(draft.sports);
    if (chosen.has(sport)) chosen.delete(sport);
    else chosen.add(sport);
    onChange({ ...draft, sports: SPORTS.filter((each) => chosen.has(each)) }, 'sports');
  };

  return (
    <div className={styles.fields}>
      <TextField
        label={DETAILS_COPY.name}
        name="name"
        value={draft.name}
        onChange={(event) => onChange({ ...draft, name: event.target.value }, 'name')}
        error={refusals.name}
        autoComplete="organization"
      />
      <div className={styles.pair}>
        <TextField
          label={DETAILS_COPY.district}
          name="district"
          value={draft.district}
          onChange={(event) => onChange({ ...draft, district: event.target.value }, 'district')}
          error={refusals.district}
        />
        <TextField
          label={DETAILS_COPY.city}
          name="city"
          value={draft.city}
          onChange={(event) => onChange({ ...draft, city: event.target.value }, 'city')}
          error={refusals.city}
          autoComplete="address-level2"
        />
      </div>
      <Chips
        legend={DETAILS_COPY.sports}
        name="sports"
        options={SPORT_OPTIONS}
        selected={draft.sports}
        onToggle={toggle}
        error={refusals.sports}
      />
      <fieldset className={fieldStyles.group}>
        <legend className={fieldStyles.legend}>{DETAILS_COPY.pin}</legend>
        <div className={styles.pin}>
          <p id={hintId} className={fieldStyles.hint}>
            {DETAILS_COPY.pinHint}
          </p>
          <PinMap
            tileUrl={map.tileUrl}
            start={map.start}
            value={draft.point}
            onChange={(point) => onChange({ ...draft, point }, 'point')}
            label={DETAILS_COPY.map}
            describedBy={refusals.point ? `${hintId} ${pinErrorId}` : hintId}
            onReady={(ready) => {
              handle.current = ready;
            }}
          />
          <div className={styles.pinRow}>
            <p className={styles.readout} aria-live="polite">
              {draft.point === null ? (
                DETAILS_COPY.pinNone
              ) : (
                <>
                  {DETAILS_COPY.pinAt}{' '}
                  <span className={styles.mono}>{formatPoint(draft.point)}</span>
                </>
              )}
            </p>
            <Button type="button" tone="secondary" onClick={() => handle.current?.centre()}>
              {DETAILS_COPY.pinCentre}
            </Button>
          </div>
          {refusals.point ? (
            <p id={pinErrorId} className={fieldStyles.error}>
              {refusals.point}
            </p>
          ) : null}
        </div>
        <input type="hidden" name="latitude" value={draft.point?.latitude ?? ''} />
        <input type="hidden" name="longitude" value={draft.point?.longitude ?? ''} />
      </fieldset>
    </div>
  );
}
