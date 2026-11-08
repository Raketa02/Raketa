import { SignUpScreen, useScreenInView } from '@/features/auth/types';

/** The stage's status bar follows whether sign-up is the screen in view (#784, #785) — the navigator's to say. */
export default function SignUpRoute() {
  const inView = useScreenInView();

  return <SignUpScreen inView={inView} />;
}
