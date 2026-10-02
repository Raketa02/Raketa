'use client';

import { useId } from 'react';

import { sportName } from '@/features/club-details/mappers';
import { Button } from '@/ui/Button';
import fieldStyles from '@/ui/Field.module.css';
import { SelectField } from '@/ui/SelectField';
import { TextField } from '@/ui/TextField';

import { COURTS_COPY, FROM_HOURS, shareLine, UNTIL_HOURS } from '../copy';
import { BAND_DAYS, isBandDays } from '../mappers';
import { NEW_BAND, takenPrice, type BandDraft, type PriceDraft } from '../schemas';

import styles from './CourtsAndPrices.module.css';

const COPY = COURTS_COPY.prices;

const DAY_OPTIONS = BAND_DAYS.map((days) => ({ value: days, label: COPY.bandDays[days] }));

/** *140 zł ÷ 4 = 35 zł each* while what is typed splits, or nothing. */
function preview(typed: string, seats: number): string | undefined {
  const price = takenPrice(typed, seats);
  return price === null ? undefined : shareLine(price, seats);
}

/**
 * **One sport's prices** (the screens B3): the price per court-hour, the share it makes, and
 * its bands, each with its days, hours, price and share. The sport's refusal is said under it
 * all, since it may be about any of them. A sport left without a price is left unpriced, and
 * the line under its box says what that means.
 */
export function SportPriceFields({
  draft,
  refusal,
  onChange,
}: {
  draft: PriceDraft;
  /** The sentence for the sport's refusal, or `null`. */
  refusal: string | null;
  onChange: (draft: PriceDraft) => void;
}) {
  const id = useId();
  const { sport, seats } = draft;
  const band = (index: number, next: Partial<BandDraft>) =>
    onChange({
      ...draft,
      bands: draft.bands.map((each, at) => (at === index ? { ...each, ...next } : each)),
    });

  return (
    <fieldset className={styles.sport} aria-invalid={refusal === null ? undefined : true}>
      <legend className={styles.sportName}>{sportName(sport)}</legend>
      <input type="hidden" name="sport" value={sport} />
      <input type="hidden" name={`seats-${sport}`} value={seats} />
      <div className={styles.price}>
        <TextField
          label={COPY.price}
          name={`price-${sport}`}
          inputMode="decimal"
          autoComplete="off"
          value={draft.price}
          onChange={(event) => onChange({ ...draft, price: event.target.value })}
          hint={draft.price.trim() === '' ? COPY.unpriced : preview(draft.price, seats)}
        />
      </div>
      {draft.bands.map((each, index) => (
        // A group named by its title, not a fieldset: a legend sits on the panel's border.
        <div
          key={index}
          role="group"
          aria-labelledby={`${id}-band-${index}`}
          className={styles.band}
        >
          <p id={`${id}-band-${index}`} className={fieldStyles.legend}>
            {COPY.band(index + 1)}
          </p>
          <div className={styles.bandFields}>
            <SelectField
              label={COPY.days}
              name={`band-days-${sport}`}
              options={DAY_OPTIONS}
              value={each.days}
              onChange={(event) => {
                const days = event.target.value;
                if (isBandDays(days)) band(index, { days });
              }}
            />
            <SelectField
              label={COPY.from}
              name={`band-from-${sport}`}
              options={FROM_HOURS}
              value={each.from}
              onChange={(event) => band(index, { from: event.target.value })}
            />
            <SelectField
              label={COPY.until}
              name={`band-until-${sport}`}
              options={UNTIL_HOURS}
              value={each.until}
              onChange={(event) => band(index, { until: event.target.value })}
            />
            <TextField
              label={COPY.bandPrice}
              name={`band-price-${sport}`}
              inputMode="decimal"
              autoComplete="off"
              value={each.price}
              onChange={(event) => band(index, { price: event.target.value })}
              hint={preview(each.price, seats)}
            />
          </div>
          <div>
            <Button
              type="button"
              tone="secondary"
              onClick={() =>
                onChange({ ...draft, bands: draft.bands.filter((_, at) => at !== index) })
              }
            >
              {COPY.removeBand}
            </Button>
          </div>
        </div>
      ))}
      <div>
        <Button
          type="button"
          tone="secondary"
          onClick={() => onChange({ ...draft, bands: [...draft.bands, NEW_BAND] })}
        >
          {COPY.addBand}
        </Button>
      </div>
      {refusal === null ? null : <p className={fieldStyles.error}>{refusal}</p>}
    </fieldset>
  );
}
