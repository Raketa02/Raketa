/**
 * **How the club works with Raketa, wire to view and back.** The only file in this feature that
 * imports a generated type (ADR-0187 §6); everything else reads the {@link WayAndSettings} it
 * makes. The glossary keeps the two apart: the **Way of working** is chosen on its own, and the
 * **Raketa settings** are the terms a club confirms.
 */

import type { components } from '@/generated/schema';

type WireSettings = components['schemas']['RaketaSettingsResponse'];
type WireSettingsBody = components['schemas']['RaketaSettingsRequest'];
type WireWayOfWorkingBody = components['schemas']['WayOfWorkingRequest'];

/** Only Raketa, Instant or On request: one for the whole club (the mechanics §16.3). */
export type WayOfWorking = components['schemas']['WayOfWorking'];

/**
 * The three ways of working, in the order the page offers them. A `Record` over the wire's enum,
 * so a fourth fails to compile here until the page has a place for it.
 */
const KNOWN_WAYS_OF_WORKING: Readonly<Record<WayOfWorking, true>> = {
  ONLY_RAKETA: true,
  INSTANT: true,
  ON_REQUEST: true,
};

export const WAYS_OF_WORKING = Object.keys(KNOWN_WAYS_OF_WORKING) as readonly WayOfWorking[];

export function isWayOfWorking(value: unknown): value is WayOfWorking {
  return typeof value === 'string' && value in KNOWN_WAYS_OF_WORKING;
}

/** The Raketa settings a club confirms (the mechanics §16.6), each at its default until it does. */
export interface RaketaSettings {
  readonly releaseLeadDays: number;
  readonly cutOffHours: number;
  readonly minimumNoticeHours: number;
  readonly timeToConfirmMinutes: number;
  /** *Offer our groups other clubs' courts when ours are full*, and how far; kept while off. */
  readonly otherClubs: { readonly offered: boolean; readonly withinKm: number };
  readonly paused: boolean;
}

/** What the settings page reads and draws: the way of working, and the settings. */
export interface WayAndSettings extends RaketaSettings {
  /** `null` until the club chooses. */
  readonly way: WayOfWorking | null;
}

export function toWayAndSettings(wire: WireSettings): WayAndSettings {
  return {
    way: wire.way_of_working,
    releaseLeadDays: wire.release_lead_days,
    cutOffHours: wire.cut_off_hours,
    minimumNoticeHours: wire.minimum_notice_hours,
    timeToConfirmMinutes: wire.time_to_confirm_minutes,
    otherClubs: {
      offered: wire.other_clubs_courts.offered,
      withinKm: wire.other_clubs_courts.within_km,
    },
    paused: wire.paused,
  };
}

/** Every setting, every time: the first save is the club confirming them, defaults included. */
export function toSettingsBody(settings: RaketaSettings): WireSettingsBody {
  return {
    release_lead_days: settings.releaseLeadDays,
    cut_off_hours: settings.cutOffHours,
    minimum_notice_hours: settings.minimumNoticeHours,
    time_to_confirm_minutes: settings.timeToConfirmMinutes,
    other_clubs_courts: {
      offered: settings.otherClubs.offered,
      within_km: settings.otherClubs.withinKm,
    },
    paused: settings.paused,
  };
}

export function toWayOfWorkingBody(way: WayOfWorking): WireWayOfWorkingBody {
  return { way_of_working: way };
}
