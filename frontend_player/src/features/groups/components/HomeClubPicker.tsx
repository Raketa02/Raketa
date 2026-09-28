/**
 * **New group's home club** — the field, and the five things it can be showing (play 6–11;
 * #512), drawn as the 2026-09-27 mocks draw them. **Required** (PRD #500 overrides play 4 by name),
 * and not labelled so: Create the group stays disabled until a club is chosen, which says it.
 *
 * | state | what is drawn |
 * | --- | --- |
 * | empty | the field, and nothing under it |
 * | searching | the field, and **a raised card per club** (`ClubCard`): name over district · distance · sports, a *Set as home* pill, the whole head the tap |
 * | no match | *No club called "…"*, and that only clubs in Raketa can be one |
 * | a club with groups | the same card, its groups on a recessed `paper3` band under the head, each with what the reader can do about it (stories 20–22) |
 * | chosen | the field gone; the club on `mintSoft` with its distance and **Change**, and nothing under it |
 *
 * **The picker holds no state.** The form is the screen's — the text, the answer and the choice —
 * because the page's scroll is what asks for the next twenty clubs, and the results sit inside it.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, TextField, theme } from '@/shared/ui';

import type { SearchedClub } from '../domain/group';
import { searchOutcome } from '../domain/groupRules';
import type { ClubSearchState } from '../hooks/useClubSearch';

import { ClubCard } from './ClubCard';
import { FormSection } from './FormSection';
import { GroupAtClubRow } from './GroupAtClubRow';
import { GROUPS_COPY } from './groupsCopy';
import { chosenClubLabel, clubLine, noClubCalled, setAsHomeLabel } from './groupsPresentation';
import { ReadFailure } from './ReadFailure';

const COPY = GROUPS_COPY.newGroup;

export interface HomeClubPickerProps {
  readonly typed: string;
  readonly onType: (text: string) => void;
  readonly search: ClubSearchState;
  readonly chosen: SearchedClub | undefined;
  readonly onChoose: (club: SearchedClub) => void;
  readonly onChange: () => void;
}

export function HomeClubPicker({
  typed,
  onType,
  search,
  chosen,
  onChoose,
  onChange,
}: HomeClubPickerProps) {
  return (
    <FormSection label={COPY.homeClub}>
      {chosen !== undefined ? (
        <ChosenClub club={chosen} onChange={onChange} />
      ) : (
        <>
          <TextField
            label={COPY.homeClub}
            labelHidden
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
    </FormSection>
  );
}

function Results({
  search,
  onChoose,
}: {
  readonly search: ClubSearchState;
  readonly onChoose: (club: SearchedClub) => void;
}) {
  if (search.text === '') return null;

  if (search.error !== null && search.answer === undefined) {
    return <ReadFailure error={search.error} onRetry={search.retry} />;
  }

  if (search.answer === undefined) return null;

  const outcome = searchOutcome(search.answer);
  if (outcome.kind !== 'clubs') {
    return (
      <View style={s.nothing}>
        <Text style={s.nothingTitle}>{noClubCalled(search.answer.text)}</Text>
        <Text style={s.note}>{COPY.noClubNote}</Text>
      </View>
    );
  }

  return (
    <View style={s.results}>
      {search.answer.clubs.map((club) => (
        <ClubResult key={club.id} club={club} onChoose={onChoose} />
      ))}
    </View>
  );
}

function ClubResult({
  club,
  onChoose,
}: {
  readonly club: SearchedClub;
  readonly onChoose: (club: SearchedClub) => void;
}) {
  return (
    <ClubCard club={club} headLabel={setAsHomeLabel(club)} onChoose={() => onChoose(club)}>
      {club.groups.length > 0
        ? club.groups.map((group) => (
            <GroupAtClubRow key={group.id} group={group} clubName={club.name} variant="homeClub" />
          ))
        : null}
    </ClubCard>
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
          {clubLine(club)}
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
  note: { ...theme.type.tiny, color: theme.color.muted },
  nothing: { alignItems: 'center', gap: theme.space.xxs, paddingVertical: theme.space.md },
  nothingTitle: { ...theme.type.cardTitle, color: theme.color.ink, textAlign: 'center' },
  results: { gap: theme.space.sm },
  clubWords: { flex: 1, gap: theme.space.xxs },
  clubName: { ...theme.type.cardTitle, color: theme.color.ink },
  clubLine: { ...theme.type.tiny, color: theme.color.muted },
  chosen: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    backgroundColor: theme.color.mintSoft,
    borderWidth: 1,
    borderColor: theme.color.mintLine,
    borderRadius: theme.radius.btn,
    padding: theme.space.md,
  },
});
