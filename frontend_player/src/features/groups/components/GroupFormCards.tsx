/**
 * **The Name and *Who can join* every group form draws** (play 5, 12;
 * [#514](https://github.com/Rakieta02/Rakieta/issues/514): Edit group is *the New group form's Name
 * and Who can join cards*). One drawing of each control, so the forms cannot drift apart; each
 * screen holds its own state and hands it in.
 *
 * Two shapes of the same controls. **The cards** — Edit group's and the administrator's forms, the
 * field recessed onto `paper` inside a white card. **The bare controls** — `GroupNameField` and
 * `WhoCanJoinChips` — are New group's, drawn on the page under a `FormSection` label since the
 * 2026-09-27 mocks made that screen card-less.
 *
 * The name field stops at 40 characters (`GROUP_NAME_MAX`) — the server trims and counts again.
 * *Who can join* is two chips, *Anyone* first; its card adds the note that there is no sport to
 * pick — the administrator's New official group draws both cards too, *Who can join* without that
 * note (#516).
 */

import { StyleSheet, Text, View } from 'react-native';

import { Card, Chip, TextField, theme } from '@/shared/ui';

import { GROUP_NAME_MAX } from '../domain/group';
import type { JoinPolicy } from '../domain/vocabulary';

import { GROUPS_COPY } from './groupsCopy';

const COPY = GROUPS_COPY.newGroup;

interface GroupNameProps {
  readonly name: string;
  readonly onName: (name: string) => void;
  /** New official group's *Same name as the WhatsApp group* (club 10); a player's form has its own. */
  readonly placeholder?: string;
  /** A refusal the server said about the name, on the field. */
  readonly error?: string;
}

function NameInput({
  name,
  onName,
  placeholder = COPY.namePlaceholder,
  error,
  inCard,
}: GroupNameProps & { readonly inCard: boolean }) {
  return (
    <TextField
      label={COPY.name}
      // On the page the section draws the label; inside a card the field draws its own.
      labelHidden={!inCard}
      recessed={inCard}
      placeholder={placeholder}
      {...(error === undefined ? {} : { error })}
      value={name}
      onChangeText={onName}
      maxLength={GROUP_NAME_MAX}
      autoCapitalize="sentences"
      returnKeyType="next"
    />
  );
}

/** The name field alone, white on the page — its label is the `FormSection` around it. */
export function GroupNameField(props: GroupNameProps) {
  return <NameInput {...props} inCard={false} />;
}

export function GroupNameCard(props: GroupNameProps) {
  return (
    <Card style={s.card}>
      <NameInput {...props} inCard />
    </Card>
  );
}

/** *Anyone* and *People I approve* alone — New group draws them under its own label. */
export function WhoCanJoinChips({
  joinPolicy,
  onJoinPolicy,
}: {
  readonly joinPolicy: JoinPolicy;
  readonly onJoinPolicy: (policy: JoinPolicy) => void;
}) {
  return (
    <View style={s.chips}>
      <Chip
        label={COPY.anyone}
        selected={joinPolicy === 'ANYONE'}
        onPress={() => onJoinPolicy('ANYONE')}
      />
      <Chip
        label={COPY.peopleIApprove}
        selected={joinPolicy === 'PEOPLE_I_APPROVE'}
        onPress={() => onJoinPolicy('PEOPLE_I_APPROVE')}
      />
    </View>
  );
}

export function WhoCanJoinCard({
  joinPolicy,
  onJoinPolicy,
  noSportNote = true,
}: {
  readonly joinPolicy: JoinPolicy;
  readonly onJoinPolicy: (policy: JoinPolicy) => void;
  /**
   * The note that there is no sport to pick — true of a player group being made, which plays
   * whatever its members are rated in, and **false of an official group**, which declares its
   * sports on a card of its own (#516), and of **Edit group**, whose Owner is past choosing what
   * the group is (#529).
   */
  readonly noSportNote?: boolean;
}) {
  return (
    <Card style={s.card}>
      <Text style={s.label}>{COPY.whoCanJoin}</Text>
      <WhoCanJoinChips joinPolicy={joinPolicy} onJoinPolicy={onJoinPolicy} />
      {noSportNote ? <Text style={s.note}>{COPY.noSportNote}</Text> : null}
    </Card>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  chips: { flexDirection: 'row', gap: theme.space.xs },
  note: { ...theme.type.tiny, color: theme.color.muted },
});
