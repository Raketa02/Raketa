/**
 * **State A — the numbered setup checklist** (mocks 41–45; the screens A7.3; design system 7.23).
 *
 * One card, four steps, one open at a time: the open step shows its number on `ink` and its
 * controls under the title; a finished step collapses to a green tick — step 1 keeping the way of
 * paying on the right, and pressable, to choose again; the steps still ahead are grey. **A wallet's
 * card details are not a finished step** — the wallet holds the card — so step 2 is drawn with a
 * dash and says where the card is.
 *
 * What each press does, and when step 4 asks the bank by itself, is `usePaymentSetup`'s; this draws
 * it. A failure is said inside the open step, because that is where the player is looking and where
 * the next press is.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { codeMessage } from '@/shared/errors';
import { usePayments } from '@/shared/lib/platform';
import { Button, Card, Chip, Dash, Note, Tick, theme } from '@/shared/ui';

import type { SetupStep, SetupStepName } from '../domain/setupSteps';
import { isWallet } from '../domain/vocabulary';
import type { PaymentSetup, SetupFailure } from '../hooks/usePaymentSetup';

import {
  PAYMENTS_COPY,
  PAYMENT_TERMS,
  PAYMENT_TERMS_TEXT,
  PAY_WITH_NAME,
  STEP_TITLE,
  inTheWallet,
  stepLabel,
} from './paymentsCopy';

export interface SetupChecklistProps {
  readonly setup: PaymentSetup;
}

export function SetupChecklist({ setup }: SetupChecklistProps) {
  return (
    <Card style={s.card}>
      {setup.steps.map((step, index) => (
        <View key={step.name} style={index > 0 ? s.divided : undefined}>
          <StepHead step={step} setup={setup} />
          {step.state === 'open' ? (
            <View style={s.body}>
              <StepBody name={step.name} setup={setup} />
              {setup.failure === null ? null : (
                <Note variant="coral" accessibilityRole="alert">
                  {failureLine(setup.failure)}
                </Note>
              )}
            </View>
          ) : null}
        </View>
      ))}
    </Card>
  );
}

/**
 * Whether this is a finished step 1 — the one head that is pressable (choose again) and that keeps
 * the answer on its right.
 */
function isAnsweredChoice(step: SetupStep): boolean {
  return step.name === 'choose' && step.state === 'done';
}

/** What the step says on its right once it is behind the player — step 1's answer, step 2's wallet. */
function asideOf(step: SetupStep, setup: PaymentSetup): string | undefined {
  const chosen = setup.chosen;
  if (chosen === null) return undefined;
  if (isAnsweredChoice(step)) return PAY_WITH_NAME[chosen];
  if (step.name === 'card' && step.state === 'skipped' && isWallet(chosen)) {
    return inTheWallet(chosen);
  }
  return undefined;
}

function StepHead({ step, setup }: { readonly step: SetupStep; readonly setup: PaymentSetup }) {
  const aside = asideOf(step, setup);
  const label = stepLabel(step, aside);
  const ahead = step.state === 'waiting' || step.state === 'skipped';

  const head = (
    <View style={s.head}>
      <StepMark step={step} />
      <Text style={[s.title, ahead ? s.titleAhead : undefined]}>{STEP_TITLE[step.name]}</Text>
      {aside === undefined ? null : <Text style={s.aside}>{aside}</Text>}
    </View>
  );

  if (isAnsweredChoice(step)) {
    return (
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={label}
        accessibilityHint={PAYMENTS_COPY.chooseAgain}
        disabled={setup.busy !== null}
        onPress={setup.reopen}
        hitSlop={theme.hit.btn}
        style={({ pressed }) => (pressed ? s.pressed : undefined)}
      >
        {head}
      </Pressable>
    );
  }

  return (
    <View accessible accessibilityRole="header" accessibilityLabel={label}>
      {head}
    </View>
  );
}

function StepMark({ step }: { readonly step: SetupStep }) {
  switch (step.state) {
    case 'done':
      return (
        <View style={[s.mark, s.markDone]}>
          <Tick />
        </View>
      );
    case 'skipped':
      return (
        <View style={[s.mark, s.markAhead]}>
          <Dash />
        </View>
      );
    case 'open':
      return (
        <View style={[s.mark, s.markOpen]}>
          <Text style={s.markNumberOpen}>{step.number}</Text>
        </View>
      );
    case 'waiting':
      return (
        <View style={[s.mark, s.markAhead]}>
          <Text style={s.markNumberAhead}>{step.number}</Text>
        </View>
      );
  }
}

function StepBody({ name, setup }: { readonly name: SetupStepName; readonly setup: PaymentSetup }) {
  const { CardFields } = usePayments();

  switch (name) {
    case 'choose':
      return (
        <>
          <View style={s.chips}>
            {setup.offered.map((payWith) => (
              <Chip
                key={payWith}
                label={PAY_WITH_NAME[payWith]}
                selected={setup.chosen === payWith}
                disabled={setup.busy !== null}
                onPress={() => setup.choose(payWith)}
              />
            ))}
          </View>
          {setup.chosen === 'BLIK' ? <Text style={s.line}>{PAYMENTS_COPY.blikNotice}</Text> : null}
          <Button
            label={PAYMENTS_COPY.continue}
            variant="dark"
            disabled={!setup.canContinue}
            busy={setup.busy === 'opening'}
            busyLabel={PAYMENTS_COPY.opening}
            onPress={setup.continueOn}
            style={s.action}
          />
        </>
      );

    case 'card':
      return (
        <>
          <CardFields
            onChange={setup.cardChanged}
            placeholders={PAYMENTS_COPY.cardFields.placeholders}
            accessibilityLabel={PAYMENTS_COPY.cardFields.label}
          />
          <Button
            label={PAYMENTS_COPY.saveTheCard}
            variant="dark"
            disabled={!setup.cardComplete}
            busy={setup.busy === 'taking'}
            busyLabel={PAYMENTS_COPY.saving}
            onPress={setup.saveCard}
            style={s.action}
          />
        </>
      );

    case 'terms':
      return (
        <>
          {/* Said before the press, not after it: the setup already named the terms in force. */}
          {setup.wordsInForce || setup.failure?.kind === 'TERMS_OUTDATED' ? null : (
            <Note variant="coral" accessibilityRole="alert">
              {PAYMENTS_COPY.failures.TERMS_OUTDATED}
            </Note>
          )}
          <Text style={s.line} accessibilityLabel={PAYMENT_TERMS_TEXT}>
            {PAYMENT_TERMS.map((run) => (
              <Text key={run.text} style={run.strong === true ? s.strong : undefined}>
                {run.text}
              </Text>
            ))}
          </Text>
          <Button
            label={PAYMENTS_COPY.accept}
            disabled={!setup.wordsInForce}
            busy={setup.busy === 'accepting'}
            busyLabel={PAYMENTS_COPY.accepting}
            onPress={setup.acceptTheTerms}
            style={s.action}
          />
        </>
      );

    case 'bank':
      return (
        <>
          <Text style={s.line}>{PAYMENTS_COPY.bankLine}</Text>
          <Button
            label={PAYMENTS_COPY.askTheBank}
            variant="dark"
            busy={setup.busy === 'asking'}
            busyLabel={PAYMENTS_COPY.asking}
            onPress={setup.askTheBank}
            style={s.action}
          />
        </>
      );
  }
}

function failureLine(failure: SetupFailure): string {
  return failure.kind === 'SAY_SO'
    ? codeMessage(PAYMENTS_COPY.refusals, failure.error)
    : PAYMENTS_COPY.failures[failure.kind];
}

const s = StyleSheet.create({
  card: { paddingVertical: theme.space.xs },
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  head: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.md,
    paddingVertical: theme.space.md,
  },
  pressed: { opacity: 0.7 },
  mark: {
    width: theme.size.payments.stepMark,
    height: theme.size.payments.stepMark,
    borderRadius: theme.radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markOpen: { backgroundColor: theme.color.ink },
  markDone: { backgroundColor: theme.color.mintInk },
  markAhead: { backgroundColor: theme.color.paper2 },
  markNumberOpen: { ...theme.type.cardTitle, color: theme.color.surface },
  markNumberAhead: { ...theme.type.cardTitle, color: theme.color.muted },
  title: { ...theme.type.question, color: theme.color.ink, flex: 1 },
  titleAhead: { color: theme.color.muted },
  aside: { ...theme.type.rlLabel, color: theme.color.muted },
  // The body sits under the title, indented past the mark as the mocks draw it.
  body: {
    gap: theme.space.md,
    paddingBottom: theme.space.lg,
    paddingLeft: theme.size.payments.stepMark + theme.space.md,
  },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
  line: { ...theme.type.rlLabel, color: theme.color.muted },
  strong: { fontFamily: theme.font.sans[700], color: theme.color.ink },
  action: { alignSelf: 'flex-start' },
});
