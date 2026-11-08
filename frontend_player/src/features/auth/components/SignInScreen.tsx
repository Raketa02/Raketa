/**
 * Sign in.
 *
 * The screen owns rendering and interaction. It owns no rule: what a valid email looks like is
 * `schemas/`, what signing in does is `use-cases/`, and what a failure means is the error model. A
 * `disabled={…}` expression encoding a rule would be a rule nobody can test.
 *
 * **It is drawn on the stage** ([#784](https://github.com/Raketa02/Raketa/issues/784), PRD #783):
 * the dark hero with the wordmark and *Your next game is only one swipe away.*, and the paper sheet
 * over it holding the form, restyled to mocks 1 and 3. **Nothing it does changed**: every control
 * keeps its target and what it carries, the refusals keep their sentences and sources, and **Sign
 * in** still fires on the button and on the keyboard's Go.
 *
 * **Top to bottom**: the title; the server's banner when there is one (a refusal about the whole
 * form, above the whole form); *Email*, empty with *you@example.com* as its placeholder so the
 * keychain's autofill still offers the saved address; *Password*, with **Show** and **Hide** inside the
 * box; ***Forgot password?***, quiet and right-aligned under the box it is about; **Sign in**; the
 * *or* rule; ***I have an invitation code***, the outlined way in a club's invitation opens; and *New
 * to Raketa? Create an account* at the sheet's foot.
 *
 * **The boxes and buttons are the mock's, not the app's**: both boxes in the shared field's `stage`
 * look (a grey sentence-case label, a 48pt box, a 14pt value, a sentence-case *Show*) and both
 * buttons at its `stage` height, 6.13 and 6.1 as amended. Every other field in the app keeps 6.13's.
 *
 * **A box's own refusal is drawn on its label's row** (`errorOnLabelRow`, 6.13 as amended), so the
 * form does not shift down a line under somebody who pressed too early.
 *
 * **The password box can be read back**, exactly as both of the sign-up form's can. The argument
 * there was a typo nobody can see costing a player the whole form; here it is a typo nobody can see
 * costing them a refusal they cannot distinguish from a wrong password — and a keychain that filled
 * the box with the wrong entry looks identical either way.
 *
 * ***Forgot password?*** ([#515](https://github.com/Raketa02/Raketa/issues/515)) and ***I have an
 * invitation code*** ([#518](https://github.com/Raketa02/Raketa/issues/518)) each carry what is in
 * the email box across, so it is not typed twice, on the one sign-in screen players and
 * administrators share.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import { Button, TextField } from '@/shared/ui';

import { useSignIn } from '../hooks/useAuthActions';
import { signInSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthFields } from './AuthFrame';
import { AuthLink } from './AuthLink';
import { AuthNotice } from './AuthNotice';
import { AuthStage } from './AuthStage';
import { EMAIL_PLACEHOLDER, PASSWORD_LABEL, SIGN_IN_COPY } from './authPresentation';
import { authErrorMessage } from './authErrorMessage';
import { EmailField } from './EmailField';
import { INVITATION_COPY } from './invitationPresentation';
import { invitationCodeHref } from './invitationRoutes';
import { OrRule } from './OrRule';
import { RESET_COPY } from './resetPresentation';
import { askForResetHref } from './resetRoutes';
import { StageDeck } from './StageDeck';
import { StageSplash } from './StageSplash';
import { useStageLoop } from './useStageLoop';

export interface SignInScreenProps {
  /**
   * Whether sign-in is the screen in view — the route reads it off the navigator
   * (`useScreenInView`). A screen drawn on its own, as the suites draw it, is.
   */
  readonly inView?: boolean;
}

export function SignInScreen({ inView = true }: SignInScreenProps) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const signIn = useSignIn();
  // The hero's story — while sign-in is in view and the app not in the background, never under
  // collapsed presentation. Nothing in it is the form's, and nothing the form does reaches it.
  const loop = useStageLoop(inView);

  const submit = () => {
    const result = validate(signInSchema, { email, password });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    signIn.mutate(result.values);
  };

  const forgotPassword = () => router.push(askForResetHref(email));
  const haveACode = () => router.push(invitationCodeHref(email));

  return (
    <AuthStage
      title={SIGN_IN_COPY.title}
      headline={SIGN_IN_COPY.headline}
      picture={<StageDeck {...loop.deck} />}
      cover={loop.splash === undefined ? undefined : <StageSplash {...loop.splash} />}
      inView={inView}
      footer={
        <AuthLink lead={SIGN_IN_COPY.newHere} label={SIGN_IN_COPY.createAccount} href="/sign-up" />
      }
    >
      {signIn.error !== null ? <AuthNotice message={authErrorMessage(signIn.error)} /> : null}

      <AuthFields>
        <EmailField
          value={email}
          onChangeText={setEmail}
          error={fieldErrors.email}
          errorOnLabelRow
          stage
          placeholder={EMAIL_PLACEHOLDER}
          returnKeyType="next"
          editable={!signIn.isPending}
        />
        {/* The quiet link sits straight under the box it is about, with no gap of the form's. */}
        <View>
          <TextField
            label={PASSWORD_LABEL}
            value={password}
            onChangeText={setPassword}
            error={fieldErrors.password}
            errorOnLabelRow
            stage
            secureTextEntry
            reveal
            autoCapitalize="none"
            autoComplete="current-password"
            textContentType="password"
            returnKeyType="go"
            onSubmitEditing={submit}
            editable={!signIn.isPending}
          />
          <AuthLink label={RESET_COPY.signInLink} onPress={forgotPassword} quiet />
        </View>
      </AuthFields>

      <Button
        label={SIGN_IN_COPY.submit}
        size="stage"
        busyLabel={SIGN_IN_COPY.submitting}
        busy={signIn.isPending}
        onPress={submit}
      />

      <OrRule word={SIGN_IN_COPY.or} />

      {/* A link in what it does — it opens a screen carrying the email — and 6.1 `secondary` in look,
          with the product owner's coral dot (6.1 and 1.2 as amended, Part 16 2026-11-08). */}
      <Button
        label={INVITATION_COPY.signInLink}
        variant="secondary"
        size="stage"
        role="link"
        dot
        onPress={haveACode}
      />
    </AuthStage>
  );
}
