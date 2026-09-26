/**
 * **The club's details, wire to view and back.** The only file in this feature that imports a
 * generated type (ADR-0187 §6); everything else reads the {@link Club} it makes.
 */

import type { components } from '@/generated/schema';

type WireClub = components['schemas']['ClubDetailsResponse'];
type WireDetails = components['schemas']['ClubDetailsRequest'];
type WireSport = components['schemas']['Sport'];

/**
 * The four sports, **in the registry's order**, which is the order the backend answers in and
 * the order the chips are drawn in. A `Record` over the wire's enum, so a fifth sport in the
 * contract fails to compile here until it has a name.
 */
const SPORT_NAMES: Readonly<Record<WireSport, string>> = {
  PADEL: 'Padel',
  TENNIS: 'Tennis',
  SQUASH: 'Squash',
  BADMINTON: 'Badminton',
};

export type Sport = WireSport;

export const SPORTS = Object.keys(SPORT_NAMES) as readonly Sport[];

export const SPORT_OPTIONS = SPORTS.map((value) => ({ value, label: SPORT_NAMES[value] }));

export function isSport(value: unknown): value is Sport {
  return typeof value === 'string' && value in SPORT_NAMES;
}

/** *Padel*: a sport as a person names it. */
export function sportName(sport: Sport): string {
  return SPORT_NAMES[sport];
}

/**
 * **A sport the club can't stop offering**, because an official group plays it (ADR-0182 §5):
 * the first such group by name, as the backend's refusal names it.
 */
export interface SportInUse {
  readonly sport: Sport;
  readonly group: string;
}

/**
 * Which group plays the sport a save unticked, from the backend's refusal: `details.sport` and
 * `details.group` of a `club_sport_declared_by_group`. `null` for any other refusal, or one
 * that names neither.
 */
export function toSportInUse(error: {
  readonly code: string;
  readonly details?: Readonly<Record<string, string>>;
}): SportInUse | null {
  if (error.code !== 'club_sport_declared_by_group') return null;
  const { sport, group } = error.details ?? {};
  return isSport(sport) && group !== undefined ? { sport, group } : null;
}

export interface MapPoint {
  readonly latitude: number;
  readonly longitude: number;
}

/** What the map needs from the server: its tiles, and where it opens before a pin exists. */
export interface MapSettings {
  readonly tileUrl: string;
  readonly start: MapPoint;
}

/** A club as its pages draw it. */
export interface Club {
  readonly name: string;
  readonly district: string;
  readonly city: string;
  readonly sports: readonly Sport[];
  readonly point: MapPoint;
}

export function toClub(wire: WireClub): Club {
  return {
    name: wire.name,
    district: wire.district,
    city: wire.city,
    sports: SPORTS.filter((sport) => wire.sports.includes(sport)),
    point: { latitude: wire.point.latitude, longitude: wire.point.longitude },
  };
}

/** *Grzegórzki, Kraków*: where the club is, as the top bar says it after the name. */
export function placeOf(club: Pick<Club, 'district' | 'city'>): string {
  return `${club.district}, ${club.city}`;
}

/** The five details as a save sends them: all of them, every time (a full replacement). */
export function toDetailsBody(details: Club): WireDetails {
  return {
    name: details.name,
    district: details.district,
    city: details.city,
    sports: [...details.sports],
    point: { latitude: details.point.latitude, longitude: details.point.longitude },
  };
}
