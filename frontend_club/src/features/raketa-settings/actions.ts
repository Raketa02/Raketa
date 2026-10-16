'use server';

import { revalidatePath } from 'next/cache';

import { stepDone, toSetup } from '@/features/overview/mappers';
import { writeAsClub } from '@/server/club';
import { formText, hasRefusals, placeRefusal, type FormState } from '@/ui/forms';

import { toRaketaSettings, toSettingsBody, type RaketaSettings } from './mappers';
import {
  checkSettings,
  NUMBER_FIELDS,
  readSettings,
  settingsOf,
  type NumberField,
} from './schemas';

const PAGE = '/raketa-settings';

export interface SettingsFormState extends FormState<NumberField> {
  /** The settings as the backend recorded them, after a save that landed. */
  readonly saved: RaketaSettings | null;
  /** Whether that save was the first: the club confirming its settings. */
  readonly confirmedNow: boolean;
}

/** The backend's refusal, under the setting it names, or over the form. */
function refused(error: { readonly code: string; readonly field?: string }): SettingsFormState {
  return { ...placeRefusal(error, NUMBER_FIELDS), saved: null, confirmedNow: false };
}

/**
 * **Confirm settings**, then **Save settings** (the screens B5): every setting, every time.
 * `confirmed` says whether the club had confirmed its settings before, so the page can say which
 * this was.
 */
export async function saveRaketaSettings(
  _previous: SettingsFormState,
  form: FormData,
): Promise<SettingsFormState> {
  const draft = readSettings(form);
  const refusals = checkSettings(draft);
  if (hasRefusals(refusals)) {
    return { refusals, formRefusal: null, saved: null, confirmedNow: false };
  }

  const outcome = await writeAsClub((api, auth) =>
    api.PUT('/api/v1/club/raketa-settings', { ...auth, body: toSettingsBody(settingsOf(draft)) }),
  );
  if (!outcome.ok) return refused(outcome.error);
  revalidatePath(PAGE);

  return {
    refusals: {},
    formRefusal: null,
    saved: toRaketaSettings(outcome.data),
    confirmedNow: formText(form, 'confirmed') !== 'true',
  };
}

export interface PauseState {
  readonly paused: boolean;
  /** What the pause was refused with. */
  readonly refusal: string | null;
}

/**
 * ***Leave Raketa* begins with a pause** (the mechanics §16.15): the settings as the backend
 * holds them, paused. Read first, so a pause never saves what the form holds unsaved. Refused
 * (`settings_not_confirmed`, the website's own) while the settings are not confirmed: a save
 * would confirm them, the checklist's last step, which is the desk's to take on purpose, and a
 * club not live sells nothing to pause.
 */
export async function pauseRaketaBookings(): Promise<PauseState> {
  const setup = await writeAsClub((api, auth) => api.GET('/api/v1/club/setup', auth));
  if (!setup.ok) return { paused: false, refusal: setup.error.code };
  if (!stepDone(toSetup(setup.data), 'SETTINGS')) {
    return { paused: false, refusal: 'settings_not_confirmed' };
  }
  const now = await writeAsClub((api, auth) => api.GET('/api/v1/club/raketa-settings', auth));
  if (!now.ok) return { paused: false, refusal: now.error.code };
  const settings = toRaketaSettings(now.data);
  if (settings.paused) return { paused: true, refusal: null };

  const outcome = await writeAsClub((api, auth) =>
    api.PUT('/api/v1/club/raketa-settings', {
      ...auth,
      body: toSettingsBody({ ...settings, paused: true }),
    }),
  );
  if (!outcome.ok) return { paused: false, refusal: outcome.error.code };
  revalidatePath(PAGE);
  return { paused: true, refusal: null };
}
