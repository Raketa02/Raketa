/**
 * Move the filter's switch — *Off*, *at least Medium* or *at least High*
 * ([ADR-0195](../../../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
 * §6, [#662](https://github.com/Raketa02/Raketa/issues/662)).
 *
 * A pass-through with one translation, which is the uniform-strict escape hatch again: the one
 * thing the client decides is that *Off* is written as `null`, and `minimumOf` is where that is
 * written down. What the filter then does to the deal is the server's, from the moment it answers.
 */

import { putReliabilityFilter } from '../api/playerRecordApi';
import { minimumOf, type FilterPosition } from '../domain/reliabilityFilter';

export function setReliabilityFilter(position: FilterPosition): Promise<void> {
  return putReliabilityFilter(minimumOf(position));
}
