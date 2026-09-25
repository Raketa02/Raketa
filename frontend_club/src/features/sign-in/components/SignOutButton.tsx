import { Button } from '@/ui/Button';

import { signOut } from '../actions';
import { SIGN_OUT_COPY } from '../copy';

/** **Sign out**, in the top bar: revokes the session and returns to sign-in (#500 story 90). */
export function SignOutButton() {
  return (
    <form action={signOut}>
      <Button type="submit" tone="quiet">
        {SIGN_OUT_COPY.submit}
      </Button>
    </form>
  );
}
