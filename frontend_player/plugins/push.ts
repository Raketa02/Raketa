/**
 * **The iPhone build without the push entitlement** — a local config plugin, until the Apple
 * Developer membership exists (#559; open item O6; `src/shared/config/push.ts`).
 *
 * `expo-notifications`' own plugin writes `aps-environment` into the iOS entitlements unless one is
 * there already — and `expo prebuild` applies it whether or not `app.config.ts` lists it. A personal
 * Apple team cannot sign that entitlement, so a development build on a real iPhone would stop
 * building the day the library arrived, for a push Apple would not deliver without the membership
 * anyway. `withPush` takes it back out while `IPHONE_PUSH` is false.
 *
 * **The order is what makes it work.** Each plugin's change wraps the ones registered before it and
 * runs first, so the one registered **earliest runs last**: `app.config.ts` is wrapped in this one
 * as it is returned — before its `plugins` list is applied, the library among them — so the removal
 * lands after the library has added the entitlement. `npx expo config --type introspect` shows the
 * result without writing `ios/`: no `aps-environment` while `IPHONE_PUSH` is false.
 *
 * Node loads this while Expo evaluates `app.config.ts`, before Metro exists; nothing in `src/`
 * imports it. Delete the removal the day `IPHONE_PUSH` turns true.
 */

import { withEntitlementsPlist, type ConfigPlugin } from 'expo/config-plugins';

import { IPHONE_PUSH } from '../src/shared/config/push';

const withoutIphonePush: ConfigPlugin = (config) =>
  withEntitlementsPlist(config, (entitled) => {
    delete entitled.modResults['aps-environment'];
    return entitled;
  });

/** The app's config as push stands today — see the module note. */
export const withPush: ConfigPlugin = (config) =>
  IPHONE_PUSH ? config : withoutIphonePush(config);
