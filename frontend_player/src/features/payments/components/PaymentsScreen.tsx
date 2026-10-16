/**
 * **You › Account › Payments** — the four-step setup, or the saved method
 * ([#552](https://github.com/Raketa02/Raketa/issues/552); the screens A7.3; mocks 41–47; the
 * mechanics §12.4, §12.5).
 *
 * ## Two states, one read
 *
 * `GET …/current` decides: **nothing saved is state A**, the numbered checklist; **a saved method is
 * state B**, the dark method card with *Change* and, under it, *Remove this method*. A save writes
 * the server's answer into that read, so the screen turns from A to B the moment the bank's answer
 * is read back — nobody navigates anywhere.
 *
 * ## Change keeps the old method working
 *
 * *Change* opens the checklist under a line saying the method on file still pays until the new one
 * is saved (Q83) — nothing is removed first, and the server replaces it only on the new one's
 * confirmation. *Keep this one* closes the checklist again; a setup it opened stays at the provider
 * until a newer one replaces it, where it can charge nothing.
 *
 * ## Remove is refused while anything needs the method
 *
 * The server knows what still needs it — a live yes, a booked game ahead — and refuses with the
 * counts; the screen says so under the link (Q83). It is not asked first, because the one fact that
 * decides it is the server's.
 *
 * ## When the bank moved the card to another brand
 *
 * The read's `terms_needed`: clubs cannot charge the card until the terms are accepted again, and
 * the terms were accepted for a brand (the mechanics §12.5). The card says so, shows the terms, and
 * one press accepts them — there is no setup and nothing for the bank to confirm.
 *
 * ## Live yeses are handed in
 *
 * State B's *LIVE YESES* (mock 48, #554) are the proposals feature's — the deck's answers, whose
 * details are the deck's screen — so the route file composes them and this screen only places
 * them, under the method. They are drawn in state B alone: a yes needs a saved method, and a
 * method is not removed while a yes needs it.
 *
 * *TO CONFIRM* (#555) is placed the same way, above them: a share refused when somebody else's
 * yes filled the game, waiting for the player — the proposals feature's read, and its fill's
 * confirmation.
 *
 * ## Receipts close state B
 *
 * *RECEIPTS* (mock 49, #555) are this feature's own read — every share paid, the club named as the
 * seller — drawn last, under the live yeses. State B alone, as the screens draw it: a receipt is
 * only ever for a game a saved method paid for.
 */

import { useRouter } from 'expo-router';
import { useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { codeMessage, recoveryMessage, type AppError } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import type { SavedMethod } from '../domain/vocabulary';
import {
  useAcceptTermsAgain,
  usePaymentMethod,
  useRemovePaymentMethod,
} from '../hooks/usePaymentMethod';
import { usePaymentSetup } from '../hooks/usePaymentSetup';

import { MethodCard } from './MethodCard';
import { Receipts } from './Receipts';
import {
  PAYMENTS_COPY,
  PAYMENTS_TITLE,
  PAYMENT_TERMS_TEXT,
  PAYMENT_TERMS_VERSION,
  inUseLine,
  keepsWorkingLine,
} from './paymentsCopy';
import { SetupChecklist } from './SetupChecklist';

export interface PaymentsScreenProps {
  /** State B's *TO CONFIRM* section, drawn first under the method — see the module note. */
  readonly toConfirm?: ReactNode;
  /** State B's *LIVE YESES* section, drawn under the method — see the module note. */
  readonly liveYeses?: ReactNode;
}

export function PaymentsScreen({ toConfirm, liveYeses }: PaymentsScreenProps) {
  const router = useRouter();
  const read = usePaymentMethod();
  /** *Change* pressed on state B: the checklist over the method still on file. */
  const [changing, setChanging] = useState(false);

  const standing = read.data;

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.account}
      title={PAYMENTS_TITLE}
      onBack={router.back}
      keepsKeyboardOnTap>
      {standing === undefined ? (
        <ReadStanding
          pending={read.isPending}
          error={read.error}
          onRetry={() => void read.refetch()}
        />
      ) : standing.method === null ? (
        <Setup onSaved={() => setChanging(false)} />
      ) : changing ? (
        <View style={s.column}>
          <Text style={s.line}>{keepsWorkingLine(standing.method)}</Text>
          <Setup onSaved={() => setChanging(false)} />
          <TextLink label={PAYMENTS_COPY.method.keep} onPress={() => setChanging(false)} />
        </View>
      ) : (
        <>
          <Saved
            method={standing.method}
            termsNeeded={standing.termsNeeded}
            onChange={() => setChanging(true)}
          />
          {toConfirm}
          {liveYeses}
          <Receipts />
        </>
      )}
    </ShellScreen>
  );
}

function Setup({ onSaved }: { readonly onSaved: () => void }) {
  const setup = usePaymentSetup({
    termsVersion: PAYMENT_TERMS_VERSION,
    walletSheetLabel: PAYMENTS_COPY.walletSheet,
    onSaved,
  });
  return <SetupChecklist setup={setup} />;
}

function Saved({
  method,
  termsNeeded,
  onChange,
}: {
  readonly method: SavedMethod;
  readonly termsNeeded: boolean;
  readonly onChange: () => void;
}) {
  const removal = useRemovePaymentMethod();

  return (
    <View style={s.column}>
      <MethodCard method={method} onChange={onChange} />
      {termsNeeded ? <TermsAgain /> : null}
      <View style={s.remove}>
        <TextLink
          label={removal.isPending ? PAYMENTS_COPY.method.removing : PAYMENTS_COPY.method.remove}
          disabled={removal.isPending}
          onPress={removal.remove}
        />
        {removal.refusal === null || removal.refusal.kind === 'GONE' ? null : (
          <Note variant="amber" accessibilityRole="alert">
            {removal.refusal.kind === 'IN_USE'
              ? inUseLine(removal.refusal.counts)
              : recoveryMessage(removal.refusal.error)}
          </Note>
        )}
      </View>
    </View>
  );
}

/** The bank moved the card to another brand: the terms again, and one press. */
function TermsAgain() {
  const accept = useAcceptTermsAgain();

  return (
    <View style={s.column}>
      <Note variant="amber" title={PAYMENTS_COPY.method.termsAgainTitle}>
        {PAYMENTS_COPY.method.termsAgainLine}
      </Note>
      <Text style={s.line}>{PAYMENT_TERMS_TEXT}</Text>
      {accept.error === null ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {codeMessage(PAYMENTS_COPY.refusals, accept.error)}
        </Note>
      )}
      <Button
        label={PAYMENTS_COPY.method.termsAgain}
        busy={accept.isPending}
        busyLabel={PAYMENTS_COPY.accepting}
        onPress={() => accept.mutate(PAYMENT_TERMS_VERSION)}
        style={s.action}
      />
    </View>
  );
}

function ReadStanding({
  pending,
  error,
  onRetry,
}: {
  readonly pending: boolean;
  readonly error: AppError | null;
  readonly onRetry: () => void;
}) {
  if (error !== null && !pending) {
    return (
      <View style={s.column}>
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(error)}
        </Note>
        <TextLink label={PAYMENTS_COPY.readAgain} onPress={onRetry} />
      </View>
    );
  }
  return <Text style={s.line}>{PAYMENTS_COPY.loading}</Text>;
}

/** A small link under a card — *Remove this method*, *Keep this one*. */
function TextLink({
  label,
  onPress,
  disabled = false,
}: {
  readonly label: string;
  readonly onPress: () => void;
  readonly disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [s.link, pressed ? s.pressed : undefined]}
    >
      <Text style={s.linkWords}>{label}</Text>
    </Pressable>
  );
}

const s = StyleSheet.create({
  column: { gap: theme.space.md },
  line: { ...theme.type.rlLabel, color: theme.color.muted },
  remove: { gap: theme.space.sm, alignItems: 'center' },
  link: { alignSelf: 'center', paddingVertical: theme.space.xs },
  linkWords: { ...theme.type.rlValue, color: theme.color.muted, textDecorationLine: 'underline' },
  pressed: { opacity: 0.7 },
  action: { alignSelf: 'flex-start' },
});
