/**
 * The builder's one param is untrusted input, and it is worth checking twice over: the string
 * becomes `ForecastRequest.search_id` on a request body **and** a Query key.
 *
 * An unchecked one would put somebody else's text into both — a cache entry under a key nothing
 * could ever clear, and a request the origin route would answer `404 search_not_found` to, which
 * is one code for four cases and so tells nobody what happened.
 */

import { parseBuilderRouteParams } from './routeParams';

const SEARCH = 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';

describe('the builder route params', () => {
  it('accepts a well-formed link', () => {
    expect(parseBuilderRouteParams({ search: SEARCH })).toEqual({ search: SEARCH });
  });

  it('rejects a search id that is not one', () => {
    expect(parseBuilderRouteParams({ search: '../../searches/someone-else' })).toBeUndefined();
    expect(parseBuilderRouteParams({ search: 'latest' })).toBeUndefined();
  });

  /** There is no builder without an origin: nobody to seat, and no forecast to ask for. */
  it('rejects a link with no origin at all', () => {
    expect(parseBuilderRouteParams({})).toBeUndefined();
    expect(parseBuilderRouteParams({ search: undefined })).toBeUndefined();
  });

  /**
   * expo-router hands params over as `string | string[]` whatever the route declared, so the
   * array is a real shape rather than a hypothetical one — `?search=a&search=b`.
   */
  it('rejects a param that arrived twice', () => {
    expect(parseBuilderRouteParams({ search: [SEARCH, SEARCH] })).toBeUndefined();
  });

  /**
   * The sport and the mode are `playPreferences`', which is process-scoped and cannot be linked
   * into. A builder whose sport came off a link could disagree with the chips one screen back,
   * which is the state the origin key exists to make impossible rather than one to render.
   */
  it('takes nothing else, so a link cannot decide what the court is for', () => {
    expect(
      parseBuilderRouteParams({ search: SEARCH, sport: 'squash', mode: 'COMPETITIVE' }),
    ).toEqual({ search: SEARCH });
  });
});
