'use server';

import { revalidatePath } from 'next/cache';

import { stepDone, toSetup } from '@/features/overview/mappers';
import { writeAsClub } from '@/server/club';
import { formText, hasRefusals, placeRefusal, type FormState } from '@/ui/forms';

import {
  toSettingsBody,
  toWayAndSettings,
  toWayOfWorkingBody,
  type WayAndSettings,
} from './mappers';
import {
  checkSettings,
  readSettings,
  settingsOf,
  SETTINGS_FIELDS,
  type SettingsField,
} from './schemas';

const PAGE = '/raketa-settings';

export interface SettingsFormState extends FormState<SettingsField> {
  /** The way of working and the settings as the backend recorded them, after a save that landed. */
  readonly saved: WayAndSettings | null;
  /** Whether that save was the first: the club confirming its settings. */
  readonly confirmedNow: boolean;
}

/** The backend's refusal, placed: a way of working not chosen goes under the way. */
function refused(error: { readonly code: string; readonly field?: string }): SettingsFormState {
  const placed =
    error.code === 'way_of_working_not_chosen' ? { ...error, field: 'way_of_working' } : error;
  return { ...placeRefusal(placed, SETTINGS_FIELDS), saved: null, confirmedNow: false };
}

/**
 * **Confirm settings**, then **Save settings** (the screens B5): the way of working, then every
 * setting, in that order, because the backend refuses settings until a way is chosen (#535). The
 * way is sent only when it changed (`was` is the way the page was drawn with); `confirmed` says
 * whether the club had confirmed its settings before, so the page can say which this was.
 */
export async function saveRaketaSettings(
  _previous: SettingsFormState,
  form: FormData,
): Promise<SettingsFormState> {
  const draft = readSettings(form);
  const refusals = checkSettings(draft);
  if (hasRefusals(refusals) || draft.way === null) {
    return { refusals, formRefusal: null, saved: null, confirmedNow: false };
  }

  const way = draft.way;
  const wayChanged = way !== formText(form, 'was');
  if (wayChanged) {
    const chosen = await writeAsClub((api, auth) =>
      api.PUT('/api/v1/club/way-of-working', { ...auth, body: toWayOfWorkingBody(way) }),
    );
    if (!chosen.ok) return refused(chosen.error);
  }
  const outcome = await writeAsClub((api, auth) =>
    api.PUT('/api/v1/club/raketa-settings', { ...auth, body: toSettingsBody(settingsOf(draft)) }),
  );
  // A way that landed is recorded even when the settings were refused: the page says so.
  if (outcome.ok || wayChanged) revalidatePath(PAGE);
  if (!outcome.ok) return refused(outcome.error);

  return {
    refusals: {},
    formRefusal: null,
    saved: toWayAndSettings(outcome.data),
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
  const settings = toWayAndSettings(now.data);
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
