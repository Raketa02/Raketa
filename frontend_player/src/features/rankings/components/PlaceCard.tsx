/**
 * **The reader's place card** (the rankings screens §4; rankings 3; [#775](https://github.com/Raketa02/Raketa/issues/775)).
 *
 * - **Listed** — the dark card: the eyebrow *YOUR PLACE*, the place large in volt with *of 13*
 *   beside it; the level on the right with the chip and its words under it; and under a fold the gap
 *   line, its numbers bold (§4.1, §4.2).
 * - **Hidden from General** — the same card with *Hidden from General* where the gap line was, and
 *   **the switch beside it** (§4.5, [#778](https://github.com/Raketa02/Raketa/issues/778)): You's own
 *   *Show me in General*, `player_profile`'s, written by the same route and spoken by its name —
 *   *Show me in General, off* — because *Hidden from General* is what off means here. Turned on, it
 *   stands on while the ranking catches up, and the page follows it until the gap line is back
 *   (`useGeneral`). A refused write says why above the card, on paper, as the declaration's card
 *   says it — the dark card's repaint has no on-dark coral.
 * - **Not listed** — a light card in the dark card's place, one line: *2 of 5 games — …*, *Off the
 *   list — …*, or *No squash level yet — …* with **Get your squash level**, which starts that sport's
 *   questionnaire and returns to Rankings on this sport (§4.3, §4.4).
 * - **Friends, when the card is the page** (§4.6, #777) — a light card: *Just you so far*, or *None
 *   of your friends is ranked in padel yet*, each with **Add friends**, which opens `friends`' own Add
 *   friends sheet (the page holds it, and hears the press). In Friends the not-listed cards read their
 *   view's words — *Not ranked in padel yet — …*, and one game after a level — and stand above the
 *   friends' table.
 *
 * **Volt is the place's**, as a fill anywhere and a stroke only on dark: here it is text on `night`,
 * the confidence ring's own ground (13,96:1 is ink on volt; volt on night is the ring's pair). The
 * bold numbers in the gap line are mono, as every number is (Part 16, 2026-11-08).
 */

import { StyleSheet, Text, View } from 'react-native';

import { STARTING_LABEL, fromRankings, useAddASport } from '@/features/onboarding/types';
import { SHOW_ME_IN_GENERAL_TITLE, useShowMeInGeneral } from '@/features/player_profile/types';
import { recoveryMessage } from '@/shared/errors';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import { Button, Card, DarkCard, Note, Switch, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { GapLine, PlaceCard as ReaderCard, Placed } from '../domain/ranking';
import type { RankingView } from '../domain/vocabulary';

import { RankChip } from './RankChip';
import {
  RANKINGS_COPY,
  cardChipWords,
  friendsCardLine,
  gapLineParts,
  getYourLevelLabel,
  notListedLine,
  ofListed,
  ordinal,
  placeCardSpoken,
  type FriendsCard,
  type NotListedCard,
} from './rankingsCopy';

export interface PlaceCardProps {
  readonly card: ReaderCard;
  readonly sport: Sport;
  /** The view the card is in — a not-listed card says its view's words (§30.5). */
  readonly view: RankingView;
  /** **Add friends** was pressed, on a Friends card that is the page — the page opens the sheet. */
  readonly onAddFriends: () => void;
}

export function PlaceCard({ card, sport, view, onAddFriends }: PlaceCardProps) {
  switch (card.state) {
    case 'LISTED':
      return <PlacedCard placed={card} below={<GapLineText line={card.gapLine} />} />;
    case 'HIDDEN':
      return <HiddenCard placed={card} />;
    case 'NO_LEVEL':
      return <NoLevelCard card={card} sport={sport} view={view} />;
    case 'NEEDS_RESULTS':
    case 'OFF_THE_LIST':
      return <NotListed card={card} sport={sport} view={view} />;
    case 'JUST_YOU':
    case 'NO_FRIEND_LISTED':
      return <AddFriendsCard card={card} sport={sport} onAddFriends={onAddFriends} />;
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

/**
 * §4.5: the placed card, and under the fold *Hidden from General* with the switch — the row the
 * switch is, on the dark card's repaint.
 */
function HiddenCard({ placed }: { readonly placed: Placed }) {
  const showMe = useShowMeInGeneral();

  return (
    <View style={s.hidden}>
      {showMe.writeError === null ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(showMe.writeError)}
        </Note>
      )}
      <PlacedCard
        placed={placed}
        below={
          <View testID="hidden-from-general">
            <Switch
              onDark
              label={RANKINGS_COPY.hidden}
              accessibilityLabel={SHOW_ME_IN_GENERAL_TITLE}
              // The card says hidden: off, until the profile has said otherwise.
              checked={showMe.checked ?? false}
              onChange={showMe.change}
            />
          </View>
        }
      />
    </View>
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
function NotListed({
  card,
  sport,
  view,
}: {
  readonly card: NotListedCard;
  readonly sport: Sport;
  readonly view: RankingView;
}) {
  return (
    <Card>
      <Text testID="not-listed-line" style={s.notListed}>
        {notListedLine(card, sport, view)}
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
  view,
}: {
  readonly card: Extract<ReaderCard, { readonly state: 'NO_LEVEL' }>;
  readonly sport: Sport;
  readonly view: RankingView;
}) {
  const addASport = useAddASport(fromRankings(sport));

  return (
    <Card style={s.withButton}>
      <Text testID="not-listed-line" style={s.notListed}>
        {notListedLine(card, sport, view)}
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

/**
 * §4.6: *Just you so far*, or *None of your friends is ranked in padel yet*, and **Add friends** — a
 * light card in the dark card's place, as a not-listed card is, with nothing below it.
 */
function AddFriendsCard({
  card,
  sport,
  onAddFriends,
}: {
  readonly card: FriendsCard;
  readonly sport: Sport;
  readonly onAddFriends: () => void;
}) {
  return (
    <Card style={s.withButton}>
      <Text testID="friends-card-line" style={s.notListed}>
        {friendsCardLine(card, sport)}
      </Text>
      <Button label={RANKINGS_COPY.addFriends} onPress={onAddFriends} />
    </Card>
  );
}

const s = StyleSheet.create({
  dark: { gap: theme.space.md },
  // A refused write above the hidden card, the card's own gap below it — as a stack of cards.
  hidden: { gap: theme.space.xs },
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
  // A light card with its button under the line: §4.4's, and §4.6's.
  withButton: { gap: theme.space.md },
  notListed: { ...theme.type.rlLabel, color: theme.color.ink },
});
