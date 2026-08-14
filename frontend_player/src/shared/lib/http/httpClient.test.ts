/**
 * The chokepoint's own behaviour: the things that are true of every request in the app
 * because they are true here.
 */

import { AppError } from "@/shared/errors";
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  neverResponds,
  noContent,
  type Transport,
} from "@/test-support/transport";

import { configureHttp, httpRequest, resetHttp } from "./httpClient";
import { TIMEOUT_MS } from "./timeouts";

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  resetHttp();
});

afterEach(() => {
  transport.restore();
  resetHttp();
  jest.useRealTimers();
});

describe("the auth header", () => {
  it("is attached to an authenticated request", async () => {
    configureHttp({ getAccessToken: () => "token-1" });
    transport.on("GET", "/api/v1/users/me", () => json({ ok: true }));

    await httpRequest({ method: "GET", path: "/api/v1/users/me", authenticated: true });

    expect(transport.requests[0]?.headers.Authorization).toBe("Bearer token-1");
  });

  it("is absent from an unauthenticated request even when a token exists", async () => {
    // Login, refresh and registration must not carry a stale token: the endpoints that
    // take none are a different set from the endpoints that happen to have none.
    configureHttp({ getAccessToken: () => "token-1" });
    transport.on("POST", "/api/v1/auth/login", () => json({ ok: true }));

    await httpRequest({
      method: "POST",
      path: "/api/v1/auth/login",
      body: {},
      authenticated: false,
    });

    expect(transport.requests[0]?.headers.Authorization).toBeUndefined();
  });

  it("is absent when there is no session", async () => {
    configureHttp({ getAccessToken: () => undefined });
    transport.on("GET", "/api/v1/sports", () => json({ sports: [] }));

    await httpRequest({ method: "GET", path: "/api/v1/sports", authenticated: true });

    expect(transport.requests[0]?.headers.Authorization).toBeUndefined();
  });
});

describe("the timeout policy", () => {
  it("abandons a request the server never answers", async () => {
    jest.useFakeTimers();
    transport.on("GET", "/api/v1/sports", neverResponds());

    const pending = httpRequest({
      method: "GET",
      path: "/api/v1/sports",
      authenticated: false,
    });
    // Assert before advancing, or an unhandled rejection escapes the microtask queue.
    const assertion = expect(pending).rejects.toMatchObject({ kind: "timeout" });

    jest.advanceTimersByTime(TIMEOUT_MS.request + 1);

    await assertion;
  });

  it("uses the class the caller named, not one number for everything", async () => {
    jest.useFakeTimers();
    transport.on("GET", "/api/v1/sports", neverResponds());

    const pending = httpRequest({
      method: "GET",
      path: "/api/v1/sports",
      authenticated: false,
      timeout: "background",
    });
    const assertion = expect(pending).rejects.toMatchObject({ kind: "timeout" });

    // Past the interactive timeout, and the background request is still running.
    jest.advanceTimersByTime(TIMEOUT_MS.request + 1);
    await Promise.resolve();

    jest.advanceTimersByTime(TIMEOUT_MS.background);
    await assertion;
  });
});

describe("cancellation", () => {
  it("propagates an abort as an abort, not as a failure", async () => {
    // TanStack Query cancels a query on unmount. If that arrived as an `AppError` the
    // screen would render an error for work nobody was waiting for any more.
    const controller = new AbortController();
    transport.on("GET", "/api/v1/sports", neverResponds());

    const pending = httpRequest({
      method: "GET",
      path: "/api/v1/sports",
      authenticated: false,
      signal: controller.signal,
    });
    const assertion = expect(pending).rejects.toMatchObject({ name: "AbortError" });

    controller.abort();

    await assertion;
  });
});

describe("normalizing failures", () => {
  it("turns an error envelope into an AppError carrying its code", async () => {
    transport.on("GET", "/api/v1/assessments/x", () =>
      errorResponse(409, "question_not_outstanding"),
    );

    await expect(
      httpRequest({
        method: "GET",
        path: "/api/v1/assessments/x",
        authenticated: false,
      }),
    ).rejects.toMatchObject({
      name: "AppError",
      code: "question_not_outstanding",
      status: 409,
      traceId: "trace-test",
    });
  });

  it("turns an unreachable server into an AppError, not a raw TypeError", async () => {
    transport.on("GET", "/api/v1/sports", networkFailure());

    const failure = await httpRequest({
      method: "GET",
      path: "/api/v1/sports",
      authenticated: false,
    }).catch((error: unknown) => error);

    // Raw fetch rejections must never reach a screen.
    expect(failure).toBeInstanceOf(AppError);
    expect((failure as AppError).kind).toBe("network-unavailable");
  });
});

describe("decoding", () => {
  it("returns undefined for a 204 rather than failing to parse an empty body", async () => {
    transport.on("POST", "/api/v1/assessments/x/abandonment", () => noContent());

    await expect(
      httpRequest({
        method: "POST",
        path: "/api/v1/assessments/x/abandonment",
        authenticated: false,
      }),
    ).resolves.toBeUndefined();
  });
});

describe("the request itself", () => {
  it("carries a correlation id in the alphabet the backend accepts", async () => {
    transport.on("GET", "/api/v1/sports", () => json({ sports: [] }));

    await httpRequest({ method: "GET", path: "/api/v1/sports", authenticated: false });

    const id = transport.requests[0]?.headers["X-Request-ID"];
    // Anything outside this pattern the backend discards and replaces, which would leave
    // a client-side failure tied to nothing.
    expect(id).toMatch(/^[A-Za-z0-9._-]{1,64}$/);
  });

  it("gives every request its own id", async () => {
    transport.on("GET", "/api/v1/sports", () => json({ sports: [] }));

    await httpRequest({ method: "GET", path: "/api/v1/sports", authenticated: false });
    await httpRequest({ method: "GET", path: "/api/v1/sports", authenticated: false });

    expect(transport.requests[0]?.headers["X-Request-ID"]).not.toBe(
      transport.requests[1]?.headers["X-Request-ID"],
    );
  });

  it("resolves the path against the configured API base URL", async () => {
    transport.on("GET", "/api/v1/sports", () => json({ sports: [] }));

    await httpRequest({ method: "GET", path: "/api/v1/sports", authenticated: false });

    expect(transport.requests[0]?.path).toBe("/api/v1/sports");
  });
});
