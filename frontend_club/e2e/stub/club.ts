/**
 * **One club, as the backend would keep it**: the default handlers every test starts with.
 *
 * Ogrody 33's desk has an account; tokens rotate on every refresh and a spent one is refused;
 * a reset signs every session out. The rules are the club surface's own, from
 * `backend/openapi.club.json`, kept just deep enough that a test can walk sign-in, a reload, a
 * refresh, a save and a reset without programming each reply. A test that is about one reply
 * overrides that handler with `stub.on`.
 */

import { randomUUID } from 'node:crypto';

import type { components } from '../../src/generated/schema';

import { refusal, type StubBackend } from './backend';

type ClubDetails = components['schemas']['ClubDetailsResponse'];
type TokenPair = components['schemas']['TokenResponse'];
export type Administrator = components['schemas']['AdministratorSchema'];

const HOUR_MS = 3_600_000;
export const DAY_MS = 24 * HOUR_MS;
/** How long an invitation stays open, from its sending or its resending (ADR-0184 §3). */
const INVITATION_MS = 72 * HOUR_MS;

/** An instant `ms` from now, written as the wire writes one. */
export function fromNow(ms: number): string {
  return new Date(Date.now() + ms).toISOString();
}

/**
 * **Somebody the club named**, invited a moment ago unless the test says otherwise: a test
 * gives the name, the email and whatever its reply is about.
 */
export function administrator(
  fields: Pick<Administrator, 'name' | 'email'> & Partial<Administrator>,
): Administrator {
  return {
    id: randomUUID(),
    status: 'INVITED',
    last_used_at: null,
    expires_at: fromNow(INVITATION_MS),
    groups: [],
    can_reset_password: false,
    ...fields,
  };
}

export const DESK_EMAIL = 'desk@ogrody33.pl';
export const DESK_PASSWORD = 'kort33ogrody';

export const OGRODY_33: ClubDetails = {
  id: '6f1c2c7e-4b1d-4a53-9f2e-3a0a7f1b2c33',
  name: 'Ogrody 33',
  district: 'Grzegórzki',
  city: 'Kraków',
  sports: ['PADEL', 'TENNIS'],
  point: { latitude: 50.0592, longitude: 19.9575 },
};

/** The one-time credential a *Forgot password?* email carries. */
export interface ResetEmail {
  readonly to: string;
  readonly token: string;
  readonly code: string;
}

export class FakeClub {
  details: ClubDetails = { ...OGRODY_33 };
  email = DESK_EMAIL;
  password = DESK_PASSWORD;
  /** Seconds an access token lasts, as a pair says in `expires_in`. */
  expiresIn = 900;
  /** How many of the next pairs are issued already about to lapse (see {@link shortLived}). */
  private lapsing = 0;

  private issued = 0;
  /**
   * Tokens are unique across the run, as real ones are: the website keeps a renewed pair for a
   * few seconds per refresh token, and a second test's `refresh-1` must not find the first's.
   */
  private readonly run = randomUUID().slice(0, 8);
  /** Access tokens that work: token → when it lapses, in epoch milliseconds. */
  private readonly access = new Map<string, number>();
  /** Refresh tokens that can still be presented once. */
  private readonly refresh = new Set<string>();
  /** Every reset email "sent", newest last. */
  readonly outbox: ResetEmail[] = [];
  private readonly tickets = new Set<string>();
  /** The club's administrators, removed ones gone; the list answers them by name. */
  administrators: Administrator[] = [];

  constructor(private readonly stub: StubBackend) {}

  /**
   * Issue the next `count` pairs with five seconds to live: inside the website's margin from the
   * moment they are issued, so the next request that carries one renews it.
   */
  shortLived(count = 1): void {
    this.lapsing = count;
  }

  /** The `n`th access token this club issued. */
  accessToken(n: number): string {
    return `access-${n}.${this.run}`;
  }

  /** The `n`th refresh token this club issued. */
  refreshToken(n: number): string {
    return `refresh-${n}.${this.run}`;
  }

  /**
   * Mint a pair and remember it. Tokens are numbered in the order they were issued. A rotation
   * spends the refresh token and leaves the access token working until it lapses, as the backend
   * does; only signing out everywhere ({@link revokeAll}) stops it sooner.
   */
  issue(): TokenPair {
    this.issued += 1;
    const lifetime = this.lapsing > 0 ? 5 : this.expiresIn;
    this.lapsing = Math.max(0, this.lapsing - 1);
    const pair = {
      access_token: this.accessToken(this.issued),
      refresh_token: this.refreshToken(this.issued),
      token_type: 'bearer',
      expires_in: lifetime,
    };
    this.access.set(pair.access_token, Date.now() + lifetime * 1000);
    this.refresh.add(pair.refresh_token);
    return pair;
  }

  /** Sign out everywhere: no pair issued so far works any more. */
  revokeAll(): void {
    this.access.clear();
    this.refresh.clear();
  }

  private accessIsLive(authorization: string | undefined): boolean {
    const lapses = this.access.get(authorization?.replace(/^Bearer /, '') ?? '');
    return lapses !== undefined && Date.now() < lapses;
  }

  install(): this {
    const stub = this.stub;

    stub.on('post', '/api/v1/club/auth/login', ({ body }) =>
      body.email === this.email && body.password === this.password
        ? { status: 200, body: this.issue() }
        : { status: 401, body: refusal('invalid_credentials') },
    );

    stub.on('post', '/api/v1/club/auth/refresh', ({ body }) => {
      if (!this.refresh.delete(body.refresh_token)) {
        return { status: 401, body: refusal('refresh_token_revoked') };
      }
      return { status: 200, body: this.issue() };
    });

    stub.on('post', '/api/v1/club/auth/logout', ({ body }) => {
      this.refresh.delete(body.refresh_token);
      return { status: 200, body: { message: 'Logged out successfully' } };
    });

    stub.on('post', '/api/v1/club/sign-up', ({ body }) => {
      this.email = body.email;
      this.password = body.password;
      this.details = {
        id: OGRODY_33.id,
        name: body.name,
        district: body.district,
        city: body.city,
        sports: body.sports,
        point: body.point,
      };
      return { status: 201, body: this.details };
    });

    stub.on('get', '/api/v1/club/details', ({ headers }) =>
      this.accessIsLive(headers.authorization)
        ? { status: 200, body: this.details }
        : { status: 401, body: refusal('access_token_invalid') },
    );

    stub.on('put', '/api/v1/club/details', ({ headers, body }) => {
      if (!this.accessIsLive(headers.authorization)) {
        return { status: 401, body: refusal('access_token_invalid') };
      }
      this.details = {
        ...this.details,
        ...body,
        name: body.name.trim().replace(/\s+/g, ' '),
      };
      return { status: 200, body: this.details };
    });

    stub.on('post', '/api/v1/club/auth/forgot-password', ({ body }) => {
      if (body.email === this.email) {
        const n = this.outbox.length + 1;
        this.outbox.push({ to: body.email, token: `reset-link-${n}`, code: `K7Q2M9X${n}` });
      }
      return { status: 202, body: undefined };
    });

    stub.on('post', '/api/v1/club/auth/forgot-password/claim', ({ body }) => {
      const sent = this.outbox.at(-1);
      if (sent === undefined || sent.to !== body.email || sent.code !== body.code) {
        return { status: 400, body: refusal('code_incorrect', 'code') };
      }
      const ticket = `ticket-for-${sent.code}`;
      this.tickets.add(ticket);
      return { status: 200, body: { ticket, expires_in: 900 } };
    });

    stub.on('post', '/api/v1/club/auth/forgot-password/new-password', ({ body }) => {
      const byLink = body.token != null && this.outbox.some((mail) => mail.token === body.token);
      const byCode = body.ticket != null && this.tickets.has(body.ticket);
      if (!byLink && !byCode) return { status: 404, body: refusal('credential_not_found') };
      this.password = body.password;
      this.revokeAll();
      this.outbox.length = 0;
      this.tickets.clear();
      return { status: 200, body: this.issue() };
    });

    this.installAdministrators();
    return this;
  }

  private find(id: string | undefined): Administrator | undefined {
    return this.administrators.find((each) => each.id === id);
  }

  /** Put a changed row in the place of the old one, and answer with it. */
  private replace(row: Administrator): Administrator {
    this.administrators = this.administrators.map((each) => (each.id === row.id ? row : each));
    return row;
  }

  /** The club's Administrators, as ADR-0184 keeps them: one per email, every status derived. */
  private installAdministrators(): void {
    const stub = this.stub;
    const signedOut = { status: 401, body: refusal('access_token_invalid') } as const;
    const notFound = { status: 404, body: refusal('administrator_not_found') } as const;
    const reopened = (row: Administrator): Administrator => ({
      ...row,
      status: 'INVITED',
      last_used_at: null,
      expires_at: fromNow(INVITATION_MS),
    });

    stub.on('get', '/api/v1/club/administrators', ({ headers }) => {
      if (!this.accessIsLive(headers.authorization)) return signedOut;
      const byName = [...this.administrators].sort((a, b) => a.name.localeCompare(b.name));
      return { status: 200, body: { administrators: byName } };
    });

    stub.on('post', '/api/v1/club/administrators', ({ headers, body }) => {
      if (!this.accessIsLive(headers.authorization)) return signedOut;
      const name = body.name.trim().replace(/\s+/g, ' ');
      const length = [...name].length;
      if (length < 2 || length > 64) {
        return { status: 400, body: refusal('administrator_name_invalid', 'name') };
      }
      const email = body.email.trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        return { status: 400, body: refusal('email_invalid', 'email') };
      }
      const here = this.administrators.find(
        (each) => each.email.toLowerCase() === email.toLowerCase(),
      );
      if (here !== undefined) {
        const code =
          here.status === 'ACTIVE'
            ? 'administrator_already_active'
            : 'administrator_already_invited';
        return { status: 409, body: refusal(code, 'email') };
      }
      const invited = administrator({ name, email });
      this.administrators.push(invited);
      return { status: 201, body: invited };
    });

    stub.on(
      'post',
      '/api/v1/club/administrators/{administrator_id}/invitation',
      ({ headers, params }) => {
        if (!this.accessIsLive(headers.authorization)) return signedOut;
        const row = this.find(params.administrator_id);
        if (row === undefined) return notFound;
        if (row.status === 'ACTIVE') {
          return { status: 409, body: refusal('administrator_already_active') };
        }
        return { status: 200, body: this.replace(reopened(row)) };
      },
    );

    stub.on(
      'post',
      '/api/v1/club/administrators/{administrator_id}/password-reset',
      ({ headers, params }) => {
        if (!this.accessIsLive(headers.authorization)) return signedOut;
        const row = this.find(params.administrator_id);
        if (row === undefined) return notFound;
        if (!row.can_reset_password) {
          return { status: 409, body: refusal('administrator_also_plays') };
        }
        return { status: 200, body: this.replace(reopened(row)) };
      },
    );

    stub.on('delete', '/api/v1/club/administrators/{administrator_id}', ({ headers, params }) => {
      if (!this.accessIsLive(headers.authorization)) return signedOut;
      if (this.find(params.administrator_id) === undefined) return notFound;
      this.administrators = this.administrators.filter(
        (each) => each.id !== params.administrator_id,
      );
      return { status: 204, body: undefined };
    });
  }
}
