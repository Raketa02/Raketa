import { SignInScreen, useScreenInView } from '@/features/auth/types';

/** The stage's status bar follows whether sign-in is the screen in view (#784) — the navigator's to say. */
export default function SignInRoute() {
  const inView = useScreenInView();

  return <SignInScreen inView={inView} />;
}
