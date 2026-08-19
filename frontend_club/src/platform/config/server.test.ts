import { describe, expect, it } from "vitest";

import { ConfigError, ENVIRONMENTS, type AppEnvironment } from "./environment";
import { parseServerConfig, type RawServerEnv } from "./server";

/** The only environment that runs today. */
const valid = {
  APP_ENV: "local",
  BACKEND_API_URL: "http://localhost:8000",
  SESSION_COOKIE_NAME: "raketa_club_session",
  NEXT_PUBLIC_APP_URL: "http://localhost:3000",
} as const satisfies RawServerEnv;

/** The three deployed environments. None is provisioned — no domain is registered yet. */
const DEPLOYED: readonly AppEnvironment[] = ["development", "staging", "production"];

/** The valid configuration minus one variable, so a missing one can be tested at a time. */
function without(name: keyof RawServerEnv, raw: RawServerEnv = valid): RawServerEnv {
  const copy: { -readonly [K in keyof RawServerEnv]: RawServerEnv[K] } = { ...raw };
  delete copy[name];
  return copy;
}

/** A valid configuration for any environment, so one field can be varied at a time. */
function validFor(environment: AppEnvironment): RawServerEnv {
  if (environment === "local") return valid;

  return {
    APP_ENV: environment,
    BACKEND_API_URL: "https://api.raketa.example",
    SESSION_COOKIE_NAME: "raketa_club_session",
    NEXT_PUBLIC_APP_URL: "https://club.raketa.example",
  };
}

describe("parseServerConfig", () => {
  it("maps a valid environment onto the app configuration", () => {
    expect(parseServerConfig(valid)).toEqual({
      environment: "local",
      backendApiUrl: "http://localhost:8000",
      appUrl: "http://localhost:3000",
      session: { name: "raketa_club_session", secure: false },
    });
  });

  it.each([
    ["APP_ENV"],
    ["BACKEND_API_URL"],
    ["SESSION_COOKIE_NAME"],
    ["NEXT_PUBLIC_APP_URL"],
  ] as const)("rejects a missing %s and names the variable", (name) => {
    const raw = without(name);

    expect(() => parseServerConfig(raw)).toThrow(ConfigError);
    expect(() => parseServerConfig(raw)).toThrow(new RegExp(name));
  });

  it("names every offending variable when several are wrong at once", () => {
    try {
      parseServerConfig({});
      throw new Error("expected parseServerConfig to reject");
    } catch (error) {
      const { message } = error as ConfigError;

      expect(message).toContain("APP_ENV");
      expect(message).toContain("BACKEND_API_URL");
      expect(message).toContain("SESSION_COOKIE_NAME");
      expect(message).toContain("NEXT_PUBLIC_APP_URL");
    }
  });

  it("tells the reader how to fix it", () => {
    expect(() => parseServerConfig({})).toThrow(/\.env\.example/);
  });
});

/**
 * The no-echo rule. Config lands in logs and crash reports, and a URL can carry
 * credentials — so a refusal names the variable and never its value.
 *
 * The environment name is the one thing a message may mention, and only as a *reason*:
 * it is not a secret and is already on every log record.
 */
describe("the failure messages", () => {
  it("never puts a config value in the message", () => {
    const secretish = "https://user:hunter2@api.example.com";

    try {
      parseServerConfig({ ...valid, BACKEND_API_URL: secretish, APP_ENV: "kittens" });
      throw new Error("expected parseServerConfig to reject");
    } catch (error) {
      expect(error).toBeInstanceOf(ConfigError);
      expect((error as ConfigError).message).not.toContain("hunter2");
      expect((error as ConfigError).message).not.toContain(secretish);
    }
  });

  /**
   * zod's own `invalid_enum_value` text ends `received '…'`, so the enum needs an
   * errorMap to obey the rule above. The rejected value here is deliberately not a
   * substring of any legal name: `dev` and `prod` are substrings of `development` and
   * `production`, which is what makes a naive no-echo assertion pass by accident.
   */
  it("does not echo a rejected environment name", () => {
    try {
      parseServerConfig({ ...valid, APP_ENV: "kittens" });
      throw new Error("expected parseServerConfig to reject");
    } catch (error) {
      expect((error as ConfigError).message).not.toContain("kittens");
      expect((error as ConfigError).message).toContain("local, development, staging, production");
    }
  });

  it("does not echo a rejected cookie name", () => {
    try {
      parseServerConfig({ ...valid, SESSION_COOKIE_NAME: "session id=oops" });
      throw new Error("expected parseServerConfig to reject");
    } catch (error) {
      expect((error as ConfigError).message).toContain("SESSION_COOKIE_NAME");
      expect((error as ConfigError).message).not.toContain("oops");
    }
  });
});

/**
 * The four names are the same four the backend and the player app use. A fifth spelling
 * here would mean the three apps disagree about where they are running, which is the
 * failure the shared vocabulary exists to remove.
 */
describe("the environment names", () => {
  it("is exactly the four, in the order the platform spells them", () => {
    expect(ENVIRONMENTS).toEqual(["local", "development", "staging", "production"]);
  });

  it.each(ENVIRONMENTS)("accepts %s", (environment) => {
    expect(parseServerConfig(validFor(environment)).environment).toBe(environment);
  });

  // `dev` and `prod` are the spellings the backend used to accept and no longer does;
  // `test` is the fifth name that was deliberately never introduced — a test run happens
  // on a laptop or a CI runner, both of which are `local`.
  it.each(["dev", "prod", "production ", "Local", "test", "", "PRODUCTION"])(
    "rejects %p and names the variable",
    (environment) => {
      const raw = { ...valid, APP_ENV: environment };

      expect(() => parseServerConfig(raw)).toThrow(ConfigError);
      expect(() => parseServerConfig(raw)).toThrow(/APP_ENV/);
    },
  );
});

/**
 * The scheme rule applies to a URL that crosses a **public network**, and to no other.
 *
 * `NEXT_PUBLIC_APP_URL` is the origin a browser visits, so a deployed environment must be
 * `https://` — `http://` there is a session cookie in the clear. `BACKEND_API_URL` is
 * server-to-server and carries no scheme rule at all: a cluster-internal
 * `http://backend.svc.cluster.local:8000` never leaves the cluster. #96 implemented the
 * blanket rule its AC specified and reported that it refuses exactly that address; this is
 * where #99 settles it, and it is the same settlement that lets the player app's `local`
 * accept an https tunnel.
 *
 * `local` is `null` in the table: either scheme, on both URLs.
 */
describe("the public-network scheme rule", () => {
  it.each(DEPLOYED)("requires https:// for the browser-facing origin in %s", (environment) => {
    const raw = { ...validFor(environment), NEXT_PUBLIC_APP_URL: "http://localhost:3000" };

    expect(() => parseServerConfig(raw)).toThrow(ConfigError);
    expect(() => parseServerConfig(raw)).toThrow(/NEXT_PUBLIC_APP_URL/);
  });

  it("accepts either scheme for the browser-facing origin in local", () => {
    const raw = { ...valid, NEXT_PUBLIC_APP_URL: "https://club.localhost.example" };

    expect(parseServerConfig(raw).appUrl).toBe("https://club.localhost.example");
  });

  /**
   * The reason the rule was widened. A server tier calling another over the cluster network
   * is the ordinary deployed topology, and refusing it would push an operator into either
   * terminating TLS they do not need or editing this schema.
   */
  it.each(DEPLOYED)("accepts a cluster-internal http:// backend origin in %s", (environment) => {
    const raw = {
      ...validFor(environment),
      BACKEND_API_URL: "http://backend.svc.cluster.local:8000",
    };

    expect(parseServerConfig(raw).backendApiUrl).toBe("http://backend.svc.cluster.local:8000");
  });

  it("accepts an https:// backend origin in local", () => {
    const raw = { ...valid, BACKEND_API_URL: "https://api.raketa.example" };

    expect(parseServerConfig(raw).backendApiUrl).toBe("https://api.raketa.example");
  });

  it("names the environment as the reason and the URL as the problem", () => {
    try {
      parseServerConfig({
        ...validFor("staging"),
        NEXT_PUBLIC_APP_URL: "http://club.raketa.example",
      });
      throw new Error("expected parseServerConfig to reject");
    } catch (error) {
      const { message } = error as ConfigError;

      expect(message).toContain("NEXT_PUBLIC_APP_URL");
      expect(message).toContain("staging");
    }
  });

  /**
   * Dropping the rule from `BACKEND_API_URL` moved the unprovisioned-environment refusal
   * onto one variable rather than two, so it is asserted directly rather than left to fall
   * out. A `local` configuration whose `APP_ENV` alone is changed must still not start.
   */
  it.each(DEPLOYED)("still refuses a wholly local configuration relabelled %s", (environment) => {
    expect(() => parseServerConfig({ ...valid, APP_ENV: environment })).toThrow(ConfigError);
  });

  /**
   * A malformed URL is reported as a malformed URL and never *also* as a scheme mismatch.
   *
   * This does not come for free, and the first draft got it wrong: a failing `.url()`
   * leaves zod's result dirty rather than aborting it, so the object-level refinement ran
   * over the rejected string anyway and `localhost:8000` produced two complaints — the
   * second of them naming the environment, which is not what is wrong. `requireScheme`
   * re-runs the field and stays silent unless it passes.
   */
  it.each(ENVIRONMENTS)("rejects a scheme-less host:port in %s", (environment) => {
    for (const field of ["BACKEND_API_URL", "NEXT_PUBLIC_APP_URL"] as const) {
      const raw = { ...validFor(environment), [field]: "localhost:8000" };

      expect(() => parseServerConfig(raw)).toThrow(new RegExp(field));
      expect(() => parseServerConfig(raw)).not.toThrow(/when APP_ENV/);
    }
  });

  it.each(ENVIRONMENTS)("reports one problem, not two, for one typo in %s", (environment) => {
    for (const field of ["BACKEND_API_URL", "NEXT_PUBLIC_APP_URL"] as const) {
      try {
        parseServerConfig({ ...validFor(environment), [field]: "localhost:8000" });
        throw new Error("expected parseServerConfig to reject");
      } catch (error) {
        const { message } = error as ConfigError;

        expect(message.match(new RegExp(field, "g"))).toHaveLength(1);
      }
    }
  });

  it.each(ENVIRONMENTS)("rejects a non-HTTP scheme in %s", (environment) => {
    const raw = { ...validFor(environment), BACKEND_API_URL: "ftp://api.raketa.example" };

    expect(() => parseServerConfig(raw)).toThrow(/BACKEND_API_URL/);
  });
});

/**
 * The security footgun this ticket removes. `Secure` used to be an independent variable,
 * so a deployed environment could be configured to transmit its session in clear — and it
 * would look deliberate, because somebody typed it.
 */
describe("the session cookie", () => {
  it("derives Secure=false for local, the only environment without TLS", () => {
    expect(parseServerConfig(valid).session.secure).toBe(false);
  });

  it.each(DEPLOYED)("derives Secure=true for %s", (environment) => {
    expect(parseServerConfig(validFor(environment)).session.secure).toBe(true);
  });

  /**
   * Refused rather than ignored. Silently dropping a stale `SESSION_COOKIE_SECURE=false`
   * would leave an operator believing a security control is in effect that nothing reads.
   */
  it.each(["false", "true", ""])(
    "refuses SESSION_COOKIE_SECURE=%p rather than ignoring it",
    (value) => {
      const raw = { ...valid, SESSION_COOKIE_SECURE: value };

      expect(() => parseServerConfig(raw)).toThrow(ConfigError);
      expect(() => parseServerConfig(raw)).toThrow(/SESSION_COOKIE_SECURE/);
      expect(() => parseServerConfig(raw)).toThrow(/derived/);
    },
  );

  it("accepts a configuration that simply omits it", () => {
    expect(() => parseServerConfig(valid)).not.toThrow();
  });

  it("carries the configured cookie name through", () => {
    const raw = { ...valid, SESSION_COOKIE_NAME: "rk_sess" };

    expect(parseServerConfig(raw).session.name).toBe("rk_sess");
  });

  // A name with a space or a separator produces a Set-Cookie header browsers silently
  // drop, which presents as "login does nothing".
  it.each(["session id", "session;id", "session=id", "session\tid", "sesión", ""])(
    "rejects the cookie name %p",
    (name) => {
      expect(() => parseServerConfig({ ...valid, SESSION_COOKIE_NAME: name })).toThrow(
        /SESSION_COOKIE_NAME/,
      );
    },
  );
});

/**
 * The rule ADR-0007 exists for. `BACKEND_API_URL` is server-only; the browser must never
 * learn the FastAPI origin, and a `NEXT_PUBLIC_` twin would put it in the bundle.
 */
describe("the server-only boundary", () => {
  it("does not accept a NEXT_PUBLIC_ spelling of the backend origin", () => {
    const raw = {
      ...without("BACKEND_API_URL"),
      NEXT_PUBLIC_BACKEND_API_URL: "http://localhost:8000",
    } as RawServerEnv;

    expect(() => parseServerConfig(raw)).toThrow(/BACKEND_API_URL/);
  });

  /**
   * The environment is server-only too, and is deliberately not mirrored into a public
   * variable — the badge reads this value through a Server Component instead, so there is
   * exactly one copy. A `NEXT_PUBLIC_` spelling must not satisfy the schema.
   */
  it("does not accept a NEXT_PUBLIC_ spelling of the environment", () => {
    const raw = { ...without("APP_ENV"), NEXT_PUBLIC_APP_ENV: "local" } as RawServerEnv;

    expect(() => parseServerConfig(raw)).toThrow(/APP_ENV/);
  });
});
