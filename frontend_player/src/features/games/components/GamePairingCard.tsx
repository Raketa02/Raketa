/**
 * **A game's pairing, drawn as its kind's card** — the forecast on a competitive game, the Social
 * vibe card on a For-fun one — for a surface that draws its own people
 * ([#556](https://github.com/Raketa02/Raketa/issues/556); [#841](https://github.com/Raketa02/Raketa/issues/841);
 * the screens A4.1, details 9; ADR-0207 §5).
 *
 * A booked game's details draw their tiles from the booking, with *paid* on each, so the players
 * card would be the second drawing of four people on one screen; what they take from this feature
 * is the pairing's card alone. It is one read (`usePairing`, the Game's own pairing), and the card
 * is absent on the same ground whatever the kind — no game in the list yet, a pairing with nothing
 * to draw, a read in flight or failed — with no sentence beside the absence (ADR-0161 §4). Whether
 * it is drawn at all is the composer's: a booking draws it while the full game awaits its entry,
 * before its hour and at the court.
 *
 * **The kind decides the card** (`pairingCardOf`): a For-fun game — `FRIENDLY` — draws the Social
 * vibe card where *A friendly — nothing moves.* stood, and the forecast #835 still sends for older
 * apps is ignored; a competitive game draws the Balance forecast and its stakes, as it always did.
 * Both are `shared/ui`'s since a game still filling draws them too (#839, #840); what this feature
 * hands them is its own read and its own words.
 *
 * **The vibe card's columns are the composer's** (`columns`): you first, then the others as its
 * tiles stand, each with the face it holds — the Game's seats carry neither that order nor a
 * photograph. The rows and the dots are this feature's, off the pairing.
 */

import { ForecastBlock, SocialVibeCard } from '@/shared/ui';
import type { SocialVibeColumn } from '@/shared/vocabulary/socialVibeGrid';

import type { Game } from '../domain/game';
import { pairingCardOf } from '../domain/pairing';
import { useGame } from '../hooks/useGames';
import { usePairing } from '../hooks/usePairing';

import { barLabels, forecastSentence, sideNames } from './gamePresentation';

export interface GamePairingCardProps {
  /** The Game whose pairing is read — a booking's `game_id`. */
  readonly gameId: string;
  /** The reader: your side is the bar's left, *You* first (ADR-0141's join). */
  readonly playerId: string;
  /**
   * **The Social vibe card's columns**, as the composer draws the people above it: you first, then
   * the others as its tiles stand, each with their face. Read on a For-fun game alone.
   */
  readonly columns: readonly SocialVibeColumn[];
}

export function GamePairingCard({ gameId, playerId, columns }: GamePairingCardProps) {
  const { game } = useGame(gameId);
  return game === undefined ? null : <Card game={game} playerId={playerId} columns={columns} />;
}

/** The read, once the game is known — a hook cannot wait for its argument. */
function Card({
  game,
  playerId,
  columns,
}: {
  readonly game: Game;
  readonly playerId: string;
  readonly columns: readonly SocialVibeColumn[];
}) {
  const pairing = usePairing(game).data ?? undefined;
  const card = pairing === undefined ? undefined : pairingCardOf(game.kind, pairing, columns);
  if (card === undefined) return null;
  if (card.kind === 'vibe') return <SocialVibeCard grid={card.grid} />;

  return (
    <ForecastBlock
      forecast={card.forecast}
      split={card.split}
      {...(card.atStake === undefined ? {} : { stake: card.atStake })}
      labels={barLabels(game.seats, playerId)}
      names={sideNames(game.seats, playerId)}
      sentence={forecastSentence(game.kind)}
    />
  );
}
