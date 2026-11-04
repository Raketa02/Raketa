/**
 * **The You tab's header card** — the record's own header, compact, on a dark card; tapping it
 * opens *How others see you*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1; Part 16, 2026-09-17).
 *
 * ```
 * ┌ photo ┐  tomek.k                           ◯ 92
 * │  ON   │  “Will travel for a hard game.”    SCORE
 * │ COURT │  ● Padel 2,71  ● Tennis 3,10
 * └───────┘
 * ```
 *
 * ## Three reads, and what each is for
 *
 * The nickname is `GET /users/me`'s — seeded by bootstrap, so the card has it before anything else
 * lands, and the one the *Nickname* row's save writes into, so a rename shows here on the way
 * back. Drawn large, **with nothing under it**: the handle is the identity, and the `@nickname`
 * line that once sat under a name went with the name
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1). The sport pills are `GET /ratings`', the same read the passport row's
 * line is drawn from. The photograph, the mark, the intro and the score are the record's, the
 * same read the sheet this card opens draws whole. Each part draws when its read is in and is
 * simply absent until then: the card never draws a nought.
 *
 * ## The face is the card panel, not a smaller one
 *
 * The record's photo panel at its `card` size (74 × 92), which is 10 pt wider than the
 * prototype's 64. **The ON COURT mark is why**: the mark's words and its tick, at the tag
 * type role, need about 57 pt of clear width at the mark's own top edge once the corner's
 * curve has taken its share, and a 64 pt panel leaves under 50 — `onCourtMarkFit.test.ts`
 * holds that arithmetic for every panel size, and a size that cannot carry the mark cannot be
 * one. The card panel is the smallest that can, and it is already drawn beside a name on every
 * candidate card.
 *
 * ## The intro is upright, in the drawing's marks
 *
 * As the record sheet and the deck card draw it, and for their reason: this app loads no italic
 * Archivo, and a `fontStyle` on a custom family is ignored on Android and synthesised on iOS.
 * The quotation marks carry *their words*.
 *
 * ## The ring's second home outside onboarding
 *
 * 7.8's ring at `ringSm`, still inside a dark card, printing the bare score — a Player Score is
 * out of a hundred and not a percentage — with `SCORE` beneath. Drawn only where the record
 * holds a reliability: a player nothing has fallen due for has no score, and the card draws
 * the pills alone rather than a nought in a ring.
 *
 * ## One element, one door
 *
 * The whole card is one press with one spoken name — the identity, then the score — because
 * everything on it is a fact and the one act is opening the sheet. `moveAccessibilityFocus`
 * is the sheet's own business on the way in.
 */

import { StyleSheet, Text, View } from 'react-native';

import { useCurrentUser } from '@/features/auth/types';
import {
  sportColour,
  sportLabel,
  sportShortLabel,
  useSkillRatings,
} from '@/features/onboarding/types';
import { ConfidenceRing, PhotoPanel, PressableDarkCard, Tag, theme } from '@/shared/ui';

import { useOwnRecord } from '../hooks/useOwnRecord';

import { OPENS_OWN_RECORD_HINT, SCORE_LABEL, scoreRingLabel } from './youRecordPresentation';
import { introLine, reliabilityReading, sportPill } from './recordPresentation';

export interface YouHeaderCardProps {
  /** Opens *How others see you* — the tab's overlay, which the shell holds. */
  readonly onPress: () => void;
}

export function YouHeaderCard({ onPress }: YouHeaderCardProps) {
  const user = useCurrentUser();
  const ratings = useSkillRatings();
  const { record, playerId } = useOwnRecord();

  const own = record.data;
  const name = user.data?.nickname;
  const intro = own?.intro === undefined ? undefined : introLine(own.intro);
  const reliability = own?.reliability;
  // Drawn short — three pills have to fit between a face and a ring — and spoken in full.
  const pills = (ratings.data ?? []).map(({ sport, level }) => ({
    sport,
    drawn: sportPill(sportShortLabel(sport), level),
    spoken: sportPill(sportLabel(sport), level),
  }));

  return (
    <PressableDarkCard
      style={s.card}
      accessibilityLabel={[
        ...(name === undefined ? [] : [name]),
        ...(intro === undefined ? [] : [intro]),
        ...(pills.length === 0 ? [] : [pills.map((pill) => pill.spoken).join(', ')]),
        // The band's word or *New* is spoken here, since the ring draws the figure alone.
        ...(reliability === undefined ? [] : [reliabilityReading(reliability)]),
      ].join('. ')}
      accessibilityHint={OPENS_OWN_RECORD_HINT}
      onPress={onPress}
    >
      {playerId === undefined ? null : (
        <PhotoPanel
          size="card"
          playerId={playerId}
          {...(own?.photoUrl === undefined ? {} : { photoUrl: own.photoUrl })}
          onCourt={own?.onCourt ?? false}
        />
      )}

      <View style={s.column}>
        {name === undefined ? null : <Text style={s.name}>{name}</Text>}
        {intro === undefined ? null : <Text style={s.intro}>{intro}</Text>}

        {pills.length === 0 ? null : (
          <View style={s.pills}>
            {pills.map(({ sport, drawn, spoken }) => (
              <Tag
                key={sport}
                label={drawn}
                accessibilityLabel={spoken}
                variant="onDark"
                dot={sportColour(sport)}
              />
            ))}
          </View>
        )}
      </View>

      {reliability === undefined ? null : (
        <ConfidenceRing
          size="sm"
          value={reliability.playerScore}
          figure={String(reliability.playerScore)}
          label={SCORE_LABEL}
          accessibilityLabel={scoreRingLabel(reliability.playerScore)}
        />
      )}
    </PressableDarkCard>
  );
}

const s = StyleSheet.create({
  card: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  // Takes what the panel and the ring leave, so a long nickname wraps inside it.
  column: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.h2, color: theme.color.surface },
  intro: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  pills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.space.xxs,
    marginTop: theme.space.xs,
  },
});
