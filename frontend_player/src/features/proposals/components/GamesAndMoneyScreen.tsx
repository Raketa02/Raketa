/**
 * **You › Account › Games & money** — the two limits that bound what every deck deals, saved as
 * the player taps ([#554](https://github.com/Rakieta02/Rakieta/issues/554); the screens A7.1; mocks
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

import { useRouter } from 'expo-router';
import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

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
import { Stepper } from './Stepper';

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
            figure={String(held.gamesPerWeek)}
            fewer={{
              glyph: 'minus',
              label: COPY.games.fewer,
              value: gamesSpoken(held.gamesPerWeek),
              onPress: canStep(held, -1) ? () => step(-1) : undefined,
            }}
            more={{
              glyph: 'plus',
              label: COPY.games.more,
              value: gamesSpoken(held.gamesPerWeek),
              onPress: canStep(held, 1) ? () => step(1) : undefined,
            }}
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
});
