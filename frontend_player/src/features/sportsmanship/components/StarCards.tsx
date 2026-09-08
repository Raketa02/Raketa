/**
 * **The cards still waiting for your stars**, drawn in the games list on the Now tab.
 *
 * ## The surface composes and this feature owns the act
 *
 * `GamesSection` draws this above its own rows and hands down the courts it already holds —
 * the same seam the builder has with the challenge send, where *"the pinned CTA is the court's
 * own slot calling a challenges use-case"*. The read behind the cards is this feature's, the
 * words are this feature's and the write is this feature's; what `games` supplies is the one
 * thing this route deliberately does not carry, which is who the ids are.
 *
 * That is why `RatedCourt` is declared in `domain/card.ts` rather than imported from `games`:
 * this feature says what it needs to know about an evening, and the games list satisfies it.
 * Taking `Game` would have taken the whole of another feature's entity as this one's contract.
 *
 * ## Nothing is drawn when nothing is waiting, and nothing says so
 *
 * An empty list is *the ordinary answer* — a card appears the day after the game and stays a
 * week, so most of the time there is none — and Now **never says nothing is happening**. It is
 * also why there is no *thanks* and no *0 of 3 rated*: ignoring a card costs nothing, and a
 * section that counted what a player had not done would be an obligation the design refuses to
 * create.
 *
 * The read's own failure is silent here for the same reason, and this is the one place it
 * differs from `GamesSection` beneath it: that section draws a note on a failed read because a
 * list of *your own games* vanishing is indistinguishable from having none, and it must not be.
 * A card list that failed to load has nothing a player is owed — there was probably nothing in
 * it, ignoring it costs nothing, and a coral note over an unasked-for favour is the app
 * apologising for a chore it invented.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { cardsOnCourts, type RatedCourt } from '../domain/card';
import { useOpenCards } from '../hooks/useCards';

import { StarCard } from './StarCard';
import { STARS_HEADING } from './starsPresentation';

export interface StarCardsProps {
  /**
   * The evenings the caller holds — every game, not only the settled ones. Which of them a
   * card is drawn for is the **server's** answer and never a filter applied here: the window
   * runs from the day after the game to seven days later, and a second spelling of it on this
   * side would eventually disagree with the one the send is judged against.
   */
  readonly courts: readonly RatedCourt[];
}

export function StarCards({ courts }: StarCardsProps) {
  const cards = useOpenCards();
  const drawn = cardsOnCourts(cards.data ?? [], courts);

  if (drawn.length === 0) return null;

  return (
    <View style={s.section}>
      <Text style={s.heading}>{STARS_HEADING}</Text>
      {drawn.map((one) => (
        <StarCard key={one.card.gameId} {...one} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  // `sm` inside and nothing outside: the games section this is composed into stacks its own
  // children on the same 9pt step, so one rule separates the cards from each other and this
  // section from the heading beneath it. A margin here would compose with that gap into a
  // fourth number belonging to neither.
  section: { gap: theme.space.sm },
  heading: { ...theme.type.h2, color: theme.color.ink },
});
