/**
 * **The fake group directory**: the stub's default answer to *the group a link opens*, keeping the
 * backend's rules so a test seats only the groups it is about (`groups.seat(code, group)`).
 *
 * - A code is read **in any case**, as the backend reads it: every code is minted lower case.
 * - A code no group has is one answer, `404 group_not_found`, which is also what a deleted group's
 *   link and a code that could be nobody's get (ADR-0183 §4).
 */

import type { components } from '../../src/generated/schema';

import { refusal, type StubBackend } from './backend';

/** The wire's answer, as the stub sends it: not the site's view model of the same name. */
export type LinkedGroupResponse = components['schemas']['LinkedGroupResponse'];

export const GROUP_PATH = '/api/v1/public/groups/{code}';

/** Ogrody 33 Club, as Marta posted it into the padel WhatsApp chat (#525). */
export function linkedGroup(overrides: Partial<LinkedGroupResponse> = {}): LinkedGroupResponse {
  return {
    name: 'Ogrody 33 Club',
    monogram: { letters: 'O3', colour: 0 },
    club: { name: 'Ogrody 33', district: 'Grzegórzki' },
    sports: ['PADEL'],
    member_count: 11,
    ...overrides,
  };
}

export class FakeGroups {
  private readonly byCode = new Map<string, LinkedGroupResponse>();

  constructor(private readonly stub: StubBackend) {}

  install(): this {
    this.stub.on('get', GROUP_PATH, ({ params }) => {
      const group = this.byCode.get((params.code ?? '').toLowerCase());
      return group === undefined
        ? { status: 404, body: refusal('group_not_found') }
        : { status: 200, body: group };
    });
    return this;
  }

  /** Seat a group behind a code, which is minted lower case. */
  seat(code: string, group: LinkedGroupResponse = linkedGroup()): LinkedGroupResponse {
    this.byCode.set(code.toLowerCase(), group);
    return group;
  }

  /** The group is deleted: its link leads nowhere from now on. */
  delete(code: string): void {
    this.byCode.delete(code.toLowerCase());
  }
}
