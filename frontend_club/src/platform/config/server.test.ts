import { describe, expect, it } from "vitest";

import { ConfigError, ENVIRONMENTS, type AppEnvironment } from "./environment";
import { parseServerConfig, type RawServerEnv } from "./server";

/** The only environment that runs today, and the only one an `http://` URL is legal in. */
const valid = {
  APP_ENV: "local",
  BACKEND_API_URL: "http://localhost:8000",
  SESSION_COOKIE_NAME: "rakieta_club_session",
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
    BACKEND_API_URL: "https://api.rakieta.app",
    SESSION_COOKIE_NAME: "rakieta_club_session",
    NEXT_PUBLIC_APP_URL: "https://club.rakieta.app",
  };
}

describe("parseServerConfig", () => {
  it("maps a valid environment onto the app configuration", () => {
    expect(parseServerConfig(valid)).toEqual({
      environment: "local",
      backendApiUrl: "http://localhost:8000",
      appUrl: "http://localhost:3000",
      session: { name: "rakieta_club_session", secure: false },
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
 * The scheme rule, in both directions and at every environment. `local` is a laptop over
 * `http://`; the three deployed environments are reached over TLS.
 *
 * The consequence the ticket wants falls out of it rather than needing a check of its own:
 * with no domain registered, selecting `staging` today fails at start, because the only
 * reachable backend is an `http://` one.
 */
describe("the scheme rule", () => {
  it("requires http:// for local", () => {
    const raw = { ...valid, BACKEND_API_URL: "https://api.rakieta.app" };

    expect(() => parseServerConfig(raw)).toThrow(/BACKEND_API_URL/);
    expect(() => parseServerConfig(raw)).toThrow(/http:\/\//);
  });

  it.each(DEPLOYED)("requires https:// for %s", (environment) => {
    const raw = { ...validFor(environment), BACKEND_API_URL: "http://localhost:8000" };

    expect(() => parseServerConfig(raw)).toThrow(ConfigError);
    expect(() => parseServerConfig(raw)).toThrow(/BACKEND_API_URL/);
  });

  it.each(DEPLOYED)("applies the same rule to the app's own origin in %s", (environment) => {
    const raw = { ...validFor(environment), NEXT_PUBLIC_APP_URL: "http://localhost:3000" };

    expect(() => parseServerConfig(raw)).toThrow(/NEXT_PUBLIC_APP_URL/);
  });

  it("names the environment as the reason and the URL as the problem", () => {
    try {
      parseServerConfig({ ...validFor("staging"), BACKEND_API_URL: "http://api.rakieta.app" });
      throw new Error("expected parseServerConfig to reject");
    } catch (error) {
      const { message } = error as ConfigError;

      expect(message).toContain("BACKEND_API_URL");
      expect(message).toContain("staging");
    }
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
    const raw = { ...validFor(environment), BACKEND_API_URL: "localhost:8000" };

    expect(() => parseServerConfig(raw)).toThrow(/BACKEND_API_URL/);
    expect(() => parseServerConfig(raw)).not.toThrow(/when APP_ENV/);
  });

  it.each(ENVIRONMENTS)("reports one problem, not two, for one typo in %s", (environment) => {
    try {
      parseServerConfig({ ...validFor(environment), BACKEND_API_URL: "localhost:8000" });
      throw new Error("expected parseServerConfig to reject");
    } catch (error) {
      const { message } = error as ConfigError;

      expect(message.match(/BACKEND_API_URL/g)).toHaveLength(1);
    }
  });

  it.each(ENVIRONMENTS)("rejects a non-HTTP scheme in %s", (environment) => {
    const raw = { ...validFor(environment), BACKEND_API_URL: "ftp://api.rakieta.app" };

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
