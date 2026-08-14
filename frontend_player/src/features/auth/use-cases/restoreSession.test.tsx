/**
 * Relaunch: what the app concludes from what it finds in the keychain.
 *
 * Two of these — the rejected token and the unreachable server — are the reason the step
 * exists at all. They look identical from the app's side (a stored token, a failed
 * validation) and demand opposite behaviour.
 */

import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react-native";
import { Text } from "react-native";

import {
  beginSession,
  clearStoredTokens,
  getSessionStatus,
  hasTokens,
  resetSessionStatus,
  useSessionStatus,
  wireHttpCredentials,
} from "@/shared/lib/auth";
import { BootstrapGate, bootstrapApp } from "@/shared/lib/bootstrap";
import { queryClient } from "@/shared/lib/query-client";
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  type Transport,
  type Wire,
} from "@/test-support/transport";

import { authKeys } from "../hooks/authKeys";

import { restoreSession } from "./restoreSession";

const USER: Wire["UserResponse"] = {
  id: "11111111-2222-4333-8444-555555555555",
  email: "ada@example.com",
  nickname: "ada",
  authority: "player",
  is_admin: false,
  is_active: true,
};

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials();
  await clearStoredTokens();
  queryClient.clear();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

/** A previous run of the app that ended with a signed-in player. */
async function credentialsOnDevice() {
  await beginSession({ accessToken: "access-1", refreshToken: "refresh-1" });
  resetSessionStatus(); // the process restarted; only the keychain survived
}

describe("relaunching", () => {
  it("restores the session when the server still recognises the token", async () => {
    await credentialsOnDevice();
    transport.on("GET", "/api/v1/users/me", () => json(USER));

    const restored = await restoreSession();

    expect(restored.status).toBe("authenticated");
    expect(getSessionStatus()).toBe("authenticated");
    expect(restored.user).toEqual({
      id: USER.id,
      email: USER.email,
      nickname: USER.nickname,
    });
  });

  it("sends the stored token on the validation request", async () => {
    await credentialsOnDevice();
    transport.on("GET", "/api/v1/users/me", () => json(USER));

    await restoreSession();

    const [validation] = transport.requestsTo("GET", "/api/v1/users/me");
    expect(validation?.headers.Authorization).toBe("Bearer access-1");
  });

  it("is signed out when the device holds no credentials", async () => {
    const restored = await restoreSession();

    expect(restored.status).toBe("unauthenticated");
    expect(getSessionStatus()).toBe("unauthenticated");
    // Nothing was asked of the server: an unauthenticated launch that fires an
    // authenticated request can only 401.
    expect(transport.requests).toHaveLength(0);
  });

  it("discards a token the server no longer recognises", async () => {
    // The iOS reinstall case: Keychain data outlives the app, so a fresh install can
    // start life holding a credential the backend retired months ago.
    await credentialsOnDevice();
    transport.on("GET", "/api/v1/users/me", () =>
      errorResponse(401, "access_token_invalid"),
    );

    const restored = await restoreSession();

    expect(restored.status).toBe("unauthenticated");
    expect(hasTokens()).toBe(false);
  });

  it("keeps the session when the server could not be reached", async () => {
    // Unreachable is not rejected. Destroying a valid session — and costing someone
    // their password — because a tunnel swallowed one request is the worst outcome here,
    // and it is the easy mistake.
    await credentialsOnDevice();
    transport.on("GET", "/api/v1/users/me", networkFailure());

    const restored = await restoreSession();

    expect(restored.status).toBe("authenticated");
    expect(hasTokens()).toBe(true);
  });

  it("keeps the session when the server itself failed", async () => {
    await credentialsOnDevice();
    transport.on("GET", "/api/v1/users/me", () => errorResponse(503, "internal_error"));

    const restored = await restoreSession();

    expect(restored.status).toBe("authenticated");
    expect(hasTokens()).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// The launch sequence, rendered — no flash in either direction
// ---------------------------------------------------------------------------

/** Stands in for the route tree: it names whichever branch the guard would render. */
function TreeUnderTest() {
  const status = useSessionStatus();
  return <Text>{status === "authenticated" ? "Signed in" : "Sign in"}</Text>;
}

function renderLaunch() {
  const seen: string[] = [];

  const run = () =>
    bootstrapApp({
      validateConfig: () => {},
      wirePlatformManagers: () => {},
      wireCredentials: wireHttpCredentials,
      restoreSession: async () => {
        const restored = await restoreSession();
        if (restored.user !== undefined) {
          queryClient.setQueryData(authKeys.currentUser(), restored.user);
        }
      },
      loadFonts: async () => {},
    });

  render(
    <QueryClientProvider client={queryClient}>
      <BootstrapGate run={run}>
        <Recorder seen={seen} />
      </BootstrapGate>
    </QueryClientProvider>,
  );

  return seen;
}

function Recorder({ seen }: { readonly seen: string[] }) {
  const status = useSessionStatus();
  seen.push(status);
  return <TreeUnderTest />;
}

describe("the launch sequence", () => {
  it("shows the authenticated tree with no login-screen flash", async () => {
    await credentialsOnDevice();
    transport.on("GET", "/api/v1/users/me", () => json(USER));

    const seen = renderLaunch();

    expect(await screen.findByText("Signed in")).toBeTruthy();
    // The tree renders only after the sequence resolves, so it was never mounted while
    // the status was still `bootstrapping` — which is what a login-screen flash is.
    expect(seen).not.toContain("bootstrapping");
    expect(seen).not.toContain("unauthenticated");
  });

  it("shows the sign-in tree with no authenticated-tree flash", async () => {
    const seen = renderLaunch();

    expect(await screen.findByText("Sign in")).toBeTruthy();
    expect(seen).not.toContain("bootstrapping");
    expect(seen).not.toContain("authenticated");
  });

  it("seeds the profile it already fetched, so the first screen does not refetch", async () => {
    await credentialsOnDevice();
    transport.on("GET", "/api/v1/users/me", () => json(USER));

    renderLaunch();

    await waitFor(() =>
      expect(queryClient.getQueryData(authKeys.currentUser())).toEqual({
        id: USER.id,
        email: USER.email,
        nickname: USER.nickname,
      }),
    );
    expect(transport.requestsTo("GET", "/api/v1/users/me")).toHaveLength(1);
  });
});
