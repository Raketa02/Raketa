/**
 * Create an account — **credentials, and nothing about who you are.**
 *
 * Email, a password twice and the adult attestation. The nickname is not asked here
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3):
 * choosing credentials and saying who you are are two different moments, and the second
 * is onboarding's first screen — *How should people see you?* — which the entry gate sends
 * this new session straight into. A sign-up refused for a taken handle was a sign-up refused
 * for a reason that had nothing to do with the account.
 *
 * **It asks one question that is not about the account**: whether the player is an adult.
 * The platform is adults only and that is a precondition of holding an account rather than
 * a rule about who is shown to whom
 * ([ADR-0124](../../../../../docs/adr/0124-the-matcher-gates-account-state-never-age.md)),
 * so this form is where it is asked. What is collected is an **attestation** — one boolean,
 * never a date of birth, and **not age verification**. There is no date picker here and
 * this screen is not where the first one arrives.
 *
 * The box is never ticked on arrival, and the *Create account* button is never disabled by
 * it. A closed control is not a validation ([ADR-0089](../../../../../docs/adr/0089-player-profile-context-event-sourced.md)):
 * the press goes through, the form refuses, and it says what is missing under the box that
 * takes the answer. The same sentence renders when the server refuses the same thing by
 * code, because a body this form would not have sent can still arrive from an older build.
 *
 * A server-side conflict — the email is taken — carries the field it belongs to, so it is
 * rendered under that box rather than in the banner. A player told "that email already has
 * an account" above a three-field form still has to work out which box to change.
 *
 * **The two password boxes are `PasswordPairFields`**, *Set a new password*'s too
 * ([#515](https://github.com/Raketa02/Raketa/issues/515)): both can be read back, and the one
 * password rule — a letter and a digit as well as the length — is written under the first before
 * anything is typed. The frame, the email box and the link at the foot are the sign-in screen's
 * pieces, so this screen owns only what it asks.
 *
 * **It is drawn on the stage, sign-in's second page** ([#785](https://github.com/Raketa02/Raketa/issues/785),
 * PRD #783; mocks 4 and 6): the same dark hero with the wordmark where sign-in has it and *Play
 * ranked. The competition starts with you.* at its foot, and the paper sheet over it holding this
 * form. **Nothing it does changed**: the same request, the same refusals from the same sources, the
 * same box that never arrives ticked.
 *
 * **Top to bottom**: the title alone; the server's banner when there is one; *Email*, empty under
 * *you@example.com*; *Password* under *At least 8 characters*, with **Show** and the rule beneath it
 * **all the time**; *Repeat password* under *Once more*, with its own **Show**; *I am 18 or over*;
 * **Create account**; and *Already have an account? Sign in* at the sheet's foot. Every box is in the
 * shared field's `stage` look with its refusal on its label row, as sign-in's are, so a refusal
 * never pushes the rule out from under the box it describes.
 *
 * ***Sign in* goes back** to the sign-in underneath (`dismissTo`) rather than pushing a second one
 * over this — the two screens are one flow, and a stack of alternating stages would take as many
 * backs to leave as presses to build. Opened with nothing under it, from a link, it replaces this
 * screen with sign-in instead. The move each way is the stack's cross-fade (`(auth)/_layout`).
 *
 * **Its hero is the podium** ([#788](https://github.com/Raketa02/Raketa/issues/788), mock 5): You on
 * the first step, rising once when the screen opens (`StagePodium`, `usePodiumRise`) — a picture,
 * hidden from screen readers, that nothing on the form touches.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { Button, TickBox } from '@/shared/ui';

import { useSignUp } from '../hooks/useAuthActions';
import { ADULT_LABEL, signUpSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthFields } from './AuthFrame';
import { AuthLink } from './AuthLink';
import { AuthNotice } from './AuthNotice';
import { AuthStage } from './AuthStage';
import { EMAIL_PLACEHOLDER, PASSWORD_LABEL, SIGN_UP_COPY } from './authPresentation';
import { bannerMessage, errorUnderField } from './authErrorMessage';
import { EmailField } from './EmailField';
import { PasswordPairFields } from './PasswordPairFields';
import { StagePodium } from './StagePodium';
import { usePodiumRise } from './usePodiumRise';

export interface SignUpScreenProps {
  /**
   * Whether sign-up is the screen in view — the route reads it off the navigator
   * (`useScreenInView`), as sign-in's does. A screen drawn on its own, as the suites draw it, is.
   */
  readonly inView?: boolean;
}

export function SignUpScreen({ inView = true }: SignUpScreenProps) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  /**
   * **False on arrival, and there is no path that starts it anywhere else.** A pre-ticked
   * box is a claim the player never made, which is the one thing an attestation exists to
   * rule out (ADR-0124).
   */
  const [adultAttested, setAdultAttested] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const signUp = useSignUp();
  // The hero's podium, rising once as the screen opens — never under collapsed presentation.
  // Nothing in it is the form's, and nothing the form does reaches it.
  const podium = usePodiumRise();

  const submit = () => {
    const result = validate(signUpSchema, {
      email,
      password,
      confirmPassword,
      adultAttested,
    });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    signUp.mutate({
      email: result.values.email,
      password: result.values.password,
      adultAttested: result.values.adultAttested,
    });
  };

  // A conflict the server raised against one field belongs under that field. Anything
  // else stays in the banner.
  const errorFor = (field: string) => errorUnderField(field, fieldErrors, signUp.error);
  const banner = bannerMessage(signUp.error);

  return (
    <AuthStage
      title={SIGN_UP_COPY.title}
      headline={SIGN_UP_COPY.headline}
      picture={<StagePodium {...podium} />}
      inView={inView}
      footer={
        <AuthLink
          lead={SIGN_UP_COPY.haveAccount}
          label={SIGN_UP_COPY.signIn}
          onPress={() => router.dismissTo('/sign-in')}
        />
      }
    >
      {banner === undefined ? null : <AuthNotice message={banner} />}

      <AuthFields>
        <EmailField
          value={email}
          onChangeText={setEmail}
          error={errorFor('email')}
          errorOnLabelRow
          stage
          placeholder={EMAIL_PLACEHOLDER}
          textContentType="emailAddress"
          editable={!signUp.isPending}
        />
        <PasswordPairFields
          label={PASSWORD_LABEL}
          password={password}
          onChangePassword={setPassword}
          passwordError={errorFor('password')}
          repeat={confirmPassword}
          onChangeRepeat={setConfirmPassword}
          repeatError={errorFor('confirmPassword')}
          onSubmitEditing={submit}
          editable={!signUp.isPending}
          stage
        />

        {/* Below the three boxes and above the button, because it is the last thing a
            player agrees to rather than another detail about the account, and because
            a refusal has to be visible from the control that provoked it. */}
        <TickBox
          label={ADULT_LABEL}
          checked={adultAttested}
          onChange={setAdultAttested}
          error={errorFor('adultAttested')}
          disabled={signUp.isPending}
        />
      </AuthFields>

      <Button
        label={SIGN_UP_COPY.submit}
        size="stage"
        busyLabel={SIGN_UP_COPY.submitting}
        busy={signUp.isPending}
        onPress={submit}
      />
    </AuthStage>
  );
}
