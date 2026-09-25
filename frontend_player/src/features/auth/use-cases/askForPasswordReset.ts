/**
 * *Forgot password?* — ask for the email.
 *
 * One request and no decision: what the server answers is the same for everybody, so there is
 * nothing here to branch on and nothing to hand the screen but *it went*.
 */

import { forgotPassword } from '../api/authApi';

export async function askForPasswordReset(email: string): Promise<void> {
  await forgotPassword({ email });
}
