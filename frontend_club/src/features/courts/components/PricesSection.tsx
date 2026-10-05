'use client';

import { useActionState, useState } from 'react';

import type { Sport } from '@/features/club-details/mappers';
import { Button } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { Form } from '@/ui/Form';
import { sentenceFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { SectionHeader } from '@/ui/SectionHeader';
import { useFormFeedback } from '@/ui/useFormFeedback';

import { savePrices, type PricesFormState } from '../actions';
import { COURTS_COPY, priceRefusal } from '../copy';
import type { SportPrice } from '../mappers';
import { priceDraftOf, type PriceDraft } from '../schemas';

import styles from './CourtsAndPrices.module.css';
import { SportPriceFields } from './SportPriceFields';

const COPY = COURTS_COPY.prices;
const NOTHING_YET: PricesFormState = { refusals: {}, formRefusal: null, saved: null };

/**
 * **Prices** (the screens B3, the mechanics §16.5): a row per sport the club offers, each with
 * its price per court-hour, its bands and the share each makes, and one *Save prices* for the
 * whole table. A refusal is said under the sport it is about; a save that lands puts the table
 * back as the backend recorded it.
 */
export function PricesSection({ prices }: { prices: readonly SportPrice[] }) {
  const [state, save, saving] = useActionState(savePrices, NOTHING_YET);
  const [answered, setAnswered] = useState(state);
  const [drafts, setDrafts] = useState<readonly PriceDraft[]>(() => prices.map(priceDraftOf));
  const feedback = useFormFeedback<Sport>(state);

  // A new answer: adjust during render, as React recommends over an effect.
  if (answered !== state) {
    setAnswered(state);
    if (state.saved !== null) setDrafts(state.saved.map(priceDraftOf));
  }

  const formSentence = sentenceFor(feedback.formRefusal, {});

  return (
    <Card labelledBy="prices-title">
      <SectionHeader id="prices-title" title={COPY.title} lead={COPY.lead} />
      <Form action={save} className={styles.form}>
        {formSentence === null ? null : <Notice tone="error">{formSentence}</Notice>}
        {drafts.map((draft) => {
          const code = feedback.refusals[draft.sport];
          return (
            <SportPriceFields
              key={draft.sport}
              draft={draft}
              refusal={code === undefined ? null : priceRefusal(code, draft.sport, draft.seats)}
              onChange={(next) => {
                setDrafts(drafts.map((each) => (each.sport === next.sport ? next : each)));
                feedback.edit(draft.sport);
              }}
            />
          );
        })}
        <div className={styles.buttons}>
          <Button type="submit" disabled={saving}>
            {saving ? COPY.saving : COPY.save}
          </Button>
          {state.saved !== null && !feedback.touched ? (
            <Notice tone="success">{COPY.saved}</Notice>
          ) : null}
        </div>
      </Form>
    </Card>
  );
}
