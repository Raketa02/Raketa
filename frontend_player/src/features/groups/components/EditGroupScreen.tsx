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
 * **Switching to Anyone is asked first** (#529): a save that turns People I approve into Anyone
 * opens a sheet saying what it does — *anyone can join, including players with pending requests* —
 * and only its *Save* sends it; closing it keeps the form as it is, unsaved. Any other save goes at
 * once. The sheet is `OpenToAnyoneSheet`, which an official group's settings open too. The *Who can join* card carries no note here: the Owner is past choosing what a group is.
 *
 * **Switching to Anyone shows the people it admitted** (story 76): everybody waiting is in at once,
 * and the answer says who, in the order they asked, as a card under the button — *LET IN · 2*,
 * a face and a name each (`AdmittedCard`). It stays until the next save.
 *
 * A refusal the form can name — the name, the ownership, the group gone — is said under the
 * button in the form's words; any other says why it failed. Nothing is recorded on a refusal, so
 * the next press is the whole edit again.
 */

import { router } from 'expo-router';
import { useRef, useState } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { codeMessage } from '@/shared/errors';
import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
import { behindOverlay, Button, Note, ScreenHeader, theme, useTabBarReach } from '@/shared/ui';

import type { Group } from '../domain/group';
import { detailsUnchanged } from '../domain/groupInfo';
import { useGroup } from '../hooks/useGroups';
import { useEditGroup } from '../hooks/useGroupWrites';
import { groupDetailsFrom } from '../schemas/groupDetailsForm';

import { AdmittedCard } from './AdmittedCard';
import { GroupNameCard, WhoCanJoinCard } from './GroupFormCards';
import { GROUPS_COPY } from './groupsCopy';
import { EDIT_REFUSALS } from './groupsPresentation';
import { OpenToAnyoneSheet } from './OpenToAnyoneSheet';
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
  // Ends at the bar's reach, its own gap clear of it (10.1, ADR-0210 §3, #881).
  const reach = useTabBarReach();
  const [name, setName] = useState(group.name);
  const [joinPolicy, setJoinPolicy] = useState(group.joinPolicy);
  const edit = useEditGroup(group.id);

  const [asking, setAsking] = useState(false);
  const saveButton = useRef<View>(null);

  const details = groupDetailsFrom({ name, joinPolicy });
  const unchanged = detailsUnchanged({ name, joinPolicy }, group);
  const admitted = edit.data?.admitted ?? [];
  // What the group is now against what the form says — not against the last save's answer, which
  // is the same thing once it lands and writes the page's key.
  const opensToAnyone = group.joinPolicy === 'PEOPLE_I_APPROVE' && joinPolicy === 'ANYONE';

  function send() {
    if (details === undefined || unchanged) return;
    // The server collapses what the form cannot see — runs of spaces — so the field takes the
    // name as saved, and *Saved* is true of what is on screen.
    edit.mutate(details, { onSuccess: ({ group: saved }) => setName(saved.name) });
  }

  function save() {
    if (details === undefined || unchanged) return;
    if (opensToAnyone) {
      setAsking(true);
      return;
    }
    send();
  }

  function confirm() {
    setAsking(false);
    send();
  }

  return (
    <KeyboardAvoidingView style={s.body} behavior={KEYBOARD_AVOIDANCE}>
      <ScrollView
        contentContainerStyle={[s.content, { paddingBottom: reach + theme.space.lg }]}
        keyboardShouldPersistTaps="handled"
      >
        <GroupNameCard name={name} onName={setName} />
        <WhoCanJoinCard joinPolicy={joinPolicy} onJoinPolicy={setJoinPolicy} noSportNote={false} />

        {/* Hidden from a screen reader while the sheet is up: one label on the button and on the
            sheet's act, so the first press reaches the button and the second the act. */}
        <View ref={saveButton} {...behindOverlay(asking)}>
          <Button
            label={unchanged ? COPY.saved : COPY.save}
            variant={unchanged ? 'settled' : 'primary'}
            size="xl"
            disabled={details === undefined || unchanged}
            busy={edit.isPending}
            busyLabel={COPY.saving}
            onPress={save}
          />
        </View>

        {edit.error !== null ? (
          <Note variant="coral" accessibilityRole="alert">
            {codeMessage(EDIT_REFUSALS, edit.error)}
          </Note>
        ) : null}

        {admitted.length > 0 ? <AdmittedCard people={admitted} /> : null}
      </ScrollView>

      <OpenToAnyoneSheet
        visible={asking}
        onClose={() => setAsking(false)}
        onConfirm={confirm}
        returnFocusTo={saveButton}
      />
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { flex: 1 },
  content: {
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.sm,
  },
});
