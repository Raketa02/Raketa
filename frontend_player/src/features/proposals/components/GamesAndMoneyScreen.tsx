/**
 * **You › Account › Games & money** — the two limits that bound what every deck deals, saved as
 * the player taps ([#554](https://github.com/Raketa02/Raketa/issues/554); the screens A7.1; mocks
 * 38, 39; the mechanics §6.6).
 *
 * ```
 * ‹ Games & money
 * ┌ Games per week                 ┌───────────┐ ┐
 * │ Mon–Sun · 1 to 7               │ −   4   + │ │   the stepper, clamped to the server's range
 * │ ─────────────────────────────  └───────────┘ │
 * │ Once they are booked, your other yeses that week pause — …
 * └──────────────────────────────────────────────┘
 * ┌ Most I'll pay per game   (Off) (35 zł) (45 zł) (60 zł) ┐   6.2 chips, the one saved ink-filled
 * │ Off by default                                        │
 * │ ─────────────────────────────                         │
 * │ Every card is shown, whatever its share.              │
 * └───────────────────────────────────────────────────────┘
 *          Your bound: at most 4 games a week.
 * ```
 *
 * ## Every tap is a save
 *
 * No *Save* button (A7.1): a press moves the value at once and sends both limits
 * (`useSaveGamesAndMoney`, which writes the pair into the read, runs the saves in the order they
 * were tapped, and lets only the last one's answer stand). The stepper's button at an end of the
 * range is shut, since a press there would move nothing. A refused save says why under the bound,
 * where a note appearing does not move the control the finger is on, and the pair is read again.
 *
 * ## Nothing here holds a range
 *
 * The stepper's least and most, and the ceilings offered beside *Off*, are the read's — the server
 * says what the form offers, so it can offer more without a release.
 */

import Feather from '@expo/vector-icons/Feather';
import { useRouter } from 'expo-router';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { codeMessage, offlineMessage } from '@/shared/errors';
import { Card, Chip, Hairline, Note, theme } from '@/shared/ui';

import {
  canStep,
  limitsOf,
  steppedGames,
  withCeiling,
  withGames,
  type GamesAndMoney,
  type Limits,
  type Step,
} from '../domain/gamesAndMoney';
import { useGamesAndMoney, useSaveGamesAndMoney } from '../hooks/useGamesAndMoney';

import {
  GAMES_AND_MONEY_COPY,
  GAMES_AND_MONEY_TITLE,
  boundRuns,
  boundText,
  ceilingChipLabel,
  ceilingLine,
  gamesLine,
  gamesSpoken,
  rangeLine,
} from './gamesAndMoneyCopy';
import { ReadFailed } from './ReadFailed';

const COPY = GAMES_AND_MONEY_COPY;

export function GamesAndMoneyScreen() {
  const router = useRouter();
  const read = useGamesAndMoney();
  const { save, error, heldOffline } = useSaveGamesAndMoney();
  const held = read.data;

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.account}
      title={GAMES_AND_MONEY_TITLE}
      onBack={router.back}
    >
      {held === undefined ? (
        read.fetchStatus === 'paused' ? (
          <Note variant="amber">{offlineMessage('resumes')}</Note>
        ) : read.error !== null && !read.isFetching ? (
          <ReadFailed error={read.error} onRetry={() => void read.refetch()} />
        ) : (
          <Text style={s.line}>{COPY.loading}</Text>
        )
      ) : (
        <LimitsForm held={held} onSave={save}>
          {heldOffline ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}
          {error === null ? null : (
            <Note variant="coral" accessibilityRole="alert">
              {codeMessage(COPY.refused, error)}
            </Note>
          )}
        </LimitsForm>
      )}
    </ShellScreen>
  );
}

function LimitsForm({
  held,
  onSave,
  children,
}: {
  readonly held: GamesAndMoney;
  readonly onSave: (tap: (now: GamesAndMoney) => Limits) => void;
  /** The notes under the bound — offline, or a refusal. */
  readonly children: ReactNode;
}) {
  const limits = limitsOf(held);
  const step = (by: Step) => onSave((now) => limitsOf(withGames(now, steppedGames(now, by))));
  const choose = (grosze: number | null) => onSave((now) => limitsOf(withCeiling(now, grosze)));

  return (
    <View style={s.column}>
      <Card>
        <View style={s.head}>
          <View style={s.titles}>
            <Text style={s.title}>{COPY.games.title}</Text>
            <Text style={s.sub}>{rangeLine(held.gamesPerWeekRange)}</Text>
          </View>
          <Stepper
            value={held.gamesPerWeek}
            fewer={canStep(held, -1) ? () => step(-1) : undefined}
            more={canStep(held, 1) ? () => step(1) : undefined}
          />
        </View>
        <Hairline>
          <Text style={s.line}>{gamesLine(held.gamesPerWeek)}</Text>
        </Hairline>
      </Card>

      <Card>
        <View style={[s.head, s.wraps]}>
          <View style={s.titles}>
            <Text style={s.title}>{COPY.ceiling.title}</Text>
            <Text style={s.sub}>{COPY.ceiling.line}</Text>
          </View>
          <View style={s.chips}>
            {[null, ...held.ceilingChoicesGrosze].map((grosze) => (
              <Chip
                key={grosze ?? 'off'}
                label={ceilingChipLabel(grosze)}
                selected={held.mostIllPayGrosze === grosze}
                onPress={() => choose(grosze)}
              />
            ))}
          </View>
        </View>
        <Hairline>
          <Text style={s.line}>{ceilingLine(held.mostIllPayGrosze)}</Text>
        </Hairline>
      </Card>

      <Text style={s.bound} accessibilityLabel={boundText(limits)}>
        {boundRuns(limits).map((run) => (
          <Text key={run.text} style={run.strong === true ? s.strong : undefined}>
            {run.text}
          </Text>
        ))}
      </Text>

      {children}
    </View>
  );
}

/**
 * **− 4 +** — two keys either side of the figure, in one outlined box (mock 38). Each key is a
 * button named for what it does, carrying the value, so a listener hears the new count on the key
 * they just pressed; a key whose press would move nothing is shut (`undefined`).
 */
function Stepper({
  value,
  fewer,
  more,
}: {
  readonly value: number;
  readonly fewer: (() => void) | undefined;
  readonly more: (() => void) | undefined;
}) {
  return (
    <View style={s.stepper}>
      <StepKey glyph="minus" label={COPY.games.fewer} value={value} onPress={fewer} />
      <Text style={s.figure} accessibilityElementsHidden importantForAccessibility="no">
        {value}
      </Text>
      <StepKey glyph="plus" label={COPY.games.more} value={value} onPress={more} />
    </View>
  );
}

function StepKey({
  glyph,
  label,
  value,
  onPress,
}: {
  readonly glyph: 'minus' | 'plus';
  readonly label: string;
  readonly value: number;
  readonly onPress: (() => void) | undefined;
}) {
  const shut = onPress === undefined;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityValue={{ text: gamesSpoken(value) }}
      accessibilityState={{ disabled: shut }}
      disabled={shut}
      onPress={onPress}
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [s.key, shut ? s.shut : undefined, pressed ? s.pressed : undefined]}
    >
      <Feather
        name={glyph}
        size={theme.size.rowLeadGlyph}
        color={theme.color.ink}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </Pressable>
  );
}

const s = StyleSheet.create({
  column: { gap: theme.space.sm },
  head: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  // The chips drop under the title on a phone too narrow for both, rather than squeezing it.
  wraps: { flexWrap: 'wrap', rowGap: theme.space.sm },
  titles: { flexGrow: 1, flexShrink: 1, gap: theme.space.xxs },
  title: { ...theme.type.question, color: theme.color.ink },
  sub: { ...theme.type.tiny, color: theme.color.muted },
  line: { ...theme.type.rlLabel, color: theme.color.muted },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
  bound: { ...theme.type.rlLabel, color: theme.color.muted, textAlign: 'center' },
  strong: { fontFamily: theme.font.sans[700] },
  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: theme.space.xxs,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    backgroundColor: theme.color.surface,
  },
  // 6.5 by geometry across and by `hit.btn` up and down: 44 wide, 40 tall and 50 to the finger.
  key: {
    width: theme.size.minTouch,
    height: theme.size.btnLg,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.paper2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // 6.1's disabled: the key is there and shut, not gone — the end of the range is visible.
  shut: { opacity: 0.4 },
  pressed: { opacity: 0.7 },
  figure: {
    ...theme.num.xl,
    ...theme.tabular,
    minWidth: theme.size.btnLg,
    color: theme.color.ink,
    textAlign: 'center',
  },
});
