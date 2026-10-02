import 'server-only';

import type { Sport } from '@/features/club-details/mappers';
import { readAsClub } from '@/server/club';

import {
  clubDay,
  toCourt,
  toException,
  toSportPrice,
  type Court,
  type Exception,
  type SportPrice,
} from './mappers';

/** **Courts & prices**: everything the page draws, read together. */
export interface CourtsAndPrices {
  /** In the order they were added. */
  readonly courts: readonly Court[];
  /** Every exception not over yet, the soonest first. */
  readonly exceptions: readonly Exception[];
  /** Every sport the club offers, in the registry's order, priced or not. */
  readonly prices: readonly SportPrice[];
  /** The sports the club offers: a court plays one of them. */
  readonly sports: readonly Sport[];
  /** The local day at the club: no exception can close a day before it. */
  readonly today: string;
}

export async function getCourtsAndPrices(): Promise<CourtsAndPrices> {
  const [courts, exceptions, prices] = await Promise.all([
    readAsClub((api, auth) => api.GET('/api/v1/club/courts', auth)),
    readAsClub((api, auth) => api.GET('/api/v1/club/exceptions', auth)),
    readAsClub((api, auth) => api.GET('/api/v1/club/prices', auth)),
  ]);
  if (!courts.ok) throw new Error(`The club's courts could not be read: ${courts.error.code}`);
  if (!exceptions.ok) {
    throw new Error(`The club's exceptions could not be read: ${exceptions.error.code}`);
  }
  if (!prices.ok) throw new Error(`The club's prices could not be read: ${prices.error.code}`);
  return {
    courts: courts.data.courts.map(toCourt),
    exceptions: exceptions.data.exceptions.map(toException),
    prices: prices.data.prices.map(toSportPrice),
    // The price table lists every sport the club offers, priced or not.
    sports: prices.data.prices.map((price) => price.sport),
    today: clubDay(Date.now()),
  };
}
