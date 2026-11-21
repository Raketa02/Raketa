/**
 * **The Featurevisor SDK, behind one module** — the only file in the app that imports it
 * ([ADR-0206](../../../../../docs/adr/0206-a-feature-is-turned-on-by-a-pull-request-again-and-explore-is-the-first.md)
 * §5).
 *
 * It holds the instance and answers one question: *given this datafile and this player, is this
 * feature enabled?* Everything else — which datafile, which player, what a feature says when the
 * datafile is silent — is decided above it, so swapping the SDK, or its major, is a change to this
 * file and nothing else. The flags repo's CLI major moves only with this SDK's major; the version
 * is pinned exactly in `package.json`.
 *
 * **The evaluation itself is not tested here.** Percentages, segments and the rest
 * are the SDK's, and the flags repo's specs prove what each feature's rules say. This module is
 * tested for what it adds: that a feature the datafile does not name is *unknown* rather than off.
 */

import { createFeaturevisor, type DatafileContent, type Featurevisor } from '@featurevisor/sdk';

import type { Datafile, EvaluationContext } from '../domain/featureFlags';

/** The instance, and the datafile it was last handed — one of each for the app. */
let instance: Featurevisor | undefined;
let loaded: Datafile | undefined;

/**
 * The instance, holding `datafile`.
 *
 * Replaced rather than merged (`setDatafile(…, true)`): a datafile is a whole answer, and a
 * feature removed from the newer one must not survive from the older.
 *
 * The cast is the checked one — `schemas/` has already refused anything that is not the envelope
 * `DatafileContent` requires.
 */
function instanceHolding(datafile: Datafile): Featurevisor {
  const content = datafile as unknown as DatafileContent;

  if (instance === undefined) {
    instance = createFeaturevisor({
      datafile: content,
      // Routed nowhere. The SDK's default reporter writes every diagnostic to the console, and
      // an evaluation's carries the context it was asked with — a player id in a device log.
      // There is no observability module to send them to yet (architecture Part 15).
      onDiagnostic: () => {},
    });
  } else if (loaded !== datafile) {
    instance.setDatafile(content, true);
  }

  loaded = datafile;
  return instance;
}

/**
 * Whether `feature` is enabled for `context` under `datafile` — or `undefined` when the datafile
 * does not name the feature at all.
 *
 * `undefined` is not *off*. The SDK answers `false` for a feature it cannot find, and that would
 * turn a key the two repositories disagree about into a screen switched off for everybody; the
 * caller answers it with the code default instead (ADR-0206, *Harder*).
 *
 * The context travels with the question rather than being set on the instance, so nothing about
 * a signed-out player stays behind in it.
 */
export function evaluateFeature(
  datafile: Datafile,
  feature: string,
  context: EvaluationContext,
): boolean | undefined {
  const featurevisor = instanceHolding(datafile);

  if (featurevisor.getFeature(feature) === undefined) return undefined;

  return featurevisor.isEnabled(feature, { ...context });
}
