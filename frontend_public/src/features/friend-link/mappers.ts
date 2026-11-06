/**
 * **Whose friend link it is, wire to view.** The only file in this feature that imports a
 * generated type (ADR-0187 §6); everything else reads the {@link LinkOwner} it makes, or the
 * {@link Face} the picture draws.
 */

import type { components } from '@/generated/schema';

type WireOwner = components['schemas']['LinkedFriendResponse'];

/**
 * The link's owner, as their page draws them: **their nickname and whether they have a face, and
 * nothing else about them** (#748), since the backend sends nothing else. The owner, not a
 * friend: nobody who opens the link is their **Friend** yet (root `CONTEXT.md`).
 */
export interface LinkOwner {
  /** Drawn as they typed it: a nickname is a handle, never re-cased or cut (ADR-0199). */
  readonly nickname: string;
  /**
   * Whether they have a **Profile photo**. The page draws it from this site, `/face/<code>`, and
   * never sees the backend's link to it.
   */
  readonly hasFace: boolean;
}

/**
 * The owner as the page draws them, and the backend's link to their photograph, which is signed
 * for minutes and only ever fetched by the server: `null` when they have none.
 */
export interface ReadOwner {
  readonly owner: LinkOwner;
  readonly photoLink: string | null;
}

export function toReadOwner(wire: WireOwner): ReadOwner {
  return {
    owner: { nickname: wire.nickname, hasFace: wire.photo_url !== null },
    photoLink: wire.photo_url,
  };
}

/** A face as the picture draws it: the photograph, as a `data:` address Satori reads. */
export interface Face {
  readonly source: string;
}

export function toFace(photograph: { readonly type: string; readonly bytes: ArrayBuffer }): Face {
  return {
    source: `data:${photograph.type};base64,${Buffer.from(photograph.bytes).toString('base64')}`,
  };
}
