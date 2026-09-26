/**
 * **The two cards only an official group's form has** — the WhatsApp group size and the Sports —
 * shared by New official group ([#516](https://github.com/Raketa02/Raketa/issues/516)) and the
 * group's settings ([#517](https://github.com/Raketa02/Raketa/issues/517)), which ask the same four
 * things. The Name and *Who can join* are `groups`' own two cards; these are the other two, drawn
 * once so the two forms cannot drift apart. Each screen holds its own state and hands it in.
 */

import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { sportColour, sportLabel } from '@/features/onboarding/types';
import { Card, Chip, TextField, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { WHATSAPP_SIZE, type OfficialGroupsClub } from '../domain/officialGroup';
import { whatsAppSizeFrom } from '../schemas/officialGroupForm';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { sportsCardLine, whatsAppSizeRule } from './administratorPresentation';

const COPY = ADMINISTRATOR_COPY.newGroup;

/**
 * **WhatsApp group size** — required, 2–1024. The field says the rule the moment what is typed is
 * not a whole number in it, and otherwise what the server refused about it.
 */
export function WhatsAppSizeCard({
  size,
  onSize,
  refused,
}: {
  /** As typed — the field is text. */
  readonly size: string;
  readonly onSize: (size: string) => void;
  /** A refusal the server said about the size, on the field. */
  readonly refused?: string | undefined;
}) {
  const error =
    size.trim() !== '' && whatsAppSizeFrom(size) === undefined ? whatsAppSizeRule() : refused;

  return (
    <Card style={s.card}>
      <TextField
        label={COPY.whatsAppSize}
        recessed
        placeholder={COPY.whatsAppSizePlaceholder}
        value={size}
        onChangeText={onSize}
        keyboardType="number-pad"
        maxLength={String(WHATSAPP_SIZE.max).length}
        {...(error === undefined ? {} : { error })}
      />
    </Card>
  );
}

/**
 * **Sports** — one chip per sport **the club offers**, any number ticked: the only sports an
 * official group may declare. Until the club is read there is nothing to offer, and `unread` says
 * why where the read failed.
 */
export function SportsCard({
  club,
  ticked,
  onToggle,
  refused,
  unread,
}: {
  readonly club: OfficialGroupsClub | undefined;
  readonly ticked: readonly Sport[];
  readonly onToggle: (sport: Sport) => void;
  /** A refusal the server said about the sports, on the card. */
  readonly refused?: string | undefined;
  /** What the card says while the club is unread — a failed read, or nothing. */
  readonly unread?: ReactNode;
}) {
  return (
    <Card style={s.card}>
      <Text style={s.label}>{COPY.sports}</Text>
      {club === undefined ? (
        unread
      ) : (
        <>
          <View style={s.chips}>
            {club.sports.map((sport) => (
              <Chip
                key={sport}
                label={sportLabel(sport)}
                dot={sportColour(sport)}
                selected={ticked.includes(sport)}
                onPress={() => onToggle(sport)}
              />
            ))}
          </View>
          <Text style={s.note}>{sportsCardLine(club.name)}</Text>
        </>
      )}
      {refused === undefined ? null : (
        <Text accessibilityRole="alert" style={s.refused}>
          {refused}
        </Text>
      )}
    </Card>
  );
}

/** The sports ticked, with this one ticked or unticked. */
export function toggled(sports: readonly Sport[], sport: Sport): readonly Sport[] {
  return sports.includes(sport) ? sports.filter((held) => held !== sport) : [...sports, sport];
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  // `flab` labels a control you are about to operate — New group's card labels, drawn the same.
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
  note: { ...theme.type.tiny, color: theme.color.muted },
  // The field's own error line, for the one card that is not a field: 6.13's words, in `red`.
  refused: { ...theme.type.tiny, color: theme.color.red },
});
