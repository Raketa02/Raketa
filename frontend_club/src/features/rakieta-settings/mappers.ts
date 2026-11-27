/**
 * **The club's Rakieta settings, wire to view and back.** The only file in this feature that
 * imports a generated type (ADR-0187 §6); everything else reads the {@link RakietaSettings} it
 * makes. Every club works one way, Only Rakieta (Q121), so there is no way to choose.
 */

import type { components } from '@/generated/schema';

type WireSettings = components['schemas']['RakietaSettingsResponse'];
type WireSettingsBody = components['schemas']['RakietaSettingsRequest'];

/** The Rakieta settings a club confirms (the mechanics §16.6), each at its default until it does. */
export interface RakietaSettings {
  readonly releaseLeadDays: number;
  readonly cutOffHours: number;
  /** *Offer our groups other clubs' courts when ours are full*, and how far; kept while off. */
  readonly otherClubs: { readonly offered: boolean; readonly withinKm: number };
  readonly paused: boolean;
}

export function toRakietaSettings(wire: WireSettings): RakietaSettings {
  return {
    releaseLeadDays: wire.release_lead_days,
    cutOffHours: wire.cut_off_hours,
    otherClubs: {
      offered: wire.other_clubs_courts.offered,
      withinKm: wire.other_clubs_courts.within_km,
    },
    paused: wire.paused,
  };
}

/** Every setting, every time: the first save is the club confirming them, defaults included. */
export function toSettingsBody(settings: RakietaSettings): WireSettingsBody {
  return {
    release_lead_days: settings.releaseLeadDays,
    cut_off_hours: settings.cutOffHours,
    other_clubs_courts: {
      offered: settings.otherClubs.offered,
      within_km: settings.otherClubs.withinKm,
    },
    paused: settings.paused,
  };
}
