/**
 * **New group** — full screen, with a back arrow that discards the form (play 4–13; PRD #500
 * stories 11–27; #512).
 *
 * Three labelled sections on the page and a button, and nothing else — the 2026-09-27 mocks took
 * the form out of its cards and its explanations off the page: the **name** (up to 40 characters,
 * no suggestions — it can be the WhatsApp group's), the **home club** (`HomeClubPicker`,
 * required), and **who can join**, *Anyone* by default or *People I approve*. **Create the group**
 * is pressable only once the form's one schema answers a group (`newGroupFrom`), is busy while the
 * create is in flight — two creates are two groups, so it takes no second press — and on success
 * **replaces** this screen with the group's page and says *Group created* over it.
 *
 * **The form is this screen's own state and dies with it** (story 11): every open is empty, and
 * the back arrow is leaving, never a commitment (story 12). A refusal the form can name —
 * `group_name_invalid`, `home_club_unknown` — is said under the button in the form's words; any
 * other says why it failed.
 *
 * **More clubs as the page scrolls.** The results sit inside the page's scroller rather than a
 * list of their own — a list inside a form would be two scrollers under one thumb — so the page is
 * what notices its end and asks the search for the next twenty.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { codeMessage } from '@/shared/errors';
import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
import { showToast } from '@/shared/store/toast.store';
import { Button, Note, ScreenHeader, theme } from '@/shared/ui';

import type { SearchedClub } from '../domain/group';
import type { JoinPolicy } from '../domain/vocabulary';
import { useHomeClubSearch } from '../hooks/useClubSearch';
import { useCreateGroup } from '../hooks/useGroupWrites';
import { newGroupFrom } from '../schemas/newGroupForm';

import { FormSection } from './FormSection';
import { GroupNameField, WhoCanJoinChips } from './GroupFormCards';
import { groupRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { CREATE_REFUSALS } from './groupsPresentation';
import { HomeClubPicker } from './HomeClubPicker';
import { nearTheEnd, SCROLL_EVENT_EVERY_MS } from './pageEnd';

const COPY = GROUPS_COPY.newGroup;

/** How a walk finds this page's scroller, to scroll it to its end. */
export const NEW_GROUP_PAGE_TEST_ID = 'new-group-page';

export function NewGroupScreen() {
  const [name, setName] = useState('');
  const [typed, setTyped] = useState('');
  const [homeClub, setHomeClub] = useState<SearchedClub>();
  const [joinPolicy, setJoinPolicy] = useState<JoinPolicy>('ANYONE');

  const search = useHomeClubSearch(typed);
  const create = useCreateGroup();
  const group = newGroupFrom({ name, homeClub, joinPolicy });

  function submit() {
    if (group === undefined) return;
    create.mutate(group, {
      onSuccess: (created) => {
        router.replace(groupRoute(created.id));
        showToast({ message: COPY.created, tone: 'ok' });
      },
    });
  }

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader title={COPY.title} onBack={() => router.back()} backLabel={COPY.back} />

      <KeyboardAvoidingView style={s.body} behavior={KEYBOARD_AVOIDANCE}>
        <ScrollView
          testID={NEW_GROUP_PAGE_TEST_ID}
          contentContainerStyle={s.content}
          keyboardShouldPersistTaps="handled"
          scrollEventThrottle={SCROLL_EVENT_EVERY_MS}
          onScroll={(event) => {
            if (homeClub === undefined && nearTheEnd(event.nativeEvent)) search.loadMore();
          }}
        >
          <FormSection label={COPY.name}>
            <GroupNameField name={name} onName={setName} />
          </FormSection>

          <HomeClubPicker
            typed={typed}
            onType={setTyped}
            search={search}
            chosen={homeClub}
            onChoose={setHomeClub}
            onChange={() => setHomeClub(undefined)}
          />

          <FormSection label={COPY.whoCanJoin}>
            <WhoCanJoinChips joinPolicy={joinPolicy} onJoinPolicy={setJoinPolicy} />
          </FormSection>

          <Button
            label={COPY.create}
            size="xl"
            disabled={group === undefined}
            busy={create.isPending}
            busyLabel={COPY.creating}
            onPress={submit}
          />

          {create.error !== null ? (
            <Note variant="coral" accessibilityRole="alert">
              {codeMessage(CREATE_REFUSALS, create.error)}
            </Note>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { flex: 1 },
  // The sections stand apart by space alone, now that no card bounds them.
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.xl,
  },
});
