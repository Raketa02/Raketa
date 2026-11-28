/**
 * **Pick a club near where you play** — the other way to a Location area, for a player whose phone
 * will not say where she is ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §10, [#733](https://github.com/Rakieta02/Rakieta/issues/733)). The location step offers it after a
 * refusal — denied, blocked or no fix — and You's *Where you play* offers it always.
 *
 * | state | what is drawn |
 * | --- | --- |
 * | empty | the field, and nothing under it |
 * | searching | a raised card per club (`ClubCard`), name over *district · sports*, a *Pick* pill, the whole head the tap |
 * | no match | *No club called "…"*, and that only clubs in Rakieta can be picked |
 * | more than a page | *More clubs* under the twentieth |
 * | chosen | the field gone; the club on `mintSoft`, by name and district, with **Change** |
 *
 * **It is the home-club search, not a second one.** `groups` owns the search and its card, and
 * this file draws them with its own words: by name or district, **A–Z for a player with no area
 * yet** — the server's order, since no distance can be measured from an area that does not exist —
 * and nearest first for one who has. **The groups at a club are not drawn**: the card answers
 * *where do you play?*, and a club's groups are New group's question.
 *
 * **The picker holds the text and the search; the caller holds the choice.** On the step a pick
 * goes into the draft and nothing is sent until the commit; on the tab it is written at once. So
 * `chosen` and `onPick` are the caller's, and `saving` lets the tab say a write is on its way on
 * the one control the chosen card has. A pick hands on the club's id, name and district — the id
 * is what crosses the wire, the name and district are what the chosen card draws.
 *
 * **More clubs is a control, not a scroll**: both hosts' scrollers belong to their chrome, and the
 * search answers twenty at a time. A player who knows her club's name narrows to it by typing;
 * one who typed a district reaches the twenty-first by pressing.
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  ClubCard,
  ReadFailure,
  clubLine,
  noClubCalled,
  useHomeClubSearch,
  type ClubSearchState,
  type SearchedClub,
} from '@/features/groups/types';
import { Button, TextField, theme } from '@/shared/ui';

import type { PickedClub } from '../domain/ProfileDraft';

import {
  CHANGE_CLUB,
  CHANGE_CLUB_LABEL,
  CLUB_SEARCH_PLACEHOLDER,
  MORE_CLUBS,
  NO_CLUB_NOTE,
  PICK_A_CLUB,
  PICK_WORD,
  SAVING_WORD,
  pickClubLabel,
  pickedClubLabel,
} from './locationPresentation';

export interface AreaClubPickerProps {
  /** The club that is the area, or is being written as it. The field is drawn while there is none. */
  readonly chosen: PickedClub | undefined;
  readonly onPick: (club: PickedClub) => void;
  /** *Change*: the caller lets go of the club, and the field comes back. */
  readonly onChange: () => void;
  /** The tab's write is on its way — *Change* says so and waits. */
  readonly saving?: boolean;
}

export function AreaClubPicker({ chosen, onPick, onChange, saving = false }: AreaClubPickerProps) {
  const [typed, setTyped] = useState('');

  return (
    <View style={s.section}>
      <Text style={s.label}>{PICK_A_CLUB}</Text>
      {chosen !== undefined ? (
        <ChosenClub club={chosen} saving={saving} onChange={onChange} />
      ) : (
        <ClubSearch typed={typed} onType={setTyped} onPick={onPick} />
      )}
    </View>
  );
}

/** Mounted only while nothing is chosen, so the search asks nothing behind a chosen card. */
function ClubSearch({
  typed,
  onType,
  onPick,
}: {
  readonly typed: string;
  readonly onType: (text: string) => void;
  readonly onPick: (club: PickedClub) => void;
}) {
  const search = useHomeClubSearch(typed);

  return (
    <>
      <TextField
        label={PICK_A_CLUB}
        labelHidden
        placeholder={CLUB_SEARCH_PLACEHOLDER}
        value={typed}
        onChangeText={onType}
        autoCorrect={false}
        autoCapitalize="none"
        returnKeyType="search"
      />
      <Results search={search} onPick={onPick} />
    </>
  );
}

function Results({
  search,
  onPick,
}: {
  readonly search: ClubSearchState;
  readonly onPick: (club: PickedClub) => void;
}) {
  if (search.text === '') return null;

  if (search.error !== null && search.answer === undefined) {
    return <ReadFailure error={search.error} onRetry={search.retry} />;
  }

  if (search.answer === undefined) return null;

  if (search.answer.clubs.length === 0) {
    return (
      <View style={s.nothing}>
        <Text style={s.nothingTitle}>{noClubCalled(search.answer.text)}</Text>
        <Text style={s.note}>{NO_CLUB_NOTE}</Text>
      </View>
    );
  }

  return (
    <View style={s.results}>
      {search.answer.clubs.map((club) => (
        <ClubCard
          key={club.id}
          club={club}
          headLabel={pickClubLabel(club.name, clubLine(club))}
          chooseWord={PICK_WORD}
          onChoose={() => onPick(pickedFrom(club))}
        />
      ))}
      {search.answer.nextPage === null ? null : (
        <View style={s.more}>
          <Button label={MORE_CLUBS} variant="secondary" size="sm" onPress={search.loadMore} />
        </View>
      )}
    </View>
  );
}

function ChosenClub({
  club,
  saving,
  onChange,
}: {
  readonly club: PickedClub;
  readonly saving: boolean;
  readonly onChange: () => void;
}) {
  return (
    // Mint is *settled*: on the tab the ground turns mint only once the write has landed, and
    // stands on the ordinary surface while *Change* says *Saving…*.
    <View style={[s.chosen, saving ? s.onItsWay : undefined]}>
      <View style={s.clubWords} accessible accessibilityLabel={pickedClubLabel(club)}>
        <Text style={s.clubName} numberOfLines={1}>
          {club.name}
        </Text>
        <Text style={s.clubLine} numberOfLines={1}>
          {club.district}
        </Text>
      </View>
      <Button
        label={CHANGE_CLUB}
        accessibilityLabel={CHANGE_CLUB_LABEL}
        variant="secondary"
        size="sm"
        busy={saving}
        busyLabel={SAVING_WORD}
        onPress={onChange}
      />
    </View>
  );
}

/** What the area keeps of a searched club: the id it is sent by, and the two words it is drawn by. */
function pickedFrom(club: SearchedClub): PickedClub {
  return { id: club.id, name: club.name, district: club.district };
}

const s = StyleSheet.create({
  section: { gap: theme.space.sm, paddingTop: theme.space.xs },
  // New group's section label (`FormSection`): the field is a control about to be operated.
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  note: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
  nothing: { alignItems: 'center', gap: theme.space.xxs, paddingVertical: theme.space.md },
  nothingTitle: { ...theme.type.cardTitle, color: theme.color.ink, textAlign: 'center' },
  results: { gap: theme.space.sm },
  more: { alignItems: 'flex-start' },
  clubWords: { flex: 1, gap: theme.space.xxs },
  clubName: { ...theme.type.cardTitle, color: theme.color.ink },
  clubLine: { ...theme.type.tiny, color: theme.color.muted },
  // New group's chosen home club, drawn the same: the settled ground, because the answer is in.
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
  onItsWay: { backgroundColor: theme.color.surface, borderColor: theme.color.line },
});
