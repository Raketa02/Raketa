/**
 * **The settings as the form holds them, and the checks a save makes before it leaves.** They
 * restate the backend's bounds (ADR-0187's accepted cost of independent apps) and refuse with
 * its codes, keyed by the field the backend's refusal names, so one sentence serves either side.
 */

import { formText, type Refusals } from '@/ui/forms';

import type { RakietaSettings } from './mappers';

/** The settings typed as a number, by the names the backend's `details.field` gives them. */
export const NUMBER_FIELDS = ['release_lead_days', 'cut_off_hours', 'other_clubs_courts'] as const;

export type NumberField = (typeof NUMBER_FIELDS)[number];

/** Each number's range, as the domain bounds it (#535). */
export const BOUNDS: Readonly<Record<NumberField, readonly [number, number]>> = {
  release_lead_days: [1, 13],
  cut_off_hours: [0, 72],
  other_clubs_courts: [1, 50],
};

export interface SettingsDraft {
  /** Each number as typed. */
  readonly numbers: Readonly<Record<NumberField, string>>;
  readonly otherClubs: boolean;
  readonly paused: boolean;
}

/** Each number as the settings hold it. */
export function numbersOf(settings: RakietaSettings): Record<NumberField, number> {
  return {
    release_lead_days: settings.releaseLeadDays,
    cut_off_hours: settings.cutOffHours,
    other_clubs_courts: settings.otherClubs.withinKm,
  };
}

export function draftOf(settings: RakietaSettings): SettingsDraft {
  const numbers = numbersOf(settings);
  return {
    numbers: Object.fromEntries(
      NUMBER_FIELDS.map((field) => [field, String(numbers[field])]),
    ) as Record<NumberField, string>,
    otherClubs: settings.otherClubs.offered,
    paused: settings.paused,
  };
}

export function readSettings(form: FormData): SettingsDraft {
  return {
    numbers: Object.fromEntries(
      NUMBER_FIELDS.map((field) => [field, formText(form, field)]),
    ) as Record<NumberField, string>,
    otherClubs: form.get('other_clubs') === 'on',
    paused: form.get('paused') === 'on',
  };
}

/** A whole number within the field's range, or `null`. */
function wholeWithin(typed: string, [least, most]: readonly [number, number]): number | null {
  if (!/^\d{1,3}$/.test(typed.trim())) return null;
  const value = Number(typed.trim());
  return value >= least && value <= most ? value : null;
}

export function checkSettings(draft: SettingsDraft): Refusals<NumberField> {
  const refusals: Refusals<NumberField> = {};
  for (const field of NUMBER_FIELDS) {
    if (wholeWithin(draft.numbers[field], BOUNDS[field]) === null) {
      refusals[field] = 'setting_out_of_range';
    }
  }
  return refusals;
}

/** A draft that passed {@link checkSettings}, as the settings a save sends. */
export function settingsOf(draft: SettingsDraft): RakietaSettings {
  const number = (field: NumberField) => Number(draft.numbers[field].trim());
  return {
    releaseLeadDays: number('release_lead_days'),
    cutOffHours: number('cut_off_hours'),
    otherClubs: { offered: draft.otherClubs, withinKm: number('other_clubs_courts') },
    paused: draft.paused,
  };
}
