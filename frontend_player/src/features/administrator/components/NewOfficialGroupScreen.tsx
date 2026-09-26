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
 * - **WhatsApp group size** — **required**, 2–1024, where club 10 draws it *optional* (PRD #500
 *   overrides by name). The field says the rule the moment what is typed is not a whole number in it.
 * - **Sports** — **required**, one chip per sport **the club offers**, any number ticked. The sports
 *   are the club's as the Groups tab's read serves them, so the form offers exactly what may be
 *   declared.
 *
 * **Create the group** is pressable only once the form's one schema answers a group
 * (`newOfficialGroupFrom`), busy while the create is in flight — two creates are two groups — and on
 * success **replaces** this screen with the group's page and says *Group created* over it, so *back*
 * from a new group is the list. A refusal is said **on the field it names** (`details.field`), and
 * anything the form cannot name under the button.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  GroupNameCard,
  ReadFailure,
  WhoCanJoinCard,
  type JoinPolicy,
} from '@/features/groups/types';
import { sportColour, sportLabel } from '@/features/onboarding/types';
import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
import { showToast } from '@/shared/store/toast.store';
import { Button, Card, Chip, Note, ScreenHeader, Tag, TextField, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { WHATSAPP_SIZE } from '../domain/officialGroup';
import { useAreaClubName } from '../hooks/useAreaAccess';
import { useAdministeredGroups } from '../hooks/useOfficialGroups';
import { useCreateOfficialGroup } from '../hooks/useOfficialGroupWrites';
import { newOfficialGroupFrom, whatsAppSizeFrom } from '../schemas/newOfficialGroupForm';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import {
  createRefusal,
  refusedField,
  sportsCardLine,
  whatsAppSizeRule,
} from './administratorPresentation';
import { officialGroupRoute } from './administratorRoutes';

export function NewOfficialGroupScreen({ clubId }: { readonly clubId: string }) {
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
      : newOfficialGroupFrom({ name, joinPolicy, whatsAppSize, sports }, club.sports);

  // A refusal belongs to the form as it was sent; the next change to any field is a new form.
  const edited =
    <T,>(set: (value: T) => void) =>
    (value: T) => {
      if (create.error !== null) create.reset();
      set(value);
    };

  const refusal = create.error === null ? undefined : createRefusal(create.error);
  const field = create.error === null ? undefined : refusedField(create.error);
  const onField = (name: typeof field) => (field === name ? refusal : undefined);
  const sizeTyped = whatsAppSize.trim() !== '';
  const sizeError =
    sizeTyped && whatsAppSizeFrom(whatsAppSize) === undefined
      ? whatsAppSizeRule()
      : onField('whatsapp_size');

  function toggle(sport: Sport) {
    edited(setSports)(
      sports.includes(sport) ? sports.filter((held) => held !== sport) : [...sports, sport],
    );
  }

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
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader title={COPY.title} onBack={() => router.back()} backLabel={COPY.back} />

      <KeyboardAvoidingView style={s.body} behavior={KEYBOARD_AVOIDANCE}>
        <ScrollView contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
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

          <Card style={s.card}>
            <TextField
              label={COPY.whatsAppSize}
              recessed
              placeholder={COPY.whatsAppSizePlaceholder}
              value={whatsAppSize}
              onChangeText={edited(setWhatsAppSize)}
              keyboardType="number-pad"
              maxLength={String(WHATSAPP_SIZE.max).length}
              {...(sizeError === undefined ? {} : { error: sizeError })}
            />
          </Card>

          <Card style={s.card}>
            <Text style={s.label}>{COPY.sports}</Text>
            {club === undefined && read.error !== null ? (
              <ReadFailure error={read.error} onRetry={() => void read.refetch()} />
            ) : null}
            {club === undefined ? null : (
              <>
                <View style={s.chips}>
                  {club.sports.map((sport) => (
                    <Chip
                      key={sport}
                      label={sportLabel(sport)}
                      dot={sportColour(sport)}
                      selected={sports.includes(sport)}
                      onPress={() => toggle(sport)}
                    />
                  ))}
                </View>
                <Text style={s.note}>{sportsCardLine(club.name)}</Text>
              </>
            )}
            {onField('sports') === undefined ? null : (
              <Text accessibilityRole="alert" style={s.refused}>
                {onField('sports')}
              </Text>
            )}
          </Card>

          <Button
            label={COPY.create}
            size="xl"
            disabled={group === undefined}
            busy={create.isPending}
            busyLabel={COPY.creating}
            onPress={submit}
          />

          {refusal !== undefined && field === undefined ? (
            <Note variant="coral" accessibilityRole="alert">
              {refusal}
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
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  card: { gap: theme.space.sm },
  // `flab` labels a control you are about to operate — New group's card labels, drawn the same.
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  fixed: { flexDirection: 'row' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
  note: { ...theme.type.tiny, color: theme.color.muted },
  // The field's own error line, for the one card that is not a field: 6.13's words, in `red`.
  refused: { ...theme.type.tiny, color: theme.color.red },
});
