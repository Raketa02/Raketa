/**
 * **An official group's settings** — pushed over the You tab from the group's row
 * ([#517](https://github.com/Rakieta02/Rakieta/issues/517), PRD #500 story 131). No mock draws it: it
 * is New official group's four cards over Edit group's *Save* — the name, who can join, the
 * group size and the sports, which are what the group's Administrator said about it at its
 * creation and may say again as its WhatsApp twin changes. The home club and the link are not here:
 * neither ever changes (ADR-0183 §2, §8).
 *
 * **The form opens holding what the group says**, off the group's own read — the page's, so a group
 * opened from Groups a moment ago draws at once. The sports on offer are **the club's**, as that read
 * serves them, so the form offers exactly what may be declared.
 *
 * **Save is Edit group's** (ADR-0179's save): *Save* while the form differs from the group and makes
 * a group (`officialGroupSettingsFrom`), *Saved*, settled, while it says what the group already says
 * (`settingsUnchanged`) — so a save that would record nothing is never a round trip — busy while in
 * flight, never retried, and the screen stays. The answer is the group as its settings left it,
 * written under the page's key; the name field takes the name as the server recorded it.
 *
 * **Switching to Anyone is asked first, as an Owner is asked** (#529, the product owner's ask): a
 * save that turns *People I approve* into *Anyone* opens `groups`' own sheet — *Let anyone join?*,
 * *Selecting Anyone allows anyone to join the group, including players with pending requests.* — and
 * only its *Save* sends the form; *Keep People I approve* keeps it as it is, unsaved. Any other save
 * goes at once.
 *
 * **Switching to Anyone shows who it admitted**: everybody waiting is in at once, and the answer says
 * who, in the order they asked — `groups`' *LET IN · 2* card, under the button, until the next save.
 *
 * **A refusal is said on the field it names** (`details.field`) and forgotten the moment any field
 * changes; anything the form cannot name goes under the button. A removal is the area's to answer
 * (`useRemovalWatch`), once, and is not said here as well.
 */

import { router } from 'expo-router';
import { useRef, useState } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet, View } from 'react-native';

import {
  AdmittedCard,
  GroupNameCard,
  OpenToAnyoneSheet,
  ReadFailure,
  WhoCanJoinCard,
} from '@/features/groups/types';
import { codeMessage } from '@/shared/errors';
import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
import {
  behindOverlay,
  Button,
  Note,
  ScreenHeader,
  theme,
  TopSafeArea,
  useTabBarReach,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { OfficialGroup } from '../domain/officialGroup';
import { settingsUnchanged } from '../domain/officialGroupRules';
import { useOfficialGroup } from '../hooks/useOfficialGroups';
import { useSaveSettings } from '../hooks/useOfficialGroupWrites';
import { officialGroupSettingsFrom } from '../schemas/officialGroupForm';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { formRefusal, type FormField } from './administratorPresentation';
import { SportsCard, toggled, WhatsAppSizeCard } from './OfficialGroupFormCards';

const COPY = ADMINISTRATOR_COPY.settings;

export function GroupSettingsScreen({
  clubId,
  groupId,
}: {
  readonly clubId: string;
  readonly groupId: string;
}) {
  const read = useOfficialGroup(clubId, groupId);
  const group = read.data;

  return (
    <TopSafeArea style={s.screen}>
      <ScreenHeader title={COPY.title} onBack={() => router.back()} backLabel={COPY.back} />

      {group !== undefined ? (
        <SettingsForm clubId={clubId} group={group} />
      ) : read.error !== null ? (
        <View style={s.content}>
          <ReadFailure
            error={read.error}
            message={codeMessage(COPY.refused, read.error)}
            onRetry={() => void read.refetch()}
          />
        </View>
      ) : null}
    </TopSafeArea>
  );
}

/** Mounted once the group is read, so the form opens holding what the group says. */
function SettingsForm({
  clubId,
  group,
}: {
  readonly clubId: string;
  readonly group: OfficialGroup;
}) {
  // Ends at the bar's reach, its own gap clear of it (10.1, ADR-0210 §3, #881).
  const reach = useTabBarReach();
  const [name, setName] = useState(group.name);
  const [joinPolicy, setJoinPolicy] = useState(group.joinPolicy);
  const [whatsAppSize, setWhatsAppSize] = useState(String(group.whatsAppSize));
  const [sports, setSports] = useState<readonly Sport[]>(group.sports);
  const save = useSaveSettings(clubId, group.id);

  const [asking, setAsking] = useState(false);
  const saveButton = useRef<View>(null);

  const settings = officialGroupSettingsFrom(
    { name, joinPolicy, whatsAppSize, sports },
    group.homeClub.sports,
  );
  const unchanged = settings !== undefined && settingsUnchanged(settings, group);
  const admitted = save.data?.admitted ?? [];
  // What the group is now against what the form says — Edit group's rule, for the same switch.
  const opensToAnyone = group.joinPolicy === 'PEOPLE_I_APPROVE' && joinPolicy === 'ANYONE';

  // A refusal belongs to the form as it was sent; the next change to any field is a new form.
  const edited =
    <T,>(set: (value: T) => void) =>
    (value: T) => {
      if (save.error !== null) save.reset();
      set(value);
    };

  const refused = formRefusal(save.error);
  const onField = (name: FormField) => (refused?.field === name ? refused.words : undefined);

  function send() {
    if (settings === undefined || unchanged) return;
    // The server collapses what the form cannot see — runs of spaces — so the field takes the name
    // as saved, and *Saved* is true of what is on screen.
    save.mutate(settings, { onSuccess: ({ group: saved }) => setName(saved.name) });
  }

  function submit() {
    if (settings === undefined || unchanged) return;
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
        <GroupNameCard
          name={name}
          onName={edited(setName)}
          placeholder={ADMINISTRATOR_COPY.newGroup.namePlaceholder}
          {...(onField('name') === undefined ? {} : { error: onField('name') })}
        />

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
          club={group.homeClub}
          ticked={sports}
          onToggle={(sport) => edited(setSports)(toggled(sports, sport))}
          refused={onField('sports')}
        />

        {/* Hidden from a screen reader while the sheet is up: one label on the button and on the
            sheet's act, so the first press reaches the button and the second the act. */}
        <View ref={saveButton} {...behindOverlay(asking)}>
          <Button
            label={unchanged ? COPY.saved : COPY.save}
            variant={unchanged ? 'settled' : 'primary'}
            size="xl"
            disabled={settings === undefined || unchanged}
            busy={save.isPending}
            busyLabel={COPY.saving}
            onPress={submit}
          />
        </View>

        {refused !== undefined && refused.field === undefined ? (
          <Note variant="coral" accessibilityRole="alert">
            {refused.words}
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
