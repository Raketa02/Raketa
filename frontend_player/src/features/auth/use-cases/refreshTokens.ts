/**
 * The wire half of a token rotation.
 *
 * Deliberately thin, and deliberately *only* this. The rotation's policy — one flight at
 * a time, when a 401 earns a refresh, whether a failure ends the session, the single
 * retry — lives in `shared/lib/http` and `shared/lib/auth/refreshCoordinator`, which is
 * where a reader looks for it and where it cannot be re-implemented per feature.
 *
 * What lives here is the one thing that cannot live there: the endpoint's path and its
 * generated types. `api/` and `mappers/` are the only layers allowed to read
 * `src/generated/`, and `shared/` may never import a feature — so the coordinator takes
 * this function rather than importing it, exactly as the bootstrap sequence takes
 * `restoreSession`.
 *
 * Nothing is caught. The coordinator classifies the failure, and it can only do that if
 * the `AppError` reaches it intact.
 */

import type { Tokens } from "@/shared/lib/auth";

import { refresh } from "../api/authApi";
import { toTokens } from "../mappers/authMappers";

export async function refreshTokens(refreshToken: string): Promise<Tokens> {
  return toTokens(await refresh({ refresh_token: refreshToken }));
}
