/**
 * **The card still waiting for your stars**, drawn at the end of the result screen.
 *
 * ## It is asked where the evening is read
 *
 * A card asking how the other players were belongs with the game it is about, and the screen
 * that is about a game is the result conversation — the one a player opens after they played,
 * to enter a score or read the one that settled. So the question is put at the **end** of that
 * screen: below the score, below the clock, after everything the screen exists to say.
 *
 * It used to sit above the games list on the Now tab ([#386](https://github.com/Raketa02/Raketa/issues/386)),
 * and the cost of moving it is worth stating rather than discovering: **nothing surfaces the
 * card any more.** Now no longer carries it, so a player who never re-opens a settled game
 * never sees it — which is a fair trade only because ignoring a card costs nothing and always
 * did.
 *
 * ## The surface composes and this feature owns the act
 *
 * `ResultScreen` draws this and hands down the one court it already holds — the same seam the
 * builder has with the challenge send, where *"the pinned CTA is the court's own slot calling a
 * challenges use-case"*. The read behind the card is this feature's, the words are this
 * feature's and the write is this feature's; what `games` supplies is the one thing this route
 * deliberately does not carry, which is who the ids are.
 *
 * That is why `RatedCourt` is declared in `domain/card.ts` rather than imported from `games`:
 * this feature says what it needs to know about an evening, and the result screen satisfies it.
 * Taking `Game` would have taken the whole of another feature's entity as this one's contract.
 *
 * ## Nothing is drawn when nothing is waiting, and nothing says so
 *
 * An empty answer is *the ordinary answer* — a card appears the day after the game **and only
 * once the score has settled**, and it stays a week — so most openings of this screen have
 * none. There is no *thanks*, no *rated* and no empty state: ignoring a card costs nothing, and
 * a line that acknowledged what a player had not done would be an obligation the design refuses
 * to create.
 *
 * The read's own failure is silent for the same reason, and it is why this is not composed as
 * one of the screen's states: a card list that failed to load has nothing a player is owed —
 * there was probably nothing in it, ignoring it costs nothing, and a coral note over an
 * unasked-for favour is the app apologising for a chore it invented. The screen's own read is
 * the one that gets a sentence when it fails.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { cardOnCourt, type RatedCourt } from '../domain/card';
import { useOpenCards } from '../hooks/useCards';

import { StarCard } from './StarCard';
import { STARS_HEADING } from './starsPresentation';

export interface StarCardSectionProps {
  /**
   * The evening this screen is about. Whether a card is drawn for it is the **server's**
   * answer and never a filter applied here: the window runs from the day after the game to
   * seven days later and opens only once the result has settled, and a second spelling of any
   * of that on this side would eventually disagree with the one the send is judged against.
   */
  readonly court: RatedCourt;
}

export function StarCardSection({ court }: StarCardSectionProps) {
  const cards = useOpenCards();
  const drawn = cardOnCourt(cards.data ?? [], court);

  if (drawn === undefined) return null;

  return (
    <View style={s.section}>
      <Text style={s.heading}>{STARS_HEADING}</Text>
      <StarCard {...drawn} />
    </View>
  );
}

const s = StyleSheet.create({
  // The screen stacks its own blocks on `sm`, so this keeps that step inside itself and takes
  // a larger one above: the card is a new question rather than another fact about the score,
  // and the gap is what says so before the heading does.
  section: { marginTop: theme.space.lg, gap: theme.space.sm },
  heading: { ...theme.type.h2, color: theme.color.ink },
});
