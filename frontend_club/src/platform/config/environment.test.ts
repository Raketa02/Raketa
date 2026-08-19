import { describe, expect, it } from "vitest";

import {
  ENVIRONMENT_BADGE,
  ENVIRONMENTS,
  REQUIRED_SCHEME,
  type AppEnvironment,
} from "./environment";

describe("the environment vocabulary", () => {
  it("is exactly the four names all three apps use", () => {
    expect(ENVIRONMENTS).toEqual(["local", "development", "staging", "production"]);
  });

  it("has no synonyms and no leftover abbreviations", () => {
    const names: readonly string[] = ENVIRONMENTS;

    for (const rejected of ["dev", "prod", "test", "stage", "prd"]) {
      expect(names).not.toContain(rejected);
    }
  });
});

/**
 * The scheme a **public-network** URL must use. Every deployed environment is reached over
 * TLS; `local` is `null`, meaning either. Asserted as a table so a retune that quietly
 * flipped one is a red test rather than a cookie transmitted in clear.
 *
 * `null` for `local` is not "unset": a laptop is legitimately reachable over either, and a
 * tunnel — which is how a device reaches a laptop at all — hands back `https://`.
 */
describe("the public-network scheme rule", () => {
  it("requires https:// for every deployed environment and constrains local no further", () => {
    expect(REQUIRED_SCHEME).toEqual({
      local: null,
      development: "https://",
      staging: "https://",
      production: "https://",
    });
  });

  it("covers every environment", () => {
    expect(Object.keys(REQUIRED_SCHEME).sort()).toEqual([...ENVIRONMENTS].sort());
  });

  // The claim that makes the table a security rule rather than a convention: no deployed
  // environment may be reached in the clear, whatever else is retuned.
  it("leaves no deployed environment reachable over http://", () => {
    for (const environment of ENVIRONMENTS) {
      if (environment === "local") continue;
      expect(REQUIRED_SCHEME[environment]).toBe("https://");
    }
  });
});

/**
 * The badge table. Production is the only unbadged environment, and that is asserted as an
 * exclusive claim rather than as one case: the failure worth catching is a *new*
 * environment silently inheriting production's clean look, which is invisible.
 */
describe("the badge table", () => {
  it("covers every environment", () => {
    expect(Object.keys(ENVIRONMENT_BADGE).sort()).toEqual([...ENVIRONMENTS].sort());
  });

  it("matches the labels the player app uses, so the two apps read the same", () => {
    expect(ENVIRONMENT_BADGE).toEqual({
      local: "LOCAL",
      development: "DEVELOPMENT",
      staging: "STAGING",
      production: null,
    });
  });

  it("badges production with nothing, and is the only environment that is unbadged", () => {
    const unbadged = ENVIRONMENTS.filter(
      (environment: AppEnvironment) => ENVIRONMENT_BADGE[environment] === null,
    );

    expect(unbadged).toEqual(["production"]);
  });

  it("gives every other environment a word, never an empty pill", () => {
    for (const environment of ENVIRONMENTS) {
      const badge = ENVIRONMENT_BADGE[environment];

      if (environment === "production") continue;
      expect(badge).toBeTruthy();
    }
  });

  it("gives distinct labels, so a screenshot can never be ambiguous", () => {
    const labels = Object.values(ENVIRONMENT_BADGE).filter((label) => label !== null);

    expect(new Set(labels).size).toBe(labels.length);
  });
});
