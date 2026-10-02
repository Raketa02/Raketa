'use client';

import { useActionState, useState } from 'react';

import { SPORTS } from '@/features/club-details/mappers';
import { Button } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { Choices } from '@/ui/Choices';
import { Form } from '@/ui/Form';
import { sentenceFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { SectionHeader } from '@/ui/SectionHeader';

import { saveHours, type HoursState } from '../actions';
import { COURTS_COPY, HOURS_REFUSALS, listed } from '../copy';
import type { Court } from '../mappers';
import { cellKey } from '../schemas';

import { CopyHoursDialog } from './CopyHoursDialog';
import styles from './CourtsAndPrices.module.css';
import { HoursGrid } from './HoursGrid';

const COPY = COURTS_COPY.hours;
const NOTHING_SAVED: HoursState = { saved: null, formRefusal: null };

/** What the picker offers: one court, or every court of a sport. */
interface Choice {
  readonly key: string;
  readonly label: string;
  /** The courts a save gives the week to, in the club's order. */
  readonly courts: readonly Court[];
}

/** Each court, then *All padel courts* for each sport with more than one, in the registry's order. */
function choicesOf(courts: readonly Court[]): Choice[] {
  const one = courts.map((court) => ({ key: court.id, label: court.name, courts: [court] }));
  const all = SPORTS.flatMap((sport) => {
    const ofSport = courts.filter((court) => court.sport === sport);
    return ofSport.length < 2
      ? []
      : [{ key: `all-${sport}`, label: COPY.allOf(sport), courts: ofSport }];
  });
  return [...one, ...all];
}

function weekOf(court: Court | undefined): ReadonlySet<string> {
  return new Set(court?.hours.map(cellKey) ?? []);
}

function sameWeek(a: ReadonlySet<string>, b: ReadonlySet<string>): boolean {
  return a.size === b.size && [...a].every((key) => b.has(key));
}

/**
 * **Weekly hours for Raketa** (the screens B3, the mechanics §16.5): a court picker, the week
 * on the grid, and *Save hours*. *All padel courts* starts from the first court's week, and says
 * when the courts differ, since a save gives each of them the week shown. *Copy to other
 * courts* gives one court's week, as shown, to the courts ticked, saving it on this one too. A
 * change of court shows that court's week as saved: a week not saved is not carried over.
 */
export function HoursSection({ courts }: { courts: readonly Court[] }) {
  const [state, save, saving] = useActionState(saveHours, NOTHING_SAVED);
  const [answered, setAnswered] = useState(state);
  const [selected, setSelected] = useState<string | null>(null);
  const [copying, setCopying] = useState(false);

  const choices = choicesOf(courts);
  const choice = choices.find((each) => each.key === selected) ?? choices[0];
  const [week, setWeek] = useState(() => ({ key: choice?.key, cells: weekOf(choice?.courts[0]) }));
  // Another court chosen, or this one gone: its week as saved.
  if (week.key !== choice?.key) setWeek({ key: choice?.key, cells: weekOf(choice?.courts[0]) });

  const [touched, setTouched] = useState(false);
  if (answered !== state) {
    setAnswered(state);
    setTouched(false);
  }

  const refusal = sentenceFor(touched ? null : state.formRefusal, HOURS_REFUSALS);
  const refused = refusal === null ? null : <Notice tone="error">{refusal}</Notice>;

  if (choice === undefined) {
    return (
      <Card labelledBy="hours-title" id="hours">
        <SectionHeader id="hours-title" title={COPY.title} lead={COPY.lead} />
        {refused}
        <p className={styles.none}>{COPY.none}</p>
      </Card>
    );
  }

  const first = choice.courts[0];
  const differ = choice.courts.some((court) => !sameWeek(weekOf(court), weekOf(first)));
  const others = courts.filter((court) => !choice.courts.includes(court));
  return (
    <Card labelledBy="hours-title" id="hours">
      <SectionHeader id="hours-title" title={COPY.title} lead={COPY.lead} />
      <Form action={save} className={styles.form}>
        {refused}
        {choice.courts.map((court) => (
          <input key={court.id} type="hidden" name="court" value={court.id} />
        ))}
        {[...week.cells].map((key) => (
          <input key={key} type="hidden" name="hour" value={key} />
        ))}
        <Choices
          legend={COPY.picker}
          name="picker"
          options={choices.map((each) => ({ value: each.key, label: each.label }))}
          value={choice.key}
          onChange={setSelected}
        />
        {differ ? <p className={styles.note}>{COPY.differ}</p> : null}
        <HoursGrid
          label={COPY.grid(listed(choice.courts.map((court) => court.name)))}
          cells={week.cells}
          onPaint={(key, on) => {
            setWeek((now) => {
              if (now.cells.has(key) === on) return now;
              const cells = new Set(now.cells);
              if (on) cells.add(key);
              else cells.delete(key);
              return { ...now, cells };
            });
            setTouched(true);
          }}
        />
        <div className={styles.buttons}>
          <Button type="submit" disabled={saving}>
            {saving ? COPY.saving : COPY.save}
          </Button>
          {choice.courts.length === 1 && others.length > 0 ? (
            <Button type="button" tone="secondary" onClick={() => setCopying(true)}>
              {COPY.copy}
            </Button>
          ) : null}
          {state.saved !== null && !touched ? (
            <Notice tone="success">{COPY.saved(state.saved)}</Notice>
          ) : null}
        </div>
      </Form>
      {first === undefined ? null : (
        <CopyHoursDialog
          open={copying}
          court={first}
          others={others}
          cells={week.cells}
          action={save}
          onClose={() => setCopying(false)}
        />
      )}
    </Card>
  );
}
