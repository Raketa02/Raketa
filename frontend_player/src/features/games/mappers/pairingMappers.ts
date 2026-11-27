/**
 * The pairing's wire boundary: `GamePairingResponse` in, a {@link Pairing} out.
 *
 * **Every figure crosses as served.** The gap keeps its sign, the range keeps the engine's
 * rounding, the band is a name — `the-play-screens.md` §5's *no forecast arithmetic on the client*
 * is a rule about this file first, because it is the one place a number could be re-derived on
 * its way in. There is nothing to degrade and nothing to refuse: the response carries no closed
 * vocabulary this build could fail to read, so `gameMappers`' two-rule split does not arise.
 *
 * ## The forecast and the split are one thing, read as one
 *
 * ADR-0161 §4 omits them together, and this file holds the client to the same shape: a response
 * carrying one half of the computation is read as carrying neither, because the block draws the
 * two strengths under the percentage and half of that is not a thing to draw.
 *
 * ## A provisional figure is an absence here
 *
 * `provisional` travels inside the forecast on the engine's rule that *the failure guarded against
 * is a screen showing the number without its caveat*. It is never `true` on a game today — a
 * line-up is frozen at the plan — and when a seat can be open the answer is *omitted, never
 * provisional* (ADR-0161 §4). This screen draws no caveat, so the one shape that would put a
 * number on it without one is folded to nothing rather than drawn half.
 *
 * ## The Social vibe crosses beside the forecast, and a tag with no words is left off
 *
 * A For-fun game's pairing carries `vibe` (#835) **and** the forecast, still sent for the apps
 * already on phones. Both cross: which one is drawn is the kind's question (`pairingCardOf`), and
 * the pairing carries no kind. A tag this build cannot name is left off its rows (ADR-0207 §7) — the
 * server sends codes only, and a row with no words is not drawn — as the details' mapper does.
 */

import type { components } from '@/generated/schema';
import { toSocialTagId } from '@/shared/vocabulary/socialTags';

import type { Pairing, PairingSeat, PairingVibeRow } from '../domain/pairing';

type GamePairingResponse = components['schemas']['GamePairingResponse'];
type GamePairingSeatSchema = components['schemas']['GamePairingSeatSchema'];
type GamePairingVibeSchema = components['schemas']['GamePairingVibeSchema'];

function toSeat(wire: GamePairingSeatSchema): PairingSeat {
  return {
    playerId: wire.player_id,
    level: wire.level,
    band: wire.band,
    range: { low: wire.range.low, high: wire.range.high },
    confidence: wire.confidence,
  };
}

/** The forecast and the split, or neither — see the module note. */
function toComputed(wire: GamePairingResponse): Pick<Pairing, 'forecast' | 'split'> {
  const { forecast, split } = wire;
  if (forecast === undefined || split === undefined || forecast.provisional) return {};

  return {
    forecast: { pct: forecast.pct },
    split: { yourSide: split.your_side, theirSide: split.their_side, gap: split.gap },
  };
}

/** The Social vibe and your rows, in the order served — see the module note. */
function toVibe(wire: GamePairingVibeSchema | undefined): Pick<Pairing, 'vibe'> {
  if (wire === undefined) return {};
  const rows = wire.rows.flatMap((row): PairingVibeRow[] => {
    const tag = toSocialTagId(row.tag);
    return tag === undefined ? [] : [{ tag, carriedBy: row.carried_by }];
  });
  return { vibe: { pct: wire.pct, rows } };
}

export function toPairing(wire: GamePairingResponse): Pairing {
  return {
    readAt: wire.read_at,
    ...toComputed(wire),
    ...(wire.at_stake === undefined
      ? {}
      : { atStake: { winDelta: wire.at_stake.win_delta, lossDelta: wire.at_stake.loss_delta } }),
    seats: wire.seats.map(toSeat),
    ...toVibe(wire.vibe),
  };
}
