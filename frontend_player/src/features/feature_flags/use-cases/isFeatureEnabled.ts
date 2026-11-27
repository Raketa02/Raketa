/**
 * **Is this feature enabled for this player** — the one question a gate asks, answered in
 * ADR-0206 §6's order: the datafile fetched this session, then the one cached on the device, then
 * the feature's code default.
 */

import { evaluateFeature } from '../api/featurevisor';
import {
  FEATURE_DEFAULTS,
  datafileInUse,
  type Datafile,
  type FeatureKey,
  type EvaluationContext,
} from '../domain/featureFlags';

export interface EvaluationSources {
  /** The datafile fetched this session, if one has arrived and was readable. */
  readonly fresh?: Datafile;
  /** The last readable datafile saved on the device — `null` once looked for and not found. */
  readonly cached?: Datafile | null;
  /**
   * The signed-in player. Absent, every feature is at its code default: a rollout buckets by
   * player, and there is nobody to bucket.
   */
  readonly context: EvaluationContext | undefined;
}

export function isFeatureEnabled(feature: FeatureKey, sources: EvaluationSources): boolean {
  const codeDefault = FEATURE_DEFAULTS[feature];
  const datafile = datafileInUse(sources.fresh, sources.cached);

  if (datafile === undefined || sources.context === undefined) return codeDefault;

  // A datafile that does not name the feature has nothing to say about it.
  return evaluateFeature(datafile, feature, sources.context) ?? codeDefault;
}
