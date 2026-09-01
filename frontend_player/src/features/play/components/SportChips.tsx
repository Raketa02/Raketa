/**
 * The sports a player may search in — **the ones they are rated in, and no others.**
 *
 * Drawn identically by Find a game and by the deck, which is why it is a component: the two
 * screens ask different questions and this is not one of them. It also settles
 * `sport_not_rated` **by construction** on both — the row is `GET /ratings`' own answer, in the
 * registry's order, and nothing here sorts.
 *
 * ## It reports a choice and does not make one
 *
 * `chooseSport` is `playPreferences`', process-scoped and never written back, and the two
 * screens **share it deliberately**: a player who switched to tennis on the deck is on tennis
 * when they go back to the search screen, because switching sport is a change of mind about
 * what they play rather than a fact about a screen.
 *
 * What the two screens do *with* the change still differs — Find a game re-seeds nothing and
 * the deck deals again — so the effect belongs to each of them and only the control is shared.
 */

import { StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { Chip, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

/** The row's heading. `flab` rather than `eyebrow`: a control you are about to operate. */
export const SPORT_HEADING = 'Sport';

export interface SportChipsProps {
  /** In the order `GET /ratings` answered — the registry's, at both ends. */
  readonly rated: readonly Sport[];
  readonly selected: Sport;
  readonly onChoose: (sport: Sport) => void;
}

export function SportChips({ rated, selected, onChoose }: SportChipsProps) {
  return (
    <View style={s.section}>
      <Text style={s.heading}>{SPORT_HEADING}</Text>
      <View style={s.chips}>
        {rated.map((offered) => (
          <Chip
            key={offered}
            label={sportLabel(offered)}
            selected={offered === selected}
            onPress={() => onChoose(offered)}
          />
        ))}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  section: { gap: theme.space.xs, paddingTop: theme.space.xs },
  heading: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});
