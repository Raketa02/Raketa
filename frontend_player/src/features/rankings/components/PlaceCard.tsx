/**
 * **The reader's place card** (the rankings screens §4; rankings 3; [#775](https://github.com/Raketa02/Raketa/issues/775)).
 *
 * - **Listed** — the dark card: the eyebrow *YOUR PLACE*, the place large in volt with *of 13*
 *   beside it; the level on the right with the chip and its words under it; and under a fold the gap
 *   line, its numbers bold (§4.1, §4.2).
 * - **Hidden from General** — the same card with *Hidden from General* where the gap line was
 *   (§4.5). The switch beside it is #778's.
 * - **Not listed** — a light card in the dark card's place, one line: *2 of 5 games — …*, *Off the
 *   list — …*, or *No squash level yet — …* with **Get your squash level**, which starts that sport's
 *   questionnaire and returns to Rankings on this sport (§4.3, §4.4).
 *
 * `JUST_YOU` and `NO_FRIEND_LISTED` are Friends' (#777), which this page does not read yet: they draw
 * nothing here.
 *
 * **Volt is the place's**, as a fill anywhere and a stroke only on dark: here it is text on `night`,
 * the confidence ring's own ground (13,96:1 is ink on volt; volt on night is the ring's pair). The
 * bold numbers in the gap line are mono, as every number is (Part 16, 2026-11-08).
 */

import { StyleSheet, Text, View } from 'react-native';

import { STARTING_LABEL, fromRankings, useAddASport } from '@/features/onboarding/types';
import { recoveryMessage } from '@/shared/errors';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import { Button, Card, DarkCard, Note, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { GapLine, PlaceCard as ReaderCard, Placed } from '../domain/ranking';

import { RankChip } from './RankChip';
import {
  RANKINGS_COPY,
  cardChipWords,
  gapLineParts,
  getYourLevelLabel,
  notListedLine,
  ofListed,
  ordinal,
  placeCardSpoken,
  type NotListedCard,
} from './rankingsCopy';

export function PlaceCard({ card, sport }: { readonly card: ReaderCard; readonly sport: Sport }) {
  switch (card.state) {
    case 'LISTED':
      return <PlacedCard placed={card} below={<GapLineText line={card.gapLine} />} />;
    case 'HIDDEN':
      return (
        <PlacedCard placed={card} below={<Text style={s.line}>{RANKINGS_COPY.hidden}</Text>} />
      );
    case 'NO_LEVEL':
      return <NoLevelCard card={card} sport={sport} />;
    case 'NEEDS_RESULTS':
    case 'OFF_THE_LIST':
      return <NotListed card={card} sport={sport} />;
    case 'JUST_YOU':
    case 'NO_FRIEND_LISTED':
      // Friends' (#777): never served to General, which is all this page reads.
      return null;
  }
}

/** The dark card: a place on the left, the level on the right, and a line under the fold. */
function PlacedCard({
  placed,
  below,
}: {
  readonly placed: Placed;
  readonly below: React.ReactNode;
}) {
  const place = ordinal(placed.place);
  const level = formatLevel(placed.level);

  return (
    <DarkCard style={s.dark}>
      <View
        testID="place-card"
        style={s.top}
        accessible
        accessibilityLabel={placeCardSpoken(placed)}
      >
        <View style={s.left}>
          <Text style={s.eyebrow}>{RANKINGS_COPY.eyebrow}</Text>
          <View style={s.placeRow}>
            <Text style={s.place}>{place}</Text>
            <Text style={s.of}>{ofListed(placed.of)}</Text>
          </View>
        </View>
        <View style={s.right}>
          <Text style={s.level}>{level}</Text>
          {placed.chip === undefined ? null : (
            <View style={s.chipRow}>
              <RankChip chip={placed.chip} />
              <Text style={s.chipWords}>{cardChipWords(placed.chip)}</Text>
            </View>
          )}
        </View>
      </View>
      <View style={s.fold} />
      {below}
    </DarkCard>
  );
}

/** §4.2: the gap line, its numbers bold — one text, so it wraps as one sentence. */
function GapLineText({ line }: { readonly line: GapLine }) {
  const parts = gapLineParts(line);
  if (parts.length === 0) return null;
  return (
    <Text testID="gap-line" style={s.line}>
      {parts.map((part, at) =>
        part.strong === true ? (
          <Text key={`part-${at}`} style={s.strong}>
            {part.text}
          </Text>
        ) : (
          part.text
        ),
      )}
    </Text>
  );
}

/** §4.3: a light card, one line, no button. */
function NotListed({ card, sport }: { readonly card: NotListedCard; readonly sport: Sport }) {
  return (
    <Card>
      <Text testID="not-listed-line" style={s.notListed}>
        {notListedLine(card, sport)}
      </Text>
    </Card>
  );
}

/**
 * §4.4: *No squash level yet — …* and **Get your squash level** (coral): a pass of that one sport,
 * begun at its question, and back on Rankings on this sport however it ends (ADR-0200 §5).
 */
function NoLevelCard({
  card,
  sport,
}: {
  readonly card: Extract<ReaderCard, { readonly state: 'NO_LEVEL' }>;
  readonly sport: Sport;
}) {
  const addASport = useAddASport(fromRankings(sport));

  return (
    <Card style={s.noLevel}>
      <Text testID="not-listed-line" style={s.notListed}>
        {notListedLine(card, sport)}
      </Text>
      {addASport.error === null ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(addASport.error)}
        </Note>
      )}
      <Button
        label={getYourLevelLabel(sport)}
        busy={addASport.starting === sport}
        busyLabel={STARTING_LABEL}
        onPress={() => addASport.rate(sport)}
      />
    </Card>
  );
}

const s = StyleSheet.create({
  dark: { gap: theme.space.md },
  top: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end' },
  left: { gap: theme.space.xs, flexShrink: 1 },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.onDarkEyebrow },
  placeRow: { flexDirection: 'row', alignItems: 'baseline', gap: theme.space.xs },
  // Rankings 3: the place is the card's largest figure, in volt.
  place: { ...theme.num.levelHero, ...theme.tabular, color: theme.color.volt },
  of: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  right: { alignItems: 'flex-end', gap: theme.space.xs },
  level: { ...theme.num.levelLarge, ...theme.tabular, color: theme.color.surface },
  chipRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  chipWords: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  // 5.2: a fold inside a dark card is the on-dark hairline.
  fold: { height: StyleSheet.hairlineWidth, backgroundColor: theme.color.onDarkHair },
  line: { ...theme.type.rlLabel, color: theme.color.onDarkTiny },
  strong: { fontFamily: theme.font.mono[600], color: theme.color.surface },
  noLevel: { gap: theme.space.md },
  notListed: { ...theme.type.rlLabel, color: theme.color.ink },
});
