'use client';

import { useActionState, useState } from 'react';

import { Button } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { Form } from '@/ui/Form';
import { sentenceFor, type Refusals } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { RadioCards } from '@/ui/RadioCards';
import { TextField } from '@/ui/TextField';
import { Toggle } from '@/ui/Toggle';
import { useFormFeedback } from '@/ui/useFormFeedback';

import {
  pauseRaketaBookings,
  saveRaketaSettings,
  type PauseState,
  type SettingsFormState,
} from '../actions';
import { RANGE_REFUSALS, SETTINGS_COPY as COPY, SETTINGS_REFUSALS } from '../copy';
import { WAYS_OF_WORKING, type WayAndSettings } from '../mappers';
import {
  askedFor,
  draftOf,
  NUMBER_FIELDS,
  numbersOf,
  type NumberField,
  type SettingsDraft,
  type SettingsField,
} from '../schemas';

import { LeaveRaketa } from './LeaveRaketa';
import styles from './RaketaSettingsForm.module.css';

const NOTHING_YET: SettingsFormState = {
  refusals: {},
  formRefusal: null,
  saved: null,
  confirmedNow: false,
};
const NOT_PAUSED: PauseState = { paused: false, refusal: null };

const WAY_OPTIONS = WAYS_OF_WORKING.map((way) => ({ value: way, ...COPY.way.options[way] }));

/** A field's refusal as its sentence: a number's says its range. */
function sentenceOf(field: SettingsField, code: string | undefined): string | null {
  if (code === undefined) return null;
  if (code === 'setting_out_of_range' && field !== 'way_of_working') return RANGE_REFUSALS[field];
  return sentenceFor(code, SETTINGS_REFUSALS);
}

/** *Confirm settings* the first time, the setup checklist's last step; *Save settings* after. */
function submitLabel(confirmed: boolean, pending: boolean): string {
  if (confirmed) return pending ? COPY.saving : COPY.save;
  return pending ? COPY.confirming : COPY.confirm;
}

/**
 * **Raketa settings** (the screens B5): one form, one save. The way the club works, as three
 * cards; then the numbers that way asks for, with the cut-off every way has; then other clubs'
 * courts and the pause. A number the chosen way does not ask for is sent as the backend holds
 * it, so a hidden box can never be what a save is refused for. The first save confirms the
 * settings, the setup checklist's last step, and the button says so.
 */
export function RaketaSettingsForm({
  settings,
  confirmed,
}: {
  settings: WayAndSettings;
  confirmed: boolean;
}) {
  const [state, formAction, pending] = useActionState(saveRaketaSettings, NOTHING_YET);
  const [pauseState, pause, pausing] = useActionState(pauseRaketaBookings, NOT_PAUSED);
  const [draft, setDraft] = useState<SettingsDraft>(() => draftOf(settings));
  const [answered, setAnswered] = useState(state);
  const [pauseAnswered, setPauseAnswered] = useState(pauseState);
  const [leaving, setLeaving] = useState(false);
  const feedback = useFormFeedback<SettingsField | 'paused'>(state);

  // A new answer: adjust during render, as React recommends over an effect.
  if (answered !== state) {
    setAnswered(state);
    if (state.saved !== null) setDraft(draftOf(state.saved));
  }
  if (pauseAnswered !== pauseState) {
    setPauseAnswered(pauseState);
    if (pauseState.paused) setDraft({ ...draft, paused: true });
  }

  const refusals: Refusals<SettingsField> = feedback.refusals;
  const formSentence = sentenceFor(feedback.formRefusal, SETTINGS_REFUSALS);
  const asked = askedFor(draft.way);
  const held = numbersOf(settings);

  const typed = (field: NumberField, value: string) => {
    setDraft({ ...draft, numbers: { ...draft.numbers, [field]: value } });
    feedback.edit(field);
  };
  const numberBox = (field: NumberField) => (
    <TextField
      key={field}
      label={COPY.numbers[field].label}
      hint={COPY.numbers[field].hint}
      name={field}
      inputMode="numeric"
      value={draft.numbers[field]}
      onChange={(event) => typed(field, event.target.value)}
      error={sentenceOf(field, refusals[field])}
    />
  );
  /** A number this way does not ask for goes as the backend holds it. */
  const asHeld = (field: NumberField) => (
    <input key={field} type="hidden" name={field} value={held[field]} />
  );

  return (
    <Card>
      <Form action={formAction} className={styles.form}>
        {formSentence === null ? null : <Notice tone="error">{formSentence}</Notice>}
        <input type="hidden" name="was" value={settings.way ?? ''} />
        <input type="hidden" name="confirmed" value={String(confirmed)} />
        <RadioCards
          legend={COPY.way.legend}
          name="way_of_working"
          options={WAY_OPTIONS}
          value={draft.way}
          onChange={(way) => {
            setDraft({ ...draft, way });
            feedback.edit('way_of_working');
          }}
          note={COPY.way.note}
          error={sentenceOf('way_of_working', refusals.way_of_working)}
        />
        <div className={styles.numbers}>
          {NUMBER_FIELDS.filter((field) => field !== 'other_clubs_courts').map((field) =>
            asked.includes(field) ? numberBox(field) : asHeld(field),
          )}
        </div>
        <div className={styles.toggles}>
          <Toggle
            label={COPY.otherClubs.label}
            hint={COPY.otherClubs.hint}
            name="other_clubs"
            anchor="other-clubs"
            checked={draft.otherClubs}
            onChange={(otherClubs) => {
              setDraft({ ...draft, otherClubs });
              feedback.edit('other_clubs_courts');
            }}
          >
            {draft.otherClubs ? (
              <div className={styles.distance}>{numberBox('other_clubs_courts')}</div>
            ) : (
              asHeld('other_clubs_courts')
            )}
          </Toggle>
          <Toggle
            label={COPY.paused.label}
            hint={COPY.paused.hint}
            name="paused"
            checked={draft.paused}
            onChange={(paused) => {
              setDraft({ ...draft, paused });
              feedback.edit('paused');
            }}
          />
        </div>
        <div className={styles.actions}>
          <Button type="submit" disabled={pending}>
            {submitLabel(confirmed, pending)}
          </Button>
          {state.saved !== null && !feedback.touched ? (
            <Notice tone="success">{state.confirmedNow ? COPY.confirmed : COPY.saved}</Notice>
          ) : null}
        </div>
      </Form>
      <LeaveRaketa
        open={leaving}
        confirmed={confirmed}
        paused={settings.paused}
        refusal={pauseState.refusal}
        action={pause}
        pending={pausing}
        onOpen={() => setLeaving(true)}
        onClose={() => setLeaving(false)}
      />
    </Card>
  );
}
