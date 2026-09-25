/**
 * **Edit group** — the Owner renames the group and changes who can join
 * ([#514](https://github.com/Raketa02/Raketa/issues/514), PRD #500 stories 75–76). No mock draws
 * it: it is *the New group form's Name and Who can join cards and Save*, and those two cards are
 * New group's own (`GroupFormCards`). The home club is not here — it never changes (ADR-0183 §2).
 *
 * **Save is the You tab's save** (ADR-0179): *Save* while the form differs from the group, and
 * *Saved*, settled, while it does not — so a save that would record nothing is never a round trip
 * — busy while in flight, and the screen stays. What the save answers is the group as its page
 * reads it, written under the page's key, so *back* lands on the new name.
 *
 * **Switching to Anyone shows the people it admitted** (story 76): everybody waiting is in at once,
 * and the answer says who, in the order they asked, as a card under the button — *LET IN · 2*,
 * a face and a name each. It stays until the next save.
 *
 * A refusal the form can name — the name, the ownership, the group gone — is said under the
 * button in the form's words; any other says why it failed. Nothing is recorded on a refusal
 * (`block_state_unavailable` included), so the next press is the whole edit again.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { codeMessage } from '@/shared/errors';
import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
import { Button, Card, Note, PlayerPhoto, ScreenHeader, theme } from '@/shared/ui';

import type { Group, GroupPerson } from '../domain/group';
import { detailsUnchanged } from '../domain/groupInfo';
import { useGroup } from '../hooks/useGroups';
import { useEditGroup } from '../hooks/useGroupWrites';
import { groupDetailsFrom } from '../schemas/groupDetailsForm';

import { GroupNameCard, WhoCanJoinCard } from './GroupFormCards';
import { GROUPS_COPY } from './groupsCopy';
import { admittedEyebrow, EDIT_REFUSALS, personName } from './groupsPresentation';
import { ROW_FACE } from './peopleRow';
import { ReadFailure } from './ReadFailure';

const COPY = GROUPS_COPY.editGroup;

export function EditGroupScreen({ groupId }: { readonly groupId: string }) {
  const read = useGroup(groupId);
  const group = read.data;

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader title={COPY.title} onBack={() => router.back()} backLabel={COPY.back} />

      {group !== undefined ? (
        <EditGroupForm group={group} />
      ) : read.error !== null ? (
        <View style={s.content}>
          <ReadFailure
            error={read.error}
            message={codeMessage(GROUPS_COPY.group.refused, read.error)}
            onRetry={() => void read.refetch()}
          />
        </View>
      ) : null}
    </SafeAreaView>
  );
}

/** Mounted once the group is read, so the form opens holding what the group says. */
function EditGroupForm({ group }: { readonly group: Group }) {
  const [name, setName] = useState(group.name);
  const [joinPolicy, setJoinPolicy] = useState(group.joinPolicy);
  const edit = useEditGroup(group.id);

  const details = groupDetailsFrom({ name, joinPolicy });
  const unchanged = detailsUnchanged({ name, joinPolicy }, group);
  const admitted = edit.data?.admitted ?? [];

  function save() {
    if (details === undefined || unchanged) return;
    // The server collapses what the form cannot see — runs of spaces — so the field takes the
    // name as saved, and *Saved* is true of what is on screen.
    edit.mutate(details, { onSuccess: ({ group: saved }) => setName(saved.name) });
  }

  return (
    <KeyboardAvoidingView style={s.body} behavior={KEYBOARD_AVOIDANCE}>
      <ScrollView contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
        <GroupNameCard name={name} onName={setName} />
        <WhoCanJoinCard joinPolicy={joinPolicy} onJoinPolicy={setJoinPolicy} />

        <Button
          label={unchanged ? COPY.saved : COPY.save}
          variant={unchanged ? 'settled' : 'primary'}
          size="xl"
          disabled={details === undefined || unchanged}
          busy={edit.isPending}
          busyLabel={COPY.saving}
          onPress={save}
        />

        {edit.error !== null ? (
          <Note variant="coral" accessibilityRole="alert">
            {codeMessage(EDIT_REFUSALS, edit.error)}
          </Note>
        ) : null}

        {admitted.length > 0 ? <Admitted people={admitted} /> : null}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

/** *LET IN · 2* — who the switch to Anyone admitted, in the order they asked. */
function Admitted({ people }: { readonly people: readonly GroupPerson[] }) {
  return (
    <View style={s.section}>
      <Text accessibilityRole="header" style={s.eyebrow}>
        {admittedEyebrow(people.length)}
      </Text>
      <Card style={s.card}>
        <Text style={s.line}>{COPY.admittedLine}</Text>
        {people.map((person) => (
          <View
            key={person.playerId}
            testID={`admitted-${person.playerId}`}
            style={s.row}
            accessible
            accessibilityLabel={personName(person.name)}
          >
            <PlayerPhoto
              playerId={person.playerId}
              {...(person.photoUrl === undefined ? {} : { photoUrl: person.photoUrl })}
              box={{ kind: 'face', size: ROW_FACE }}
            />
            <Text style={s.name} numberOfLines={1}>
              {personName(person.name)}
            </Text>
          </View>
        ))}
      </Card>
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { flex: 1 },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  section: { gap: theme.space.xs },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  card: { gap: theme.space.sm },
  line: { ...theme.type.tiny, color: theme.color.muted },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
});
