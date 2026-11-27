/**
 * **You › Account › Notifications** — the notices that are always on, and the three a player
 * chooses, saved as they tap ([#559](https://github.com/Raketa02/Raketa/issues/559); the screens
 * A7.2; mocks 52, 53; the mechanics §17.2).
 *
 * ```
 * ‹ Notifications
 * [ Your phone doesn't show Rakieta's notifications yet …   (Allow notifications) ]   while it may not
 * ALWAYS ON
 * ┌ It's a game! · held                             (on) ┐   inert rows, the green tag
 * │ …                                                    │
 * └──────────────────────────────────────────────────────┘
 * YOUR CHOICE
 * ┌ You complete it                                 (On) ┐   a working On / Off chip
 * │ A card needs only you · at most 1 a day, bundled     │
 * │ …                                                    │
 * └──────────────────────────────────────────────────────┘
 * ```
 *
 * ## Asking is the line at the top, and only there
 *
 * **While the phone may not show a notice, a line at the top offers *Allow notifications*** (A7.2) —
 * the moment the player understands why, never a wall at launch (`docs/architecture.md` Part 13).
 * Pressed, the OS asks; a yes registers the phone at once (`usePushRegistration`, which reads the
 * same answer). Once the phone answers *never again* only its settings can change that, so the line
 * offers them instead — and the answer is read again on the way back. It is offered every time the
 * screen opens while the answer is missing, not only the first: it is the one way back to pushes.
 *
 * ## Every tap is a save
 *
 * No *Save* button, as Games & money: a tap turns the chip at once and sends all three
 * (`useSaveNotificationChoices`); a refusal says so under the cards and the three are read again.
 * The ones always on are not controls — a row and a tag, never pressable (6.4).
 */

import { useRouter } from 'expo-router';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { openAppSettings, type PermissionState } from '@/shared/lib/platform';
import { Button, Card, Note, Tag, theme } from '@/shared/ui';

import { CHOICES, type ChoiceKey, type NotificationChoices } from '../domain/choices';
import {
  useNotificationChoices,
  useSaveNotificationChoices,
} from '../hooks/useNotificationChoices';
import { useAllowNotifications, usePushPermission } from '../hooks/usePushPermission';

import {
  NOTIFICATIONS_COPY,
  NOTIFICATIONS_TITLE,
  alwaysOnSpoken,
  choiceSpoken,
} from './notificationsCopy';
import { ReadState } from './ReadState';

const COPY = NOTIFICATIONS_COPY;

export function NotificationsScreen() {
  const router = useRouter();
  const read = useNotificationChoices();
  const { toggle, error, heldOffline } = useSaveNotificationChoices();
  const held = read.data;

  return (
    <ShellScreen eyebrow={YOU_COPY.groups.account} title={NOTIFICATIONS_TITLE} onBack={router.back}>
      <View style={s.column}>
        <PermissionLine />

        <Section title={COPY.alwaysOn.title}>
          <Card style={s.rows}>
            {COPY.alwaysOn.rows.map((row, index) => (
              <View
                key={row}
                accessible
                accessibilityLabel={alwaysOnSpoken(row)}
                style={[s.row, index > 0 ? s.divided : undefined]}
              >
                <Text style={s.always}>{row}</Text>
                <Tag label={COPY.alwaysOn.tag} variant="ok" />
              </View>
            ))}
          </Card>
        </Section>

        <Section title={COPY.yourChoice.title}>
          {held === undefined ? (
            <ReadState read={read} loading={COPY.loading} />
          ) : (
            <Choices held={held} onToggle={toggle} />
          )}
        </Section>

        {heldOffline ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}
        {error === null ? null : (
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(error)}
          </Note>
        )}
      </View>
    </ShellScreen>
  );
}

/** A titled section — Payments' head over one card, the mocks' grey capitals. */
function Section({ title, children }: { readonly title: string; readonly children: ReactNode }) {
  return (
    <View style={s.section}>
      <Text accessibilityRole="header" style={s.head}>
        {title}
      </Text>
      {children}
    </View>
  );
}

function Choices({
  held,
  onToggle,
}: {
  readonly held: NotificationChoices;
  readonly onToggle: (key: ChoiceKey) => void;
}) {
  return (
    <Card style={s.rows}>
      {CHOICES.map((key, index) => (
        <View key={key} style={[s.row, index > 0 ? s.divided : undefined]}>
          <View style={s.words}>
            <Text style={s.title}>{COPY.yourChoice.rows[key].title}</Text>
            <Text style={s.line}>{COPY.yourChoice.rows[key].line}</Text>
          </View>
          <OnOffChip on={held[key]} label={choiceSpoken(key)} onPress={() => onToggle(key)} />
        </View>
      ))}
    </Card>
  );
}

/**
 * **The on/off chip** (A10's new component; mock 53) — 6.2's pill, ink-filled with *On* and outlined
 * with *Off*. Spoken as the switch it is: the choice's name, its role and whether it is on — the
 * word drawn is the state, so a listener is told the state and never a bare *On*.
 */
function OnOffChip({
  on,
  label,
  onPress,
}: {
  readonly on: boolean;
  readonly label: string;
  readonly onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="switch"
      accessibilityLabel={label}
      accessibilityState={{ checked: on }}
      onPress={onPress}
      hitSlop={theme.hit.chip}
      style={({ pressed }) => [s.chip, on ? s.chipOn : undefined, pressed ? s.pressed : undefined]}
    >
      <Text style={[s.chipLabel, on ? s.chipLabelOn : undefined]}>
        {on ? COPY.yourChoice.on : COPY.yourChoice.off}
      </Text>
    </Pressable>
  );
}

/** The line at the top while the phone may not show a notice — see the module note. */
function PermissionLine() {
  const permission = usePushPermission();
  const allow = useAllowNotifications();
  const state: PermissionState | undefined = permission.data;

  if (state === undefined || state === 'granted') return null;
  const blocked = state === 'blocked';
  const words = blocked ? COPY.permission.blocked : COPY.permission.ask;

  return (
    <Card style={s.permission}>
      <Text style={s.permissionLine}>{words.line}</Text>
      <Button
        label={words.button}
        variant="primary"
        size="sm"
        busy={allow.isPending}
        busyLabel={COPY.permission.ask.busy}
        onPress={() => (blocked ? openAppSettings() : allow.mutate())}
      />
    </Card>
  );
}

const s = StyleSheet.create({
  column: { gap: theme.space.sm },
  section: { gap: theme.space.xs, paddingTop: theme.space.xs },
  head: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  // The rows carry their own padding, so the card's is a step smaller (Payments' sections').
  rows: { paddingVertical: theme.space.xxs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.md,
    paddingVertical: theme.space.sm,
  },
  // 5.5: the fold from the second row on.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  always: { ...theme.type.rlLabel, color: theme.color.ink, flex: 1 },
  words: { flex: 1, gap: theme.space.xxs },
  title: { ...theme.type.question, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  permission: { gap: theme.space.sm },
  permissionLine: { ...theme.type.rlLabel, color: theme.color.ink },
  // 6.2's pill — the chip's own metrics, drawn here for a switch's role (see `OnOffChip`).
  chip: {
    minHeight: theme.size.chip,
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.xxs,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chipOn: { backgroundColor: theme.color.ink, borderColor: theme.color.ink },
  pressed: { opacity: 0.7 },
  chipLabel: { ...theme.type.chip, color: theme.color.ink },
  chipLabelOn: { color: theme.color.surface },
});
