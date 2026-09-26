/**
 * ***Start playing*'s first step — the Adult attestation**
 * ([#517](https://github.com/Raketa02/Raketa/issues/517),
 * [ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §4–§5).
 *
 * An account an Invitation opened runs a club's groups and has never been asked how old it is:
 * nothing about running groups asks, and the club typed the email, not the person. **Playing is
 * where the question is asked**, before anything player-side can be reached — so *Start playing*
 * is three steps, and this is the first: the attestation, then the naming, then the player setup.
 *
 * **Sign-up's box, sign-up's claim and sign-up's refusal** (`TickBox`, `ADULT_LABEL`,
 * `ADULT_ATTESTATION_MISSING`): an attestation, one boolean, never a date of birth and not age
 * verification (ADR-0124). Never ticked on arrival, and *Continue* is never disabled by it — the
 * press goes through, the form refuses, and says what is missing under the box.
 *
 * **Two ways here.** The administrator's You tab pushes it, and *back* returns there untouched —
 * starting to play is a choice. The entry gate redirects an account that holds no profile at all to
 * it (ADR-0185 §3), and then there is nothing behind it to go back to: no back is drawn, and **_Sign
 * out_ is drawn at the foot instead**, because signing in again must never be a dead end and a person
 * who does not want to play has no other screen with a way out.
 *
 * **On success it hands the next step to the gate**, as the naming does: the act writes *acts as a
 * player* into the cached player and awaits a fresh read of it, then the screen replaces itself
 * with `/`. The gate then reads an account that plays and is not named in full, and sends it to the
 * naming — which asks only for the nickname, because the club gave the name.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, ScreenHeader, TickBox, theme } from '@/shared/ui';

import { useAttestAdult, useSignOut } from '../hooks/useAuthActions';
import {
  ADULT_LABEL,
  adultAttestationSchema,
  validate,
  type FieldErrors,
} from '../schemas/authForms';

import { SIGN_OUT } from './accountPresentation';
import { AuthLink } from './AuthLink';
import { AuthNotice } from './AuthNotice';
import { authErrorMessage, bannerMessage, errorUnderField } from './authErrorMessage';
import {
  START_PLAYING_CONTINUE,
  START_PLAYING_EYEBROW,
  START_PLAYING_NEXT,
  START_PLAYING_SUBLINE,
  START_PLAYING_TITLE,
} from './startPlayingPresentation';

export function StartPlayingScreen() {
  const router = useRouter();
  // Read once, as the screen opens: pushed from the You tab there is somewhere to go back to, and
  // redirected to by the gate there is not.
  const [pushed] = useState(() => router.canGoBack());
  const signOut = useSignOut();
  /** **False on arrival** — a box that arrives ticked is a claim the player never made. */
  const [adultAttested, setAdultAttested] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const attest = useAttestAdult();

  const submit = () => {
    const result = validate(adultAttestationSchema, { adultAttested });
    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }
    setFieldErrors({});
    attest.mutate(undefined, { onSuccess: () => router.replace('/') });
  };

  const banner =
    bannerMessage(attest.error) ??
    (signOut.error === null ? undefined : authErrorMessage(signOut.error));

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <ScreenHeader
        eyebrow={START_PLAYING_EYEBROW}
        title={START_PLAYING_TITLE}
        subline={START_PLAYING_SUBLINE}
        {...(pushed ? { onBack: () => router.back() } : {})}
      />

      <ScrollView contentContainerStyle={s.content}>
        {banner === undefined ? null : <AuthNotice message={banner} />}

        <TickBox
          label={ADULT_LABEL}
          checked={adultAttested}
          onChange={setAdultAttested}
          error={errorUnderField('adultAttested', fieldErrors, attest.error)}
          disabled={attest.isPending}
        />
        <Text style={s.next}>{START_PLAYING_NEXT}</Text>
      </ScrollView>

      <View style={s.action}>
        <Button
          label={START_PLAYING_CONTINUE.label}
          size="lg"
          busyLabel={START_PLAYING_CONTINUE.busyLabel}
          busy={attest.isPending}
          onPress={submit}
          accessibilityHint={START_PLAYING_CONTINUE.hint}
        />
        {pushed ? null : (
          <AuthLink
            label={signOut.isPending ? SIGN_OUT.busyLabel : SIGN_OUT.label}
            onPress={() => signOut.mutate()}
          />
        )}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.md,
  },
  next: { ...theme.type.tiny, color: theme.color.muted },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
    gap: theme.space.md,
  },
});
