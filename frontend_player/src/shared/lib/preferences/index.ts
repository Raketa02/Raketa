/**
 * The phone-preferences store's public surface — see `phonePreferences.ts` and
 * [ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md).
 */

export {
  forgetPhonePreferences,
  readPhonePreference,
  savePhonePreference,
  type PhonePreference,
} from './phonePreferences';
export { phonePreferenceKeys } from './phonePreferenceKeys';
