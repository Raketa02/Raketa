# Three gaps — what the Simulator can prove, what Apple charges for, and the Android claim nobody checked

Research output for [`Raketa02/Raketa#36`](https://github.com/Raketa02/Raketa/issues/36).
**Facts and citations only.** Every non-obvious claim carries an inline link to the vendor that
owns it — Apple, Google/Android, Expo. No blog posts, no StackOverflow, no Medium. Where a vendor
**does not** document something, this file says so in those words rather than inferring.

Unlike [`push-transport.md`](https://github.com/Raketa02/Raketa/blob/research/push-transport/docs/specs/now/research/push-transport.md), which is documentation end to end, **this file
contains measurements.** Claims tagged **`[EXEC]`** were executed on this machine on 2026-08-21
against Xcode 16.0 (build 16A242d) and the iOS 18.0 Simulator runtime, and the exact commands and
their output are recorded in §1.4 so anyone can re-run them. Nothing was executed against a real
device, a real APNs endpoint, a credential, or a network service.

This file decides nothing. [ADR-0062](../../../adr/0062-a-notification-is-a-prompt-to-look-not-a-record.md)
shipped one rule provisionally and [ADR-0065](../../../adr/0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md)
named one unsourced claim. The job here is to establish what is true so the tickets around them can
decide.

---

## Verdict — read this first

> **1. `xcrun simctl push` cannot measure a collapse replacement — and it can measure the fact
> ADR-0062 is actually provisional on.** Those are two different sentences and both are now
> measured. `apns-collapse-id` is unreachable from `simctl` in every placement tried; every push
> lands as a brand-new notification with a fresh UUID identifier. But `interruption-level` **is**
> honoured end to end, and the replacement machinery Apple's collapse-id feeds into — the
> `UNNotificationRequest.identifier` — **works on the Simulator when the app sets it directly.**
> Reposting under a live identifier at `passive` posts **no banner and does not wake the screen**;
> reposting the same identifier at `active` does both. **ADR-0062's fallback branch is the one
> that is now unsupported by evidence, not its main branch.**
>
> **2. No. Apple's free tier does not get Push Notifications, and the gate is Apple's, not Expo's.**
> Apple's own capability table awards Push Notifications to the two paid programs and leaves the
> free *Apple Developer* column **blank** — one of 48 of 57 capabilities that column does not
> carry. [#26](https://github.com/Raketa02/Raketa/issues/26)'s assumption was right for the wrong
> reason: the blocker is a membership, not a tool.
>
> **3. Confirmed, verbatim, and stronger than ADR-0065 states.** `NotificationChannel.setBypassDnd`
> is documented as effective only for *"Apps with Do Not Disturb policy access"* — and carries a
> second condition ADR-0065 did not know about: *"only if the channel hasn't been updated by the
> user since its creation."* Android's own service code **silently overwrites** the value when the
> app lacks access; nothing throws.

| The question | The answer | The single load-bearing source |
|---|---|---|
| Does `simctl push` honour `interruption-level`? | **Yes**, in the payload *and* in the presentation | `[EXEC]` §1.2 — `passive` → no banner, `canTurnOnDisplay: 0`; `active` → banner, `canTurnOnDisplay: 1` |
| Does `simctl` expose an `apns-collapse-id` equivalent? | **No.** The tool's whole API is `sendPushNotificationForBundleID:jsonPayload:error:` — bundle ID and a JSON body. There is no header channel | `xcrun simctl help push`, and the selector in Apple's own `simctl` binary (§1.1) |
| Can the Simulator answer "does a passive collapse-replacement buzz"? | **Not by the remote path. Yes by a proxy** Apple's docs tie to the same field | [Apple, `UNNotificationRequest.identifier`](https://developer.apple.com/documentation/usernotifications/unnotificationrequest/identifier) + `[EXEC]` §1.3 |
| Does Apple document Simulator notification fidelity? | **No.** There is no such page. The only current first-party specification of the payload is eight lines of `--help`; the archived guide still lists push as unsupported entirely | §1.5 |
| Free personal team + Push Notifications on a device? | **No** | [Apple, *Supported capabilities (iOS)*](https://developer.apple.com/help/account/reference/supported-capabilities-ios) |
| Does channel DND bypass need Notification Policy Access? | **Yes** | [Android, `NotificationChannel.setBypassDnd`](https://developer.android.com/reference/android/app/NotificationChannel#setBypassDnd(boolean)) |

---

## 1. The iOS Simulator — question 1

### 1.1 The crux: `apns-collapse-id` is unreachable, and the reason is structural

`apns-collapse-id` is an **HTTP header** on `POST /3/device/<token>`
([Apple](https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns)).
`xcrun simctl push` has no HTTP request to put a header on. Its entire published contract is:

> ```
> Send a simulated push notification
> Usage: simctl push <device> [<bundle identifier>] (<json file> | -)
>
> 	bundle identifier
> 	     The bundle identifier of the target application
> 	     If the payload file contains a 'Simulator Target Bundle' top-level key this parameter may be omitted.
> 	     If both are provided this argument will override the value from the payload.
> 	json file
> 	     Path to a JSON payload or '-' to read from stdin. The payload must:
> 	       - Contain an object at the top level.
> 	       - Contain an 'aps' key with valid Apple Push Notification values.
> 	       - Be 4096 bytes or less.
>
> Only application remote push notifications are supported. VoIP, Complication, File Provider, and other types are not supported.
> ```
> — `xcrun simctl help push`, Xcode 16.0 `[EXEC]`

**That help text is the complete first-party specification.** `Simulator Target Bundle` is the only
top-level key it names, and it is an addressing key, not a delivery-option key.

The implementation confirms there is nowhere for a header to go. Apple's `simctl` on disk is a
725-byte shell shim that execs
`/Library/Developer/PrivateFrameworks/CoreSimulator.framework/Versions/A/Resources/bin/simctl`, and
the only push-related selector in that binary is:

```
sendPushNotificationForBundleID:jsonPayload:error:
```

`[EXEC]` — `strings` over Apple's own `simctl` binary. **Two arguments: a bundle ID and a JSON
payload.** There is no headers parameter, no options dictionary, and no third channel of any kind.
Whatever the Simulator does with a push, it does from the payload alone.

### 1.2 What `simctl push` *does* honour — measured

`[EXEC]` A minimal iOS app (`com.raketa.pushprobe`, one `UIViewController`, a
`UNUserNotificationCenterDelegate`, and a 3-second `getDeliveredNotifications` poll) was compiled
with `xcrun -sdk iphonesimulator swiftc`, hand-bundled, and installed on an *iPhone 16* running iOS
18.0. Ten pushes were then sent and every delivered notification read back.

| Payload | `content.interruptionLevel` read back | Meaning |
|---|---|---|
| `"aps": { "interruption-level": "passive" }` | `0` | `.passive` — **honoured** |
| no `interruption-level` key at all | `1` | `.active` — the documented default, so `0` above was not a default |
| `"aps": { "interruption-level": "time-sensitive" }` | `2` | `.timeSensitive` — **honoured** |
| `"aps": { "thread-id": "th-1" }` | `threadIdentifier == "th-1"` | documented `aps` keys pass through intact |

And it is honoured in **presentation**, not merely in the content object. With the app in the
background and full authorization, SpringBoard's own log shows the two paths diverging:

| Push | SpringBoard destination | Screen |
|---|---|---|
| `interruption-level: "active"` | `Rolling banner…` → `Posting notification 20D7-68EF to destination SBNotificationBannerDestination` | `Screen can be turned on for notification 20D7-68EF: 1 [ … canTurnOnDisplay: 1 … ]` |
| `interruption-level: "passive"` | `Posting notification 01ED-796C to destination CSNotificationDispatcher` — **and no banner destination at all** | `Screen can be turned on for notification 01ED-796C: 0 [ … canTurnOnDisplay: 0 … ]` |

`[EXEC]`, `xcrun simctl spawn <device> log stream --predicate 'subsystem CONTAINS "UserNotifications"'`.

**So the Simulator is a faithful instrument for `interruption-level`.** That half of ADR-0062's
provisional fact needed no device and never did.

### 1.3 Collapse: four placements, zero replacements

`[EXEC]` The collapse identifier was offered to `simctl push` in every place it could plausibly be
read. Nothing collapsed:

| Placement tried | Result |
|---|---|
| top-level `"apns-collapse-id": "seat-1"` (twice) | **2** separate delivered notifications, identifiers `F13888E8-…` and `F10F7426-…` |
| inside `aps`: `"aps": { "apns-collapse-id": "seat-2" }` (twice) | **2** separate, `9A5DDD97-…` / `95328F67-…` |
| top-level `"collapse-id": "seat-3"` (twice) | **2** separate, `A2BE4694-…` / `D63EB7A8-…` |
| top-level `"identifier": "seat-4"` (twice) | **2** separate, `3E9DB72E-…` / `74BC0260-…` |

Ten pushes, ten rows in Notification Center, **ten distinct random UUIDs**. Not one push produced
an identifier equal to the value supplied. That is the whole answer, because of what Apple says the
identifier *is* on a real device:

> *"For remote notifications, the system sets this property to the value of the `apns-collapse-id`
> key that you specified in the APNs request header"* … *"If you use the same identifier when
> scheduling a new notification, the system removes the previously scheduled notification with that
> identifier and replaces it with the new one."*
> — [Apple, `UNNotificationRequest.identifier`](https://developer.apple.com/documentation/usernotifications/unnotificationrequest/identifier)

**Apple names the identifier as the mechanism, and `simctl` always generates a fresh one.** A
replacement is therefore unreachable through `simctl push`. This is a clean, structural *no*, not a
version-dependent quirk.

**Apple does not document this.** There is no page saying `simctl push` ignores collapse
identifiers, and no page saying it honours them. The finding above is a measurement, not a citation.

### 1.4 The proxy that *does* answer ADR-0062 — and its exact caveat

The replacement machinery is present in the Simulator. It is only `simctl` that cannot address it.
`[EXEC]` A second app posted **local** notifications, setting `UNNotificationRequest.identifier`
directly — the same field Apple documents a collapse-id as populating:

| Step | Action | Delivered set afterwards |
|---|---|---|
| A | `add(identifier: "dup-1", title: "Local A")` | **1** — `dup-1` / *Local A* |
| B | `add(identifier: "dup-1", title: "Local B")` | **1** — `dup-1` / *Local B*, timestamp updated. **Replaced in place** |
| C | `add(identifier: "dup-2", title: "Local C")` | **2** — a different identifier makes a second row |

Then the presentation question, with the app **backgrounded** and full authorization, watching
SpringBoard rather than the screen:

| Step | Notification | Level | Banner destination | Screen |
|---|---|---|---|---|
| 1 | `rep-1` first post | `.active` | `Rolling banner` → `SBNotificationBannerDestination` | `Screen can be turned on … 886C-EB36: 1` |
| 2 | `rep-1` **replacement** | `.passive` | **none** — `CSNotificationDispatcher` only | `Screen can be turned on … 886C-EB36: 0 [ … canTurnOnDisplay: 0 … ]` |
| 3 | `rep-2` first post | `.passive` | **none** | `… EA34-D28B: 0` |
| 4 | `rep-2` **replacement** | `.active` | `Rolling banner` → `SBNotificationBannerDestination` | `… EA34-D28B: 1` |

Steps 1–2 share one notification record (`logDigest: 886C-EB36`, `requestIdentifier: rep-1`) and
steps 3–4 share another (`EA34-D28B`, `rep-2`), which is the replacement itself visible in the log.

**Read step 2 and step 4 together.** A replacement at `active` re-alerts and wakes the screen. The
*same replacement* at `passive` does neither. The interruption level is evaluated on the delivered
notification independently of whether it is a first post or a replacement.

**The caveat, stated plainly.** This exercises the local-notification path, not the remote one. The
two share the daemon, the `UNNotificationRequest`, the identifier semantics and — as steps 1–4 show
— the same SpringBoard destination logic that §1.2 showed `simctl push` also feeds. What it does
**not** exercise is APNs, and **Apple does not document** that the two paths make the presentation
decision at the same point. This is strong evidence, not proof. It moves ADR-0062's rule from
*unmeasured* to *measured by proxy*, and it is a great deal cheaper than the alternative.

### 1.5 Is Simulator notification fidelity documented? No.

- There is **no** `developer.apple.com/documentation/xcode/testing-notifications-in-simulator`
  page — HTTP 404.
- [*Testing in Simulator versus testing on hardware devices*](https://developer.apple.com/documentation/xcode/testing-in-simulator-versus-testing-on-hardware-devices)
  is Apple's page on the topic. It covers iCloud sync, Face ID / Touch ID, fall detection, memory
  warnings and location, and the one thing it firmly reserves for hardware is **performance** —
  *"the simulator is not an accurate test of an app's performance, memory usage, and networking
  speed"*, because it runs on the Mac's resources. **It says nothing about notifications.**
  *(Provenance caveat: this page renders in Apple's own search index but returns HTTP 404 to a
  direct fetch, so the quoted sentence was read through Apple's index rather than off the page.
  It is cited for the **absence** of a notification statement, which is what matters here.)*
- The archived *iOS Simulator Guide* still lists, under API differences, *"Receiving and sending
  Apple push notifications"* as unsupported
  ([Apple, archived](https://developer.apple.com/library/archive/documentation/IDEs/Conceptual/iOS_Simulator_Guide/TestingontheiOSSimulator/TestingontheiOSSimulator.html)).
  That page is pinned to iOS 8.2 and predates `simctl push` entirely; it is superseded by the tool's
  existence and is cited here only so nobody re-discovers it and draws the wrong conclusion.
- **Apple documents no haptics statement either way.** The archived hardware-differences list names
  motion, camera, microphone, proximity, barometer and ambient light — and **does not mention the
  Taptic Engine**. "Did it buzz" is therefore unanswerable on a Simulator not because Apple says so
  but because Apple says nothing; what *is* answerable, and what §1.2–1.3 measured, is *"did the
  system route it to a banner and wake the screen"*, which is the same decision.

### 1.6 One thing the agent could not do, and a human can

`[EXEC]` `xcrun simctl privacy` grants calendar, contacts, location, photos, media-library,
microphone, motion, reminders and siri. **It has no `notifications` service.** The only
authorization obtainable without a tap is **provisional**, which Apple documents as never alerting:
provisional notifications *"don't interrupt the person with a sound or banner, or appear on the lock
screen"*
([Apple](https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications)).
The full-authorization runs above were obtained by editing the booted device's own
`data/Library/BulletinBoard/VersionedSectionInfo.plist` — a private file format, fine for a
throwaway probe, **not** something to build a repeatable test on. A human tapping *Allow* once on a
Simulator prompt gets the same state in two seconds and is the right way to re-run any of this.

---

## 2. Apple's free personal team — question 2

**Apple states it directly, in a table, on its own account-help site.**
[*Supported capabilities (iOS)*](https://developer.apple.com/help/account/reference/supported-capabilities-ios)
opens with: *"The capabilities available to an iOS provisioning profile depend on your program
membership."* It has three columns, defined at the foot of the page verbatim:

> **ADP:** *"Apple Developer Program membership. Members of this paid program can distribute apps on
> the App Store."*
> **ADEP:** *"Apple Developer Enterprise Program membership. Members of this paid program can
> distribute apps to employees within an organization."*
> **Apple Developer:** *"Apple Account holders who have agreed to the Apple Developer Agreement to
> access certain resources on the Apple Developer website. **No cost is associated with this
> agreement and developers can't distribute apps.**"*

The third column is the free tier — the account Xcode surfaces as a *Personal Team*. The row reads:

| Capability | ADP | ADEP | Apple Developer |
|---|---|---|---|
| **Push notifications** | ✓ | ✓ | *(blank)* |

**The blank is meaningful, not an omission.** `[EXEC]` Parsing the page's 57 capability rows, the
free column carries a checkmark on exactly **nine**: App groups, Background modes, Data protection,
HealthKit, HomeKit, Inter-App Audio, Keychain sharing, Maps, Wireless Accessory Configuration.
Push notifications is one of the other 48. **Time Sensitive Notifications** — which
[ADR-0065](../../../adr/0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md)
depends on — is also blank in that column.

Two supporting statements from Apple, neither of which contradicts the table:

- *"You can learn how to develop apps for Apple platforms for free without enrolling. With just an
  Apple Account, you can access Xcode, software downloads, documentation, sample code, forums, and
  Feedback Assistant, **as well as test your apps on devices**."*
  ([Apple, *Choosing a Membership*](https://developer.apple.com/support/compare-memberships/)) —
  on-device testing is free; the *capability* is not.
- *"Xcode Personal Team. If you're signing in to Xcode with an Apple Account that's not affiliated
  with the Apple Developer Program, you'll be able to perform on-device testing for personal use
  (Xcode refers to this as a Personal Team)."* Its named limits: *"The number of App IDs that can be
  registered your account at one time is limited to 10 and each expires after 7 days"*; *"The number
  of test devices … is limited to 3 and each expires after 7 days"*; *"Provisioning profiles will
  expire 7 days from issuance."* (same page)

**What this settles for [#26](https://github.com/Raketa02/Raketa/issues/26).** Expo's *"A paid
Apple Developer Account is required to generate credentials"*
([Expo](https://docs.expo.dev/app-signing/apple-developer-program-roles-and-permissions/)) is not
the binding constraint — it is downstream of one. Even hand-rolling the provisioning outside Expo,
a personal team cannot put the Push Notifications capability on an App ID, so it cannot obtain an
APNs-registerable entitlement, so no route reaches a device push without the $99 membership. **The
Apple gate on #26 is real, and it is Apple's.**

**Apple does not document** what Xcode shows when a Personal Team selects Push Notifications under
*Signing & Capabilities*. The failure mode is unstated; only the entitlement's unavailability is.

---

## 3. Android channel-level Do Not Disturb bypass — question 3

[ADR-0065](../../../adr/0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md)
flagged this as the one claim [#25](https://github.com/Raketa02/Raketa/issues/25) could not verify
because *"Android's reference pages did not render."* They render with `?hl=en` appended — the
bare URL enters a redirect loop. **The claim is confirmed verbatim.**

> **`setBypassDnd`** — added in API level 26.
> *"Sets whether or not notifications posted to this channel can interrupt the user in
> `NotificationManager.INTERRUPTION_FILTER_PRIORITY` mode.*
> ***Apps with Do Not Disturb policy access (see `NotificationManager.isNotificationPolicyAccessGranted()`)
> can set up their own channels this way, but only if the channel hasn't been updated by the user
> since its creation.***
> *Otherwise, this value is only modifiable by the system and the notification ranker."*
> — [Android, `NotificationChannel.setBypassDnd(boolean)`](https://developer.android.com/reference/android/app/NotificationChannel#setBypassDnd(boolean))

And the permission it points at is a **user grant obtained by sending the user to Settings**:

> *"Checks the ability to modify Notification Policy for the calling package. Returns `true` if the
> calling package can modify notification policy. **Apps can request policy access by sending the
> user to the activity that matches the system intent action
> `Settings.ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS`.** Use
> `ACTION_NOTIFICATION_POLICY_ACCESS_GRANTED_CHANGED` to listen for user grant or denial of this
> access."*
> — [Android, `NotificationManager.isNotificationPolicyAccessGranted()`](https://developer.android.com/reference/android/app/NotificationManager#isNotificationPolicyAccessGranted())

> *"Activity Action: Show Notification Policy access settings. **Users can grant and deny access to
> Notification Policy (DND / Modes) configuration from here. Managed profiles cannot grant
> Notification Policy access.** … Input: Nothing. Output: Nothing. In some cases, a matching Activity
> may not exist, so ensure you safeguard against this."*
> — [Android, `Settings.ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS`](https://developer.android.com/reference/android/provider/Settings#ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS)

### Three details ADR-0065 did not have

1. **It fails silently.** Android's notification service does not throw when an app without access
   sets `bypassDnd` — it **overwrites the value**. From AOSP, in the channel-creation path:

   ```java
   // Reset fields that apps aren't allowed to set.
   if (fromTargetApp && !hasDndAccess) {
       channel.setBypassDnd(r.priority == Notification.PRIORITY_MAX);
   }
   ```
   — [`PreferencesHelper.createNotificationChannel`](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/notification/PreferencesHelper.java)

   An app that calls `setBypassDnd(true)` without policy access gets a channel that silently does
   not bypass. There is no error to observe and no runtime signal to log.

2. **A second precondition, even *with* access.** The javadoc's *"but only if the channel hasn't
   been updated by the user since its creation"* is enforced as
   `if (existing.getUserLockedFields() == 0 && hasDndAccess)` in the same file. **A player who has
   ever touched that channel's settings locks the app out of it permanently.** ADR-0065's *"a
   channel is a switch the player can see and throw"* is therefore even more true than the record
   claims: throwing it once forecloses the bypass for good.

3. **Bypass is not sufficient on its own.** *"Whether or not notifications posted to this channel
   can bypass the Do Not Disturb `NotificationManager.INTERRUPTION_FILTER_PRIORITY` mode **when the
   active policy allows priority channels to bypass notification filtering**."*
   ([Android, `canBypassDnd()`](https://developer.android.com/reference/android/app/NotificationChannel#canBypassDnd()))
   The user's own DND policy is the outer gate; a bypassing channel is filtered anyway if their
   policy does not admit priority channels.

### And the API surface hides all of it

`expo-notifications` exposes `bypassDnd: boolean` on `NotificationChannel` / `NotificationChannelInput`
with **no description at all** in the property table
([Expo](https://docs.expo.dev/versions/latest/sdk/notifications/)), and no mention anywhere on that
page of Notification Policy Access. Passing `bypassDnd: true` to `setNotificationChannelAsync`
compiles, runs, returns a channel object, and — for every user who has not granted policy access —
does nothing. **This is the most expensive shape of a wrong assumption: one that never fails
loudly.**

**Verdict: ADR-0065's sentence is correct as written**, and the *"we do not ask"* decision it
supports is better founded than the record claims. Nothing on that ADR needs to move.

---

## 4. What this changes on the existing records

| Where | What changes |
|---|---|
| [ADR-0062](../../../adr/0062-a-notification-is-a-prompt-to-look-not-a-record.md): *"Before this ships, one message goes to one real iPhone with both set and somebody watches whether it buzzes"* | **The watching can happen on a Simulator, today, for free** — by the §1.4 proxy, not by the remote path. The real-iPhone run remains the only way to close it against APNs itself, but it is no longer the only way to get evidence |
| ADR-0062: *"If it buzzes, the fallback is that every replacement buzzes"* | **The fallback branch is now the unevidenced one.** Every measurement in §1.2–1.4 points at `passive` suppressing the alert on a replacement as firmly as on a first post |
| ADR-0062: *"that assumption is one Apple switches off during testing"* | That sentence is about the **silent-push power budget** — *"These limits are disabled when testing your app from Xcode"* ([Apple](https://developer.apple.com/documentation/usernotifications/troubleshooting-push-notifications)). **No equivalent statement exists for `interruption-level`.** Apple documents no development-time override of notification presentation, so the "passes QA, fails in the field" hazard does not obviously apply to this rule |
| [#26](https://github.com/Raketa02/Raketa/issues/26): *"the measurement needs a real iPhone, which needs a paid membership"* | **Half right.** The paid membership is real and Apple-imposed (§2). The *measurement* no longer depends on it |
| [ADR-0065](../../../adr/0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md): *"the Android DND fact is the one claim on this record that #25 did not verify"* | **Verified.** Remove it from #26's device checklist — it is a documented answer, which beats a measured one |
| ADR-0065's Time Sensitive dependency | Also blank in Apple's free column (§2). It is a self-serve capability *for a paying member*, which is not the same as a free one |

---

## 5. What remains open

1. **Whether the §1.4 proxy is accepted as sufficient.** It is a measurement of the same field
   through a different door. Somebody has to decide whether ADR-0062 comes off provisional on it,
   or waits for the paid membership. This file does not decide that.
2. **What a collapse-replacement does to a notification the user already dismissed.** Unmeasurable
   here (no collapse) and **Apple does not document it** — carried over unchanged from
   [`push-transport.md`](https://github.com/Raketa02/Raketa/blob/research/push-transport/docs/specs/now/research/push-transport.md).
3. **Whether the Expo Push Service's `interruptionLevel` survives its own translation.** §1.2
   measured `simctl` → SpringBoard. Expo → APNs → device is a different hop, and Expo documents the
   field but not its fidelity.
4. **Whether a real APNs collapse-replacement re-alerts.** Still the only question a device
   genuinely owns, and the §1.4 result is the prior it should be tested against.
5. **A repeatable harness.** Everything in §1 was run from a scratch directory with a hand-built
   `.app` and a hand-edited private plist. If the Simulator becomes part of how notification
   behaviour is checked, that wants to be an XCUITest with a human granting authorization once,
   not this.

---

### Provenance

Read on 2026-08-21. **Apple:** `developer.apple.com/documentation/usernotifications/{unnotificationrequest/identifier,
sending-notification-requests-to-apns, asking-permission-to-use-notifications,
troubleshooting-push-notifications}`, `developer.apple.com/documentation/xcode/testing-in-simulator-versus-testing-on-hardware-devices`,
`developer.apple.com/help/account/reference/supported-capabilities-ios`,
`developer.apple.com/support/compare-memberships/`, and the archived *iOS Simulator Guide*.
**Android:** `developer.android.com/reference/android/app/{NotificationChannel,NotificationManager}`
and `…/android/provider/Settings` (all with `?hl=en` — the bare URLs redirect-loop, which is why
[#25](https://github.com/Raketa02/Raketa/issues/25) could not read them), plus AOSP
`frameworks/base` at `refs/heads/main` for `NotificationChannel.java` and `PreferencesHelper.java`.
**Expo:** `docs.expo.dev/versions/latest/sdk/notifications/`,
`docs.expo.dev/app-signing/apple-developer-program-roles-and-permissions/`.

**Executed** on macOS 24.6.0, Xcode 16.0 (16A242d), CoreSimulator 987, iOS 18.0 Simulator runtime
(22A3351), device *iPhone 16* `CB45C19E-…`. Two throwaway apps were compiled with
`xcrun -sdk iphonesimulator swiftc`, installed with `simctl install`, driven with `simctl push` and
`simctl launch`, and observed through `simctl spawn … log stream`. Every artefact lived in a
scratch directory outside this repository; the Simulator device was left with the probe apps
uninstalled. **No credential, certificate, `.env` file or network service was touched, and no
deployment, `eas` or `aws` command was run.**

Repo files read: [`docs/adr/0062`](../../../adr/0062-a-notification-is-a-prompt-to-look-not-a-record.md),
[`0065`](../../../adr/0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md),
[`push-transport.md`](https://github.com/Raketa02/Raketa/blob/research/push-transport/docs/specs/now/research/push-transport.md).

No file under `backend/`, `frontend_player/` or `frontend_club/` was modified.
