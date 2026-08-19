/**
 * The badge that says which environment the running app is pointed at — or nothing at all,
 * in production.
 *
 * **It is a Server Component, and that is the whole design.** The environment is
 * server-only configuration; the alternative — mirroring it into a `NEXT_PUBLIC_ENV` so a
 * Client Component could read it — would put a second copy of the environment name in the
 * bundle, free to disagree with the one the BFF actually uses. A badge that lies about
 * which backend you are talking to is worse than no badge. So the value is read on the
 * server, and only the resulting word crosses to the browser. No `"use client"` here, and
 * none in anything this renders.
 *
 * It lives beside the configuration it reads rather than in `shared/ui/`: that directory
 * holds design-system primitives that know no feature, and a component that knows what an
 * environment is is not one (`CONTEXT.md`, "Primitive vs composite").
 *
 * **The environment defaults to the validated config and is overridable.** The default is
 * written in the signature rather than at the call site so that it is evaluated when the
 * component runs, not when its JSX is created. The override is what lets a test render all
 * four environments without a process or a mocked resolver.
 *
 * Mount it once, in the root layout, when the app is scaffolded — see README.md.
 */

import { ENVIRONMENT_BADGE, type AppEnvironment } from "./environment";
import { getServerConfig } from "./server";

import styles from "./EnvironmentBadge.module.css";

export interface EnvironmentBadgeProps {
  /** Defaults to the validated server configuration. Set it only in a test. */
  readonly environment?: AppEnvironment;
}

export function EnvironmentBadge({
  environment = getServerConfig().environment,
}: EnvironmentBadgeProps = {}) {
  const badge = ENVIRONMENT_BADGE[environment];

  // Production is unbadged, and renders nothing rather than an empty node: a fixed-position
  // overlay with nothing in it is still an element on top of every page in the app.
  if (badge === null) return null;

  return (
    <div className={styles.anchor}>
      {/*
       * The visible word IS the accessible name — a `<span>` carrying text needs no
       * `aria-label`, and giving one to a generic element is a no-op the spec does not
       * promise to honour. Deliberately NOT hidden from a screen reader: this never
       * reaches a club, and a developer using one needs the fact a sighted one gets.
       */}
      <span className={styles.tag}>{badge}</span>
    </div>
  );
}
