/**
 * **New official group** — full screen, pushed over the Groups tab, with a back arrow that discards
 * the form (club 10, plus a **Sports** card; PRD #500 stories 125–126;
 * [#516](https://github.com/Raketa02/Raketa/issues/516)).
 *
 * Five cards and a button, club 10's order with Sports last:
 *
 * - **Name** — *Same name as the WhatsApp group*, New group's own card (`GroupNameCard`).
 * - **Home club** — the club, **fixed**, as a mint tag: an official group's home is its club
 *   (ADR-0183 §8), so there is nothing to choose.
 * - **Who can join** — *Anyone* or *People I approve*, New group's card without its *no sport to
 *   pick* note, which is false here.
 * - **Group size** — the WhatsApp group size, labelled without the app's name since #529;
 *   **required**, 2–1024, where club 10 draws it *optional* (PRD #500 overrides by name). The field
 *   says the rule the moment what is typed is not a whole number in it.
 * - **Sports** — **required**, one chip per sport **the club offers**, any number ticked. The sports
 *   are the club's as the Groups tab's read serves them, so the form offers exactly what may be
 *   declared.
 *
 * **Create the group** is pressable only once the form's one schema answers a group
 * (`officialGroupSettingsFrom`), busy while the create is in flight — two creates are two groups — and on
 * success **replaces** this screen with the group's page and says *Group created* over it, so *back*
 * from a new group is the list. A refusal is said **on the field it names** (`details.field`), and
 * anything the form cannot name under the button.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet, Text, View } from 'react-native';

import {
  GroupNameCard,
  ReadFailure,
  WhoCanJoinCard,
  type JoinPolicy,
} from '@/features/groups/types';
import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
import { showToast } from '@/shared/store/toast.store';
import {
  Button,
  Card,
  Note,
  ScreenHeader,
  Tag,
  theme,
  TopSafeArea,
  useTabBarReach,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { useAreaClubName } from '../hooks/useAreaAccess';
import { useAdministeredGroups } from '../hooks/useOfficialGroups';
import { useCreateOfficialGroup } from '../hooks/useOfficialGroupWrites';
import { officialGroupSettingsFrom } from '../schemas/officialGroupForm';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { formRefusal, type FormField } from './administratorPresentation';
import { officialGroupRoute } from './administratorRoutes';
import { SportsCard, toggled, WhatsAppSizeCard } from './OfficialGroupFormCards';

export function NewOfficialGroupScreen({ clubId }: { readonly clubId: string }) {
  // Ends at the bar's reach, its own gap clear of it (10.1, ADR-0210 §3, #881).
  const reach = useTabBarReach();
  const COPY = ADMINISTRATOR_COPY.newGroup;
  const clubName = useAreaClubName(clubId);
  const read = useAdministeredGroups(clubId);
  const club = read.data?.club;
  const create = useCreateOfficialGroup(clubId);

  const [name, setName] = useState('');
  const [joinPolicy, setJoinPolicy] = useState<JoinPolicy>('ANYONE');
  const [whatsAppSize, setWhatsAppSize] = useState('');
  const [sports, setSports] = useState<readonly Sport[]>([]);

  const group =
    club === undefined
      ? undefined
      : officialGroupSettingsFrom({ name, joinPolicy, whatsAppSize, sports }, club.sports);

  // A refusal belongs to the form as it was sent; the next change to any field is a new form.
  const edited =
    <T,>(set: (value: T) => void) =>
    (value: T) => {
      if (create.error !== null) create.reset();
      set(value);
    };

  const refused = formRefusal(create.error);
  const onField = (name: FormField) => (refused?.field === name ? refused.words : undefined);

  function submit() {
    if (group === undefined) return;
    create.mutate(group, {
      onSuccess: (created) => {
        router.replace(officialGroupRoute(clubId, created.id));
        showToast({ message: COPY.created, tone: 'ok' });
      },
    });
  }

  return (
    <TopSafeArea style={s.screen}>
      <ScreenHeader title={COPY.title} onBack={() => router.back()} backLabel={COPY.back} />

      <KeyboardAvoidingView style={s.body} behavior={KEYBOARD_AVOIDANCE}>
        <ScrollView
          contentContainerStyle={[s.content, { paddingBottom: reach + theme.space.lg }]}
          keyboardShouldPersistTaps="handled"
        >
          <GroupNameCard
            name={name}
            onName={edited(setName)}
            placeholder={COPY.namePlaceholder}
            {...(onField('name') === undefined ? {} : { error: onField('name') })}
          />

          <Card style={s.card}>
            <Text style={s.label}>{COPY.homeClub}</Text>
            <View style={s.fixed}>
              <Tag label={clubName} variant="ok" />
            </View>
          </Card>

          <WhoCanJoinCard
            joinPolicy={joinPolicy}
            onJoinPolicy={edited(setJoinPolicy)}
            noSportNote={false}
          />

          <WhatsAppSizeCard
            size={whatsAppSize}
            onSize={edited(setWhatsAppSize)}
            refused={onField('whatsapp_size')}
          />

          <SportsCard
            club={club}
            ticked={sports}
            onToggle={(sport) => edited(setSports)(toggled(sports, sport))}
            refused={onField('sports')}
            unread={
              read.error === null ? null : (
                <ReadFailure error={read.error} onRetry={() => void read.refetch()} />
              )
            }
          />

          <Button
            label={COPY.create}
            size="xl"
            disabled={group === undefined}
            busy={create.isPending}
            busyLabel={COPY.creating}
            onPress={submit}
          />

          {refused !== undefined && refused.field === undefined ? (
            <Note variant="coral" accessibilityRole="alert">
              {refused.words}
            </Note>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </TopSafeArea>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { flex: 1 },
  content: {
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.sm,
  },
  card: { gap: theme.space.sm },
  // `flab` labels a control you are about to operate — New group's card labels, drawn the same.
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  fixed: { flexDirection: 'row' },
});
