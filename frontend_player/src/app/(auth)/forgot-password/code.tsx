import { useLocalSearchParams } from 'expo-router';

import { ResetCodeScreen, parseEmailParam } from '@/features/auth/types';

/** *Enter the code* — the email and the 8-character code from it (#515). */
export default function ResetCodeRoute() {
  return <ResetCodeScreen email={parseEmailParam(useLocalSearchParams())} />;
}
