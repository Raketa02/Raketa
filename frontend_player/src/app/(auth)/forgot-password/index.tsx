import { useLocalSearchParams } from 'expo-router';

import { ForgotPasswordScreen, parseEmailParam } from '@/features/auth/types';

/** *Forgot password?* — the email form, opened from under the Sign in button (#515). */
export default function ForgotPasswordRoute() {
  return <ForgotPasswordScreen email={parseEmailParam(useLocalSearchParams())} />;
}
