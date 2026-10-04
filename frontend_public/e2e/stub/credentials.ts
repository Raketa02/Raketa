/**
 * **The fake credentials**: the stub's default answers to the invitation and reset links, keeping
 * the backend's rules, so a test seats only the links it is about
 * (`credentials.invite(token, …)`, `credentials.reset(token)`).
 *
 * - Reading a link changes nothing, whatever its state; a link never issued is
 *   `404 credential_not_found`, and an invitation's code is only told while the link is valid.
 * - Setting a password by a link that no longer works is `409 credential_<state>`; setting it by a
 *   valid one answers `204`, signs nobody in, and spends the link.
 * - An invitation to an email that has an account by now is accepted from the app, signed in:
 *   `409 sign_in_to_accept`.
 *
 * The password rule is not restated: the site refuses a weak password before it asks, and a test
 * about the backend refusing one overrides the operation.
 */

import type { components } from '../../src/generated/schema';

import { refusal, type StubBackend } from './backend';

export type InvitationPageResponse = components['schemas']['InvitationPageResponse'];
export type LinkState = components['schemas']['InvitationLinkState'];

export const INVITATION_READ = '/api/v1/public/invitations/by-token';
export const INVITATION_PASSWORD = '/api/v1/public/invitations/password';
export const RESET_READ = '/api/v1/public/password-resets/by-token';
export const RESET_PASSWORD = '/api/v1/public/password-resets/password';

/**
 * A token as the backend mints one: 43 URL-safe characters, `-` and `_` among them. Unique per
 * `n`, so no two tests share a link.
 */
export function token(n: number): string {
  return `Zq-_${String(n).padStart(4, '0')}${'x7Y'.repeat(11)}plK`.slice(0, 43);
}

/** Marta, invited by Ogrody 33 to be an administrator (#526). */
export function invitation(
  overrides: Partial<InvitationPageResponse> = {},
): InvitationPageResponse {
  return {
    name: 'Marta Wójcik',
    club_name: 'Ogrody 33',
    state: 'valid',
    code: 'K7PQ2MXA',
    ...overrides,
  };
}

interface SeatedInvitation {
  page: InvitationPageResponse;
  /** The email has an account by now, which accepts from the app. */
  accountExists: boolean;
}

export class FakeCredentials {
  private readonly invitations = new Map<string, SeatedInvitation>();
  private readonly resets = new Map<string, LinkState>();

  constructor(private readonly stub: StubBackend) {}

  install(): this {
    this.stub.on('post', INVITATION_READ, ({ body }) => {
      const seated = this.invitations.get(body.token);
      if (seated === undefined) return { status: 404, body: refusal('credential_not_found') };
      const { page } = seated;
      return { status: 200, body: { ...page, code: page.state === 'valid' ? page.code : null } };
    });
    this.stub.on('post', INVITATION_PASSWORD, ({ body }) => {
      const seated = this.invitations.get(body.token);
      if (seated === undefined) return { status: 404, body: refusal('credential_not_found') };
      if (seated.page.state !== 'valid') {
        return { status: 409, body: refusal(`credential_${seated.page.state}`) };
      }
      if (seated.accountExists) return { status: 409, body: refusal('sign_in_to_accept') };
      seated.page = { ...seated.page, state: 'used' };
      return { status: 204, body: undefined };
    });
    this.stub.on('post', RESET_READ, ({ body }) => {
      const state = this.resets.get(body.token);
      return state === undefined
        ? { status: 404, body: refusal('credential_not_found') }
        : { status: 200, body: { state } };
    });
    this.stub.on('post', RESET_PASSWORD, ({ body }) => {
      const state = this.resets.get(body.token);
      if (state === undefined) return { status: 404, body: refusal('credential_not_found') };
      if (state !== 'valid') return { status: 409, body: refusal(`credential_${state}`) };
      this.resets.set(body.token, 'used');
      return { status: 204, body: undefined };
    });
    return this;
  }

  /** Seat an invitation behind a link's token. */
  invite(
    linkToken: string,
    page: InvitationPageResponse = invitation(),
    { accountExists = false } = {},
  ): void {
    this.invitations.set(linkToken, { page, accountExists });
  }

  /** Seat a player's or an administrator's reset behind a link's token. */
  reset(linkToken: string, state: LinkState = 'valid'): void {
    this.resets.set(linkToken, state);
  }

  /** The link was never sent, as far as the backend can tell: `credential_not_found`. */
  forget(linkToken: string): void {
    this.invitations.delete(linkToken);
    this.resets.delete(linkToken);
  }

  /** What the link reads as now: after a password was set by it, `used`. */
  invitationState(linkToken: string): LinkState | undefined {
    return this.invitations.get(linkToken)?.page.state;
  }

  resetState(linkToken: string): LinkState | undefined {
    return this.resets.get(linkToken);
  }
}
