/**
 * **The fake friend links**: the stub's default answer to *who a friend link is from*, keeping the
 * backend's rules so a test seats only the links it is about (`friendLinks.seat(code, owner)`).
 *
 * - A code is read **in any case**, as the backend reads it: every code is minted lower case.
 * - A code no link carries now is one answer, `404 friend_link_not_found`: one replaced by a New
 *   link, one never made, and one that could be no link's.
 * - **A face is a signed link minted per read**, into the stand-in photo storage, which works only
 *   until the test expires it (`stub.expireSignedLinks()`), as the backend's work for minutes.
 */

import { refusal, type StubBackend } from './backend';

export const FRIEND_LINK_PATH = '/api/v1/public/friend-links/{code}';

/** Whose link it is: their nickname, and the JPEG of their first photograph when they have one. */
export interface LinkOwner {
  readonly nickname: string;
  readonly photo: Buffer | null;
}

/** Tomek, whose link Zofia taps (#755). No photograph unless a test gives him one. */
export function tomek(overrides: Partial<LinkOwner> = {}): LinkOwner {
  return { nickname: 'Tomek', photo: null, ...overrides };
}

export class FakeFriendLinks {
  private readonly byCode = new Map<string, LinkOwner>();

  constructor(private readonly stub: StubBackend) {}

  install(): this {
    this.stub.on('get', FRIEND_LINK_PATH, ({ params }) => {
      const code = (params.code ?? '').toLowerCase();
      const owner = this.byCode.get(code);
      if (owner === undefined) return { status: 404, body: refusal('friend_link_not_found') };
      return {
        status: 200,
        body: {
          nickname: owner.nickname,
          photo_url: owner.photo === null ? null : this.stub.signedLink(faceKey(code)),
        },
      };
    });
    return this;
  }

  /** Seat a link behind a code, which is minted lower case; a photograph goes into the storage. */
  seat(code: string, owner: LinkOwner = tomek()): LinkOwner {
    this.byCode.set(code.toLowerCase(), owner);
    if (owner.photo !== null) this.stub.store(faceKey(code.toLowerCase()), owner.photo);
    return owner;
  }

  /** New link: the old code reads as not found from now on. */
  replace(code: string): void {
    this.byCode.delete(code.toLowerCase());
  }
}

/** Where the stand-in storage keeps a link owner's face. */
function faceKey(code: string): string {
  return `photos/${code}.jpg`;
}
