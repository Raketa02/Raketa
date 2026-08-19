import { describe, expect, it } from "vitest";

import { ConfigError } from "./environment";
import { parsePublicConfig, type RawPublicEnv } from "./public";

const valid = { NEXT_PUBLIC_APP_URL: "http://localhost:3000" } as const satisfies RawPublicEnv;

describe("parsePublicConfig", () => {
  it("maps a valid environment onto the public configuration", () => {
    expect(parsePublicConfig(valid)).toEqual({ appUrl: "http://localhost:3000" });
  });

  it("rejects a missing app URL and names the variable", () => {
    expect(() => parsePublicConfig({})).toThrow(ConfigError);
    expect(() => parsePublicConfig({})).toThrow(/NEXT_PUBLIC_APP_URL/);
  });

  it.each(["nonsense", "localhost:3000", "ftp://club.raketa.example", ""])(
    "rejects %p",
    (appUrl) => {
      expect(() => parsePublicConfig({ NEXT_PUBLIC_APP_URL: appUrl })).toThrow(
        /NEXT_PUBLIC_APP_URL/,
      );
    },
  );

  /**
   * The rejected value is an `ftp://` URL rather than a mangled `https://` one on purpose:
   * WHATWG parsing trims surrounding whitespace, so `"https://x " ` is a *valid* URL and
   * the first draft of this case asserted nothing. A non-HTTP scheme is refused by the
   * field itself, which is the path a real typo takes.
   */
  it("never puts a config value in the failure message", () => {
    const secretish = "ftp://user:hunter2@club.example.com/x?token=abc";

    try {
      parsePublicConfig({ NEXT_PUBLIC_APP_URL: secretish });
      throw new Error("expected parsePublicConfig to reject");
    } catch (error) {
      expect(error).toBeInstanceOf(ConfigError);
      expect((error as ConfigError).message).not.toContain("hunter2");
      expect((error as ConfigError).message).not.toContain("abc");
    }
  });
});

/**
 * What is *absent* from the public schema is the point (§20.1). Anything named
 * `NEXT_PUBLIC_*` is inlined into the JavaScript the browser downloads, so the schema is
 * the list of things this app has decided are safe to publish.
 *
 * These assertions are about the resulting object rather than about the code, so they stay
 * true however the schema is rewritten.
 */
describe("what the browser is allowed to know", () => {
  it("is exactly the app's own origin, and nothing else", () => {
    expect(Object.keys(parsePublicConfig(valid))).toEqual(["appUrl"]);
  });

  /**
   * The backend origin is server-only (ADR-0007). A `NEXT_PUBLIC_` twin would put the
   * FastAPI origin in the bundle and invite the browser to call it directly, bypassing the
   * BFF's session and CSRF handling.
   */
  it("does not carry the FastAPI origin, even when one is offered", () => {
    const raw = {
      ...valid,
      NEXT_PUBLIC_BACKEND_API_URL: "https://api.raketa.example",
    } as RawPublicEnv;

    expect(parsePublicConfig(raw)).toEqual({ appUrl: "http://localhost:3000" });
  });

  /**
   * The environment is server-only too. A public mirror is a second copy of the same fact,
   * free to disagree with the one the BFF uses — and the badge, which is the only thing
   * that wants it, is a Server Component precisely so that no mirror is needed.
   */
  it("does not carry the environment, even when one is offered", () => {
    const raw = { ...valid, NEXT_PUBLIC_APP_ENV: "production" } as RawPublicEnv;

    expect(parsePublicConfig(raw)).toEqual({ appUrl: "http://localhost:3000" });
  });

  it("does not carry the session cookie policy", () => {
    const config = parsePublicConfig(valid);

    expect(config).not.toHaveProperty("session");
    expect(config).not.toHaveProperty("secure");
  });
});
