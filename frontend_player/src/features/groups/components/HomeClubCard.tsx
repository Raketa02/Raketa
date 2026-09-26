/**
 * **New group's home club card** — the field, and the five things it can be showing (play 6–11;
 * #512). **Required** (PRD #500 overrides play 4 by name).
 *
 * | state | what is drawn |
 * | --- | --- |
 * | empty | the field, the hint, and what the home club is for |
 * | searching | the field — live, with a **coral** focus ring — and a row per club: name, district · sports, *Set as home ›*, the whole row the tap. **No distance in these rows** (#512) |
 * | no match | *No club called "…"*, and that only clubs in Raketa can be one |
 * | a club with groups | the row tinted `amberSoft` and tagged *group already here*, with a strip for each group and what the reader can do about it (stories 20–22) |
 * | chosen | the field gone; the club on `mintSoft` with its distance and **Change**, and what the choice now means |
 *
 * **The card holds no state.** The form is the screen's — the text, the answer and the choice —
 * because the page's scroll is what asks for the next twenty clubs, and the card sits inside it.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Button, Card, Tag, TextField, theme } from '@/shared/ui';

import type { SearchedClub } from '../domain/group';
import { searchOutcome } from '../domain/groupRules';
import type { ClubSearchState } from '../hooks/useClubSearch';

import { GroupAtClubRow } from './GroupAtClubRow';
import { GROUPS_COPY } from './groupsCopy';
import {
  chosenClubConsequence,
  chosenClubLabel,
  clubLine,
  noClubCalled,
  setAsHomeLabel,
} from './groupsPresentation';
import { ReadFailure } from './ReadFailure';

const COPY = GROUPS_COPY.newGroup;

export interface HomeClubCardProps {
  readonly typed: string;
  readonly onType: (text: string) => void;
  readonly search: ClubSearchState;
  readonly chosen: SearchedClub | undefined;
  readonly onChoose: (club: SearchedClub) => void;
  readonly onChange: () => void;
}

export function HomeClubCard({
  typed,
  onType,
  search,
  chosen,
  onChoose,
  onChange,
}: HomeClubCardProps) {
  return (
    <Card style={s.card}>
      {/* The label is drawn here rather than by the field, because *· required* is quieter than
          the name it qualifies; the field still carries the name for a listener. */}
      <Text style={s.label}>
        {COPY.homeClub}
        <Text style={s.qualifier}>{` · ${COPY.required}`}</Text>
      </Text>

      {chosen !== undefined ? (
        <ChosenClub club={chosen} onChange={onChange} />
      ) : (
        <>
          <TextField
            label={COPY.homeClub}
            labelHidden
            recessed
            focusRing="coral"
            placeholder={COPY.homeClubPlaceholder}
            value={typed}
            onChangeText={onType}
            autoCorrect={false}
            autoCapitalize="none"
            returnKeyType="search"
          />
          <Results search={search} onChoose={onChoose} />
        </>
      )}

      <Text style={s.note}>
        {chosen === undefined ? COPY.homeClubConsequence : chosenClubConsequence(chosen.name)}
      </Text>
    </Card>
  );
}

function Results({
  search,
  onChoose,
}: {
  readonly search: ClubSearchState;
  readonly onChoose: (club: SearchedClub) => void;
}) {
  if (search.text === '') return <Text style={s.hint}>{COPY.homeClubHint}</Text>;

  if (search.error !== null && search.answer === undefined) {
    return <ReadFailure error={search.error} onRetry={search.retry} />;
  }

  if (search.answer === undefined) return null;

  const outcome = searchOutcome(search.answer);
  if (outcome.kind !== 'clubs') {
    return (
      <View style={s.nothing}>
        <Text style={s.nothingTitle}>{noClubCalled(search.answer.text)}</Text>
        <Text style={s.hint}>{COPY.noClubNote}</Text>
      </View>
    );
  }

  return (
    <View>
      {search.answer.clubs.map((club, index) => (
        <ClubRow key={club.id} club={club} first={index === 0} onChoose={onChoose} />
      ))}
    </View>
  );
}

function ClubRow({
  club,
  first,
  onChoose,
}: {
  readonly club: SearchedClub;
  readonly first: boolean;
  readonly onChoose: (club: SearchedClub) => void;
}) {
  const tinted = club.groups.length > 0;

  return (
    <View style={[s.club, first ? undefined : s.divided, tinted ? s.tinted : undefined]}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={setAsHomeLabel(club)}
        onPress={() => onChoose(club)}
        style={({ pressed }) => [s.clubHead, pressed ? s.pressed : undefined]}
      >
        <View style={s.clubWords}>
          <View style={s.clubNameRow}>
            <Text style={s.clubName} numberOfLines={1}>
              {club.name}
            </Text>
            {tinted ? <Tag label={COPY.groupAlreadyHere} variant="warn" /> : null}
          </View>
          <Text style={s.clubLine} numberOfLines={1}>
            {clubLine(club, { distance: false })}
          </Text>
        </View>
        <Text style={s.setAsHome}>{COPY.setAsHome}</Text>
      </Pressable>

      {club.groups.map((group) => (
        <View key={group.id} style={s.strip}>
          <GroupAtClubRow group={group} clubName={club.name} dots={false} />
        </View>
      ))}
    </View>
  );
}

function ChosenClub({
  club,
  onChange,
}: {
  readonly club: SearchedClub;
  readonly onChange: () => void;
}) {
  return (
    <View style={s.chosen}>
      <View style={s.clubWords} accessible accessibilityLabel={chosenClubLabel(club)}>
        <Text style={s.clubName} numberOfLines={1}>
          {club.name}
        </Text>
        <Text style={s.clubLine} numberOfLines={1}>
          {clubLine(club, { distance: true })}
        </Text>
      </View>
      <Button
        label={COPY.change}
        accessibilityLabel={COPY.changeLabel}
        variant="secondary"
        size="sm"
        onPress={onChange}
      />
    </View>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  qualifier: { ...theme.type.tiny, color: theme.color.muted, textTransform: 'none' },
  hint: { ...theme.type.tiny, color: theme.color.muted },
  note: { ...theme.type.tiny, color: theme.color.muted },
  nothing: { alignItems: 'center', gap: theme.space.xxs, paddingVertical: theme.space.md },
  nothingTitle: { ...theme.type.cardTitle, color: theme.color.ink, textAlign: 'center' },
  // The tinted row bleeds to the card's edges, as play 9 draws the band: the card's own padding,
  // given back on the inside.
  club: {
    marginHorizontal: -theme.space.md,
    paddingHorizontal: theme.space.md,
    gap: theme.space.sm,
  },
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  tinted: { backgroundColor: theme.color.amberSoft, paddingBottom: theme.space.sm },
  clubHead: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingVertical: theme.space.sm,
    minHeight: theme.size.minTouch,
  },
  pressed: { opacity: 0.7 },
  clubWords: { flex: 1, gap: theme.space.xxs },
  clubNameRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  clubName: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
  clubLine: { ...theme.type.tiny, color: theme.color.muted },
  setAsHome: { ...theme.type.rlValue, color: theme.color.ink },
  strip: {
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.btn,
    padding: theme.space.sm,
  },
  chosen: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    backgroundColor: theme.color.mintSoft,
    borderRadius: theme.radius.btn,
    padding: theme.space.md,
  },
});
