/**
 * **An official group, for a player rated in none of its sports** — one card in place of Games,
 * Fill in and Friends, and of Members' list
 * ([#519](https://github.com/Raketa02/Raketa/issues/519), PRD #500 story 57): *This group plays
 * padel*, *Add padel to your Skill passport to see its games.*, and a button per sport it plays.
 *
 * An official group plays what it declares (ADR-0183 §3, §6), and every tab but Info is drawn for
 * one of those sports, so a member rated in none of them has nothing those tabs could draw. **Info
 * stays** — the group, its dots and the way out are not a sport's.
 *
 * **Each button is the Skill passport's *Add a sport*** — onboarding's `useAddASport`, the second
 * door into the onboarding pass (ADR-0179 §3) — for that one sport: it starts the questionnaire and
 * the pass ends where every pass begun there does, on the passport with the new card drawn. The
 * start's wait and its failure are said here, beside the buttons, as the passport says them.
 *
 * The page's dark card, like every starting tab's (`LinkCard`): the remedy is the one bright door.
 */

import { StyleSheet, Text, View } from 'react-native';

import { STARTING_LABEL, useAddASport } from '@/features/onboarding/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, DarkCard, Note, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { addSportHeadline, addSportLabel, addSportLine } from './groupsPresentation';

export function AddSportCard({ sports }: { readonly sports: readonly Sport[] }) {
  const addASport = useAddASport();

  return (
    <DarkCard style={s.card}>
      <Text style={s.headline}>{addSportHeadline(sports)}</Text>
      <Text style={s.line}>{addSportLine(sports)}</Text>
      {addASport.error === null ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(addASport.error)}
        </Note>
      )}
      <View style={s.row}>
        {sports.map((sport) => (
          <Button
            key={sport}
            label={addSportLabel(sport)}
            variant="volt"
            busy={addASport.starting === sport}
            busyLabel={STARTING_LABEL}
            onPress={() => addASport.rate(sport)}
          />
        ))}
      </View>
    </DarkCard>
  );
}

const s = StyleSheet.create({
  card: { alignItems: 'center', gap: theme.space.md },
  // 3.3: `h2` titles a card — `LinkCard`'s headline.
  headline: { ...theme.type.h2, color: theme.color.surface, textAlign: 'center' },
  line: { ...theme.type.tiny, color: theme.color.onDarkTiny, textAlign: 'center' },
  row: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: theme.space.xs },
});
