/**
 * **The group a link opens, wire to view.** The only file in this feature that imports a
 * generated type (ADR-0187 §6); everything else reads the {@link LinkedGroup} it makes.
 */

import type { components } from '@/generated/schema';

type WireGroup = components['schemas']['LinkedGroupResponse'];
type WireSport = components['schemas']['Sport'];

export type Sport = 'padel' | 'tennis' | 'squash' | 'badminton';

/**
 * A `Record` over the wire's enum, so a fifth sport in the contract fails to compile here, and
 * then in `copy.ts` and `GroupCard.tsx`, until it has a name and a dot.
 */
const SPORTS: Readonly<Record<WireSport, Sport>> = {
  PADEL: 'padel',
  TENNIS: 'tennis',
  SQUASH: 'squash',
  BADMINTON: 'badminton',
};

/** The tile's eight fills, as the app has them (`src/ui/tokens.css`, `--colour-monogram-*`). */
export const HUES = [0, 1, 2, 3, 4, 5, 6, 7] as const;

export type Hue = (typeof HUES)[number];

/**
 * A group, as its page draws it. **Nobody in it is named** (ADR-0187 §5): the backend sends no
 * member, and there is nowhere here to put one.
 */
export interface LinkedGroup {
  readonly name: string;
  /** Drawn as it comes, never re-cased (ADR-0183 §5), on the fill its key picks. */
  readonly monogram: { readonly letters: string; readonly hue: Hue };
  /** Where it plays: its home club, and the club's district. */
  readonly club: { readonly name: string; readonly district: string };
  /** In the registry's order, as the backend answers. */
  readonly sports: readonly Sport[];
  readonly memberCount: number;
}

/** The key's fill. A key past the palette, from a backend that grew it first, wraps. */
function hueOf(key: number): Hue {
  const index = ((Math.trunc(key) % HUES.length) + HUES.length) % HUES.length;
  return HUES[index] ?? HUES[0];
}

export function toLinkedGroup(wire: WireGroup): LinkedGroup {
  return {
    name: wire.name,
    monogram: { letters: wire.monogram.letters, hue: hueOf(wire.monogram.colour) },
    club: { name: wire.club.name, district: wire.club.district },
    sports: wire.sports.map((sport) => SPORTS[sport]),
    memberCount: wire.member_count,
  };
}
