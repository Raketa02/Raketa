/**
 * **The settings as the form holds them, and the checks a save makes before it leaves.** They
 * restate the backend's bounds (ADR-0187's accepted cost of independent apps) and refuse with
 * its codes, keyed by the field the backend's refusal names, so one sentence serves either side.
 */

import { formText, type Refusals } from '@/ui/forms';

import {
  isWayOfWorking,
  type WayAndSettings,
  type RaketaSettings,
  type WayOfWorking,
} from './mappers';

/** The settings typed as a number, by the names the backend's `details.field` gives them. */
export const NUMBER_FIELDS = [
  'release_lead_days',
  'minimum_notice_hours',
  'time_to_confirm_minutes',
  'cut_off_hours',
  'other_clubs_courts',
] as const;

export type NumberField = (typeof NUMBER_FIELDS)[number];

export const SETTINGS_FIELDS = ['way_of_working', ...NUMBER_FIELDS] as const;

export type SettingsField = (typeof SETTINGS_FIELDS)[number];

/** Each number's range, as the domain bounds it (#535). */
export const BOUNDS: Readonly<Record<NumberField, readonly [number, number]>> = {
  release_lead_days: [1, 13],
  minimum_notice_hours: [1, 48],
  time_to_confirm_minutes: [5, 60],
  cut_off_hours: [0, 72],
  other_clubs_courts: [1, 50],
};

/**
 * **The numbers a way asks for**, in the page's order: the release lead at Only Raketa, the
 * minimum notice at the other two, and the time to confirm at On request, then the cut-off at
 * every one. Until a way is chosen, only the cut-off.
 */
export function askedFor(way: WayOfWorking | null): readonly NumberField[] {
  switch (way) {
    case 'ONLY_RAKETA':
      return ['release_lead_days', 'cut_off_hours'];
    case 'INSTANT':
      return ['minimum_notice_hours', 'cut_off_hours'];
    case 'ON_REQUEST':
      return ['minimum_notice_hours', 'time_to_confirm_minutes', 'cut_off_hours'];
    case null:
      return ['cut_off_hours'];
  }
}

export interface SettingsDraft {
  readonly way: WayOfWorking | null;
  /** Each number as typed. */
  readonly numbers: Readonly<Record<NumberField, string>>;
  readonly otherClubs: boolean;
  readonly checkIn: boolean;
  readonly paused: boolean;
}

/** Each number as the settings hold it. */
export function numbersOf(settings: RaketaSettings): Record<NumberField, number> {
  return {
    release_lead_days: settings.releaseLeadDays,
    minimum_notice_hours: settings.minimumNoticeHours,
    time_to_confirm_minutes: settings.timeToConfirmMinutes,
    cut_off_hours: settings.cutOffHours,
    other_clubs_courts: settings.otherClubs.withinKm,
  };
}

export function draftOf(settings: WayAndSettings): SettingsDraft {
  const numbers = numbersOf(settings);
  return {
    way: settings.way,
    numbers: Object.fromEntries(
      NUMBER_FIELDS.map((field) => [field, String(numbers[field])]),
    ) as Record<NumberField, string>,
    otherClubs: settings.otherClubs.offered,
    checkIn: settings.checkIn,
    paused: settings.paused,
  };
}

export function readSettings(form: FormData): SettingsDraft {
  const way = formText(form, 'way_of_working');
  return {
    way: isWayOfWorking(way) ? way : null,
    numbers: Object.fromEntries(
      NUMBER_FIELDS.map((field) => [field, formText(form, field)]),
    ) as Record<NumberField, string>,
    otherClubs: form.get('other_clubs') === 'on',
    checkIn: form.get('check_in') === 'on',
    paused: form.get('paused') === 'on',
  };
}

/** A whole number within the field's range, or `null`. */
function wholeWithin(typed: string, [least, most]: readonly [number, number]): number | null {
  if (!/^\d{1,3}$/.test(typed.trim())) return null;
  const value = Number(typed.trim());
  return value >= least && value <= most ? value : null;
}

export function checkSettings(draft: SettingsDraft): Refusals<SettingsField> {
  const refusals: Refusals<SettingsField> = {};
  if (draft.way === null) refusals.way_of_working = 'way_of_working_not_chosen';
  for (const field of NUMBER_FIELDS) {
    if (wholeWithin(draft.numbers[field], BOUNDS[field]) === null) {
      refusals[field] = 'setting_out_of_range';
    }
  }
  return refusals;
}

/** A draft that passed {@link checkSettings}, as the settings a save sends. */
export function settingsOf(draft: SettingsDraft): RaketaSettings {
  const number = (field: NumberField) => Number(draft.numbers[field].trim());
  return {
    releaseLeadDays: number('release_lead_days'),
    cutOffHours: number('cut_off_hours'),
    minimumNoticeHours: number('minimum_notice_hours'),
    timeToConfirmMinutes: number('time_to_confirm_minutes'),
    otherClubs: { offered: draft.otherClubs, withinKm: number('other_clubs_courts') },
    checkIn: draft.checkIn,
    paused: draft.paused,
  };
}
