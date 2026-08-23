/**
 * The route Now's door opens: take up one sport.
 *
 * The param is **untrusted input** — this route is reachable from a deep link and
 * the sport becomes a request body — so it is validated before anything reads it,
 * and a link that does not survive lands on welcome rather than issuing a request
 * built from someone else's string.
 *
 * It arrives in the registry's spelling because the value Now holds is the sport
 * bar's chip; `parseSportRouteParam` is where the two spellings meet. `all` is a
 * chip and not a sport, so it does not survive either — which is the same answer
 * as any other link that names nothing this build can rate.
 *
 * A route file and nothing else: what happens behind the door is the feature's.
 */

import { Redirect, useLocalSearchParams } from 'expo-router';

import { TakeUpSportScreen, parseSportRouteParam } from '@/features/onboarding/types';

export default function TakeUpSportRoute() {
  const sport = parseSportRouteParam(useLocalSearchParams());

  if (sport === undefined) return <Redirect href="/welcome" />;

  return <TakeUpSportScreen sport={sport} />;
}
