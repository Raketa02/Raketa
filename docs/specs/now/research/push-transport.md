# Push on the locked runtime — one message out, and the one that takes it back

Research output for [`Raketa02/Raketa#25`](https://github.com/Raketa02/Raketa/issues/25).
**Facts and citations only.** Every non-obvious claim carries an inline link to the vendor that
owns it — Apple, Google/Firebase, Expo. No blog posts, no StackOverflow, no Medium; where a
secondary source pointed the way, the primary page is what is cited. Where a vendor **does not**
document something, this file says so in those words rather than inferring, because on this
subject the undocumented cases are where the design breaks.

This file does **not** decide anything. [ADR-0052](../../../adr/0052-a-vacancy-is-offered-not-announced.md)
made a design commitment that rests on a platform capability; the job here is to establish whether
that capability exists, and to name the forks. Choosing between them is the next ticket.

---

## Verdict — read this first

> **ADR-0052's silent withdrawal does not survive on iOS. On Android it survives only if the
> *offer* is also redesigned, and even then it is best-effort. There is no platform on which
> "the server removes a delivered notification" is a guarantee, and on both platforms the
> mechanism that gets closest is one the vendor documents as throttled for exactly this use.**

The load-bearing sentence in [ADR-0052](../../../adr/0052-a-vacancy-is-offered-not-announced.md)
is *"the delivered notification is removed from the lock screen and the card disappears from
Now… No second notification."* Split it in three:

| The claim | iOS | Android |
|---|---|---|
| A server can **replace** a delivered lock-screen notification | **Yes.** `apns-collapse-id`. No app code, survives force-quit | **Yes.** `android.notification.tag` — *"If specified and a notification with the same tag is already being shown, the new notification replaces the existing one in the notification drawer"* ([Firebase](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages)) |
| A server can **remove** it, leaving nothing | **No documented mechanism.** Only via a silent push waking the app — which Apple documents as *not guaranteed*, throttled to *"two or three per hour"*, subject to a daily power budget, discarded on force-quit, and with those limits *"disabled when testing your app from Xcode"* | **No FCM field exists.** Only via a data message the app turns into `NotificationManager.cancel`. Google documents that high-priority messages which produce no notification get **deprioritized on a 7-day behavioural window** — which is precisely the shape of a withdrawal |
| The removal **arrives** if the device was offline when it was sent | **Not reliably.** APNs stores exactly **one** notification per bundle ID and *"may reorder notifications you send to the same device token"* | **Stored** up to the TTL — but *"FCM doesn't guarantee the order of delivery"* ([Firebase](https://firebase.google.com/docs/cloud-messaging/customize-messages/collapsible-message-types)), and a `ttl: 0` retraction sent for latency is discarded outright |

Five consequences follow. All five are facts, not opinions.

1. **The second buzz ADR-0052 refused is the mechanism that actually works.** A
   collapse-id / tag *replacement* is the only retraction path on either platform that needs no
   app process, no extra permission, and no cooperation from the power manager.
2. **The second buzz need not be a buzz.** iOS 15+ `interruption-level: "passive"` is documented
   as *"The system adds the notification to the notification list without lighting up the screen
   or playing a sound"*
   ([Apple](https://developer.apple.com/documentation/usernotifications/unnotificationinterruptionlevel)).
   Android's equivalent is a low-importance channel. **This is a third option ADR-0052 did not
   consider**: not a buzz, not a vanish, but a quiet in-place rewrite — server-driven, no app
   wake, and it answers the ADR's own worry that *"a notification that vanishes is exactly what a
   malfunctioning app looks like."*
3. **On Android, making the offer *cancellable* makes the offer *less reliable*.** Notification-payload
   messages are displayed by Google Play services *"without any need to start the app"* — the
   default on Android Q+ ([Firebase](https://firebase.google.com/docs/cloud-messaging/android-message-priority)) —
   and Google does not document the notification id it uses, so the app cannot cancel it. To be
   able to cancel, the app must post the notification itself from a **data-only** message, which
   means the offer now depends on the app process running. That trade is invisible in ADR-0052 and
   is the single most consequential finding in this file after the iOS verdict.
4. **Provisional authorization is not a way out.** Apple's exact words: provisional notifications
   *"don't interrupt the person with a sound or banner, **or appear on the lock screen**"*
   ([Apple](https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications)).
   An offer that expires in one hour, delivered only to Notification Center history, is an offer
   the twelve-hour backstop will quietly take away.
5. **Whatever is chosen, the app must reconcile on foreground.** Apple says so itself: *"Your app
   may need to synchronize with your application server about the information missed due to
   discarded, expired, or overwritten notification."*
   ([Apple](https://developer.apple.com/documentation/usernotifications/viewing-the-status-of-push-notifications-using-metrics-and-apns)).
   `GET /now` already is that reconciliation ([ADR-0038](../../../adr/0038-now-is-polled-the-push-is-specified-and-deferred.md)),
   so *"the card disappears from Now"* is free and correct. Only the lock-screen half is in doubt.

**Nothing here blocks building the channel.** Sending the one message is well-supported, cheap, and
does not violate [ADR-0013](../../../adr/0013-player-app-runtime-architecture.md). It is the
*unsending* that has to be re-specified.

---

## 0. What the repo already fixes

### From [ADR-0013](../../../adr/0013-player-app-runtime-architecture.md) and the code

| Constraint | Where | What it rules in or out |
|---|---|---|
| **Expo SDK 52**, React Native 0.76.9, React 18.3.1 | [`frontend_player/package.json`](../../../../frontend_player/package.json) | Current Expo is **SDK 57** (2026-06-30, RN 0.86 — [Expo changelog](https://expo.dev/changelog)). The app is five SDKs behind, and `expo-notifications` must be installed at the version SDK 52 pins |
| **Development builds, not Expo Go** | ADR-0013 Decision | Disposes of the biggest Expo push gotcha before it arises. Expo Go on Android has had no remote push since SDK 53: *"Push notifications are no longer supported in Expo Go for Android, after being deprecated in SDK 52"* ([Expo SDK 53 changelog](https://expo.dev/changelog/sdk-53)); the library docs repeat it — *"Push notifications (remote notifications) functionality provided by `expo-notifications` is unavailable in Expo Go on Android from SDK 53"* ([Expo](https://docs.expo.dev/versions/latest/sdk/notifications/)). Since this app already uses development builds, that change costs nothing |
| **Native projects are CNG output** | ADR-0013 Decision; there is no `frontend_player/ios/` or `frontend_player/android/` | Everything native arrives as a **config plugin**. `UIBackgroundModes` and `google-services.json` wiring are plugin/app-config properties, never hand-edited native files. A Notification Service Extension, being a separate native target, is *not* something the `expo-notifications` plugin provides |
| **No `eas.json` in the repo** | verified | EAS Build is unconfigured. `eas build` and `eas credentials` are both prerequisites of an iOS push credential, so this is on the critical path for [#26](https://github.com/Raketa02/Raketa/issues/26) |
| **One bundle identifier for all four environments** | [`app.config.ts`](../../../../frontend_player/app.config.ts) — `com.raketa.player` for both `ios.bundleIdentifier` and `android.package`; the file's own comment says *"per-environment identifiers wait until a second backend exists"* | One APNs topic and one FCM sender for every environment. Since [`docs/environments.md`](../../../environments.md) says only `local` runs, this is not yet a conflict — but it means APNs' **one-stored-notification-per-bundle-ID** rule (§2c) is shared across every environment on a given handset |
| **`plugins: ['expo-router', 'expo-secure-store']`** | `app.config.ts` | Push means adding `expo-notifications` here, and — for background dismissal on iOS — its `UIBackgroundModes` property. That is a change to a **shipped native capability** |
| **`newArchEnabled: true`** | `app.config.ts` | No conflict found |
| **"Dependencies arrive with the code that needs them"** | ADR-0013 "Not adopted now" | `expo-notifications`, `expo-device` and — for the dismissal path — `expo-task-manager` are new dependencies. ADR-0052 is the stated requirement that unlocks them |
| **TanStack Query owns all server state** | ADR-0013 Decision | A push navigates and invalidates; `GET /now` re-reads. Same rule as the architecture reference: *"Push notification receipt must not directly mutate critical business state without backend confirmation"* ([§121](../../player-app/react_native_expo_production_architecture.md)) |
| **Framework contact concentrated in `src/shared/lib/`** | ADR-0013, "`platform/`, `bootstrap/`, `observability/`" | `expo-notifications` belongs there, not in a feature; ADR-0013's lint rules already fail cross-boundary imports |
| **Never put sensitive content in a payload** | architecture reference §121; and Apple: *"Don't include customer information or any sensitive data… in a notification's payload"* ([Apple](https://developer.apple.com/documentation/usernotifications/generating-a-remote-notification)) | Independently corroborates ADR-0052's *"the time and the urgency, never the venue"* |

**Neither transport option violates ADR-0013.**

### From the Now specification set

| Fixed by | What it fixes |
|---|---|
| [ADR-0038](../../../adr/0038-now-is-polled-the-push-is-specified-and-deferred.md) + [`deltas/live-delivery.md`](../deltas/live-delivery.md) | The deferred **WebSocket** is a different channel: `sync`/`patch`/`drop` frames for a foregrounded screen. Push here is one message to a backgrounded phone. Building push does **not** build the live transport and does not trigger its named condition (*"another player's action reaching a viewer in under one second"*) |
| [ADR-0054](../../../adr/0054-now-refreshes-when-asked-never-on-a-timer.md) | No client timer. A push that opens the app produces a `GET /now` on arrival — which is exactly the reconciliation Apple's docs say you need |
| [`deltas/shelves-and-offers.md`](../deltas/shelves-and-offers.md) §5 | The clocks the transport must hit: exclusive hold **1 h from delivery**; open-call waves **3 → +5 after 10 min → everyone**; delivery **held to 08:00 local** unless the match starts within 12 h; release to all **at latest 12 h before start** |

---

## 1. The transport — Expo Push Service vs bare APNs/FCM

### What each is

**Expo Push Service.** The backend POSTs to `https://exp.host/--/api/v2/push/send` with an **Expo
push token** (`ExponentPushToken[…]`) obtained on device from
`Notifications.getExpoPushTokenAsync({ projectId })`. Expo's infrastructure translates to APNs and
FCM and holds the credentials
([Expo](https://docs.expo.dev/push-notifications/sending-notifications/)).

**Bare.** The backend talks to APNs (`POST /3/device/<token>`, HTTP/2, ES256 JWT from a `.p8` auth
key) and FCM v1 (`POST /v1/projects/<id>/messages:send`, OAuth from a service account) directly.
The device token comes from `getDevicePushTokenAsync()`, which Expo documents as the path for
exactly this — *"send your notifications directly through FCM and APNs"* — under the general
statement *"You can use any push notification service for Expo projects."*
([Expo push FAQ](https://docs.expo.dev/push-notifications/faq/)).

### Cost comparison

| | Expo Push Service | Bare APNs + FCM v1 |
|---|---|---|
| **Provisioning** | The **same** Apple and Google artefacts (§5) — Expo does not remove them, it *stores* them. `eas credentials` can *generate* the APNs key from an Apple login, removing the browser work on the Apple side. Adds an Expo account + EAS project | Same artefacts, but a human downloads the `.p8` and the service-account JSON and installs them as backend secrets — two more secrets in a deployment story where [`CLAUDE.md`](../../../../CLAUDE.md) forbids an agent to create them |
| **Server code** | One HTTPS POST, JSON body, batch of ≤100 | An HTTP/2 client with long-lived connections and JWT signing for APNs; a Google OAuth exchange for FCM; **two** payload shapes; two error taxonomies; two token-invalidation paths |
| **Token handling** | One platform-agnostic Expo token per device. `DeviceNotRegistered` is one receipt error | Separate APNs and FCM tokens; separate `Unregistered` / `UNREGISTERED` handling |
| **Delivery reporting** | Two-stage: a **ticket** synchronously, then a **receipt** from `/push/getReceipts`; *"push receipts are cleared after 24 hours"* | APNs returns a per-stream status immediately and offers a metrics API; FCM returns per-message status and offers BigQuery export plus the `priorityLowered` field ([Firebase](https://firebase.google.com/docs/cloud-messaging/understand-delivery)) — which matters here, see §2b |
| **Third party in the path** | Yes. *"Expo makes a best effort to deliver notifications to the push notification services operated by Google and Apple."* … *"It is more likely for a notification to be delivered to Google or Apple more than once rather than not at all; however, both these results are uncommon."* | No |
| **Throughput ceiling** | **600 notifications/second per project**, ≤100 messages per request | APNs documents no per-second ceiling. FCM's default is **600,000 messages/minute per project** ([Firebase](https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas)) |

### Does the Expo Push API expose the fields §2 needs?

**Yes.** The documented message fields
([Expo](https://docs.expo.dev/push-notifications/sending-notifications/)):

**And Expo documents the two retraction fields more precisely than either platform vendor does.**
Verbatim, from the message-format table:

> `collapseId` — *"An identifier for collapsing notifications. **On Android, this only coalesces
> messages in transit** (if the device is offline, only the latest one with a given `collapseId` is
> delivered) and maps to the FCM `collapse_key`. **To also replace already-displayed notifications
> on Android, use `tag`.** On iOS, this **both coalesces messages in transit and replaces
> already-displayed notifications on the device** and maps to `apns-collapse-id`."*
>
> `tag` — *"An identifier for **replacing notifications already displayed on the device**. If the
> device is already showing a notification with the same `tag`, the new notification **replaces**
> it. This is separate from `collapseId`, which coalesces messages in transit, while `tag` replaces
> already-displayed notifications. Maps to the FCM `notification.tag` field."*

That `collapseId` sentence is the clearest primary statement anywhere that **an iOS collapse-id
replaces a notification already on the device** — Apple only implies it, across two pages (§2a).

| Field | Platform | Relevance |
|---|---|---|
| `collapseId` | both | above — iOS replace primitive; Android in-transit coalescing only |
| `tag` | **Android only** | above — **the Android replace primitive** |
| `contentAvailable` | iOS | The silent-push flag. *"This field replaces the deprecated `_contentAvailable` field, which is still accepted for backwards compatibility."* Expo documents the recipe exactly: *"When you use the Expo Push Service, and specify only `data` and `contentAvailable: true` (and other non-interactive fields such as `ttl`), the resulting push notification request produces a Headless Background Notification."* ([Expo](https://docs.expo.dev/push-notifications/what-you-need-to-know/)) |
| `interruptionLevel` | iOS | `'active' \| 'critical' \| 'passive' \| 'time-sensitive'` — the quiet-replacement lever |
| `priority` | both | `'default' \| 'normal' \| 'high'`; *"Normal priority corresponds to APNs priority level 5 and high priority to 10."* And *"Setting the priority to `high` gives your notification the greatest likelihood that Android will display the notification"* ([FAQ](https://docs.expo.dev/push-notifications/faq/)) |
| `ttl` / `expiration` | both | Store-and-forward lifetime; `ttl` takes precedence; omitted → the provider default of 4 weeks |
| `channelId` | Android | Which channel displays it — the only Android importance/sound lever. A null `channelId` auto-creates a user-facing "Default" channel, and Expo warns *"you may not be able to fully delete it"* |
| `relevanceScore`, `threadId`, `targetContentId`, `filterCriteria`, `mutableContent`, `subtitle`, `sound`, `badge` | iOS | `relevanceScore` is the Scheduled-Summary featuring lever (§4) |
| `icon`, `richContent`, `categoryId`, `title`, `body`, `data` | | Total payload **≤ 4096 bytes** (`MessageTooBig`); `data` *"may be up to about 4KiB"* |

**What is not there:** no `apns-priority: 1`, no per-message `apns-push-type` override, no
`android.notification.notification_priority`, **no `android.notification.proxy`**, no
`android.direct_boot_ok`, no `collapseKey` (the field is `collapseId`), and **no dismissal field of
any kind** — Expo documents no remote "delete notification" endpoint. Only one of those gaps
matters here: **`proxy: DENY` is not reachable through Expo**, which drives the Android
cancellability trade in §2b.

Two operational facts about the service itself. It is **free** — push appears nowhere in
[Expo's pricing](https://expo.dev/pricing) — and by default it is **unauthenticated**: the API
*"currently does not require any authentication"*, with optional per-project push security
(`Authorization: Bearer …`) enabled from the EAS dashboard. Expo names the risk itself: *"if the
tokens are leaked, a malicious user would be able to impersonate your server."* **Turning that on
is a step [#26](https://github.com/Raketa02/Raketa/issues/26) should carry**, because an Expo push
token is a bearer-addressable target and this channel exists to move a scarce resource.

**The choice is reversible, on the server.** Both paths use the same client library; switching is
`getExpoPushTokenAsync` → `getDevicePushTokenAsync` plus backend work. That is the structurally
important fact, and it means this decision does not have to be made before the channel exists.

---

## 2. Unsending — the load-bearing question

### 2a. iOS

**Replacement: yes, documented, reliable.**

`apns-collapse-id` — *"An identifier you use to merge multiple notifications into a single
notification for the user. Typically, each notification request displays a new notification on the
user's device. When sending the same notification more than once, use the same value in this header
to merge the requests. The value of this key must not exceed 64 bytes."*
([Apple](https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns)).
Over 64 bytes is `400 BadCollapseId`
([archived APNs guide](https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/CommunicatingwithAPNs.html)).

The mechanism by which it reaches an *already-displayed* notification is documented on a different
page — `UNNotificationRequest.identifier`:

> *"For remote notifications, the system sets this property to the value of the `apns-collapse-id`
> key that you specified in the APNs request header"* … *"If you use the same identifier when
> scheduling a new notification, the system removes the previously scheduled notification with that
> identifier and replaces it with the new one."*
> — [Apple](https://developer.apple.com/documentation/usernotifications/unnotificationrequest/identifier)

The archived guide states the user-facing effect plainly: *"Multiple notifications with the same
collapse identifier are displayed to the user as a single notification."*

**This also hands the client a stable handle**, which is what makes on-device removal addressable at
all (below).

Expo states the conclusion outright, where Apple only implies it: `collapseId` *"on iOS… both
coalesces messages in transit and **replaces already-displayed notifications on the device**"*
([Expo](https://docs.expo.dev/push-notifications/sending-notifications/)).

**Apple does not document** whether a collapse-replacement re-alerts (sound, banner, screen wake) or
updates silently in place, and does not document what happens if the user already dismissed the
earlier one.

**The other `aps` keys do not help.** All descriptions from
[Apple, *Generating a remote notification*](https://developer.apple.com/documentation/usernotifications/generating-a-remote-notification):

| Key | Apple's words | Removes a delivered alert? |
|---|---|---|
| `thread-id` | *"An app-specific identifier for grouping related notifications."* | No — grouping only |
| `content-available` | *"The background notification flag."* | Only indirectly, by waking the app |
| `mutable-content` | *"the system passes the notification to your notification service app extension **before delivery**"* | No — operates on the in-flight notification |
| `relevance-score` | *"the system uses to **sort** the notifications from your app. The highest score gets featured in the notification summary."* | No |
| `interruption-level` | presentation of the incoming notification | No |
| `stale-date`, `content-state`, `event` | Live Activities | No |
| **`dismissal-date`** | *"The UNIX timestamp that represents the date at which the system ends a Live Activity **and removes it from the Dynamic Island and the Lock Screen**."* | **Yes — and it is the only server-driven lock-screen removal Apple documents anywhere.** **Live Activities only** (`apns-push-type: liveactivity`, `event: "end"`): *"To dismiss the Live Activity from the Lock Screen immediately after it ends, provide a date for `dismissal-date` that's in the past"* ([Apple](https://developer.apple.com/documentation/activitykit/starting-and-updating-live-activities-with-activitykit-push-notifications)) |

**Removal: not achievable from the server. Achievable on-device, unreliably.**

The API is `UNUserNotificationCenter.removeDeliveredNotifications(withIdentifiers:)` (iOS 10.0+) —
*"Removes your app's notifications from Notification Center that match the specified identifiers"*;
*"This method ignores the identifiers of requests whose notifications are not currently displayed in
Notification Center"*
([Apple](https://developer.apple.com/documentation/usernotifications/unusernotificationcenter/removedeliverednotifications(withidentifiers:))).
In `expo-notifications` this is `dismissNotificationAsync(identifier)` /
`dismissAllNotificationsAsync()` ([Expo](https://docs.expo.dev/versions/latest/sdk/notifications/)).

The only unattended trigger is a **silent push**: `aps` containing *only* `content-available: 1`,
`apns-push-type: background`, `apns-priority: 5` — and *"Always use priority `5`. Using priority
`10` is an error."*
([Apple](https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns)).
Apple documents **five independent** reasons that call may never run:

1. *"The system treats background notifications as low priority: you can use them to refresh your
   app's content, but **the system doesn't guarantee their delivery**. In addition, the system may
   throttle the delivery of background notifications if the total number becomes excessive. **The
   number of background notifications allowed by the system depends on current conditions, but
   don't try to send more than two or three per hour.**"*
   ([Apple](https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app))
2. *"**APNs sends a limited number of silent notifications with the `content-available` key.** In
   addition, if the device has already exceeded its power budget for the day, silent notifications
   aren't sent again until the power budget resets, which happens once a day. **These limits are
   disabled when testing your app from Xcode.**"*
   ([Apple](https://developer.apple.com/documentation/usernotifications/troubleshooting-push-notifications)) —
   the last sentence is why this design **always passes manual QA and fails in the field**.
3. Force-quit: *"the system does not automatically launch your app if the user has force-quit it. In
   that situation, the user must relaunch your app or restart the device"*
   ([Apple](https://developer.apple.com/documentation/uikit/uiapplicationdelegate/application(_:didreceiveremotenotification:fetchcompletionhandler:))),
   and *"If something force quits or kills the app, the system discards the held notification."*
4. On-device holding and coalescing: *"the system may hold and delay the delivery of the
   notification"*; *"When the system receives a new background notification, it discards the older
   notification and only holds the newest one"*; *"If the user launches the app, the system
   immediately delivers the held notification."* — so two withdrawals in quick succession collapse
   to one, and the held one only lands when the user does the very thing the push existed to avoid.
5. Low Power Mode: *"Background App Refresh is disabled automatically when a device is operating in
   low-power mode"*
   ([Apple](https://developer.apple.com/documentation/uikit/uiapplication/backgroundrefreshstatus));
   Low Power Mode is *"Pausing discretionary and background activities"*
   ([Apple](https://developer.apple.com/documentation/foundation/processinfo/islowpowermodeenabled)).
   **Apple does not document** in those words that background *pushes* stop in Low Power Mode; do
   not over-read these two pages.

**Notification Service Extension.** An NSE *"modifies the content of a remote notification before
it's delivered"*, requires `mutable-content: 1` plus alert text, has a limited budget then
`serviceExtensionTimeWillExpire()`, and *"You can't modify silent notifications or those that only
play a sound or badge the app's icon"*
([Apple](https://developer.apple.com/documentation/usernotifications/unnotificationserviceextension)).
It can **suppress the notification it is handling** — *"To suppress a notification's alert, create
an empty `UNNotificationContent` object… and pass it to the content handler"* — but **only with the
restricted entitlement `com.apple.developer.usernotifications.filtering`**, which must be applied
for: *"To apply for this entitlement, see
https://developer.apple.com/contact/request/notification-service"*
([Apple](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.usernotifications.filtering)).
Without it the trick is documented to do nothing: *"If the content object doesn't contain any alert
text, the system ignores your modifications and delivers the original notification content."*
([Apple](https://developer.apple.com/documentation/usernotifications/unnotificationserviceextension/didreceive(_:withcontenthandler:))).
**Apple does not document** any NSE capability to remove or alter *previously delivered*
notifications — and an NSE is a native target CNG does not generate.

**Nothing newer.** The UserNotifications changelog
([Apple](https://developer.apple.com/documentation/updates/usernotifications)) has exactly one dated
entry, **June 2024** (offline queue store, collapse-id, Live Activity broadcast). There is no
retraction API in iOS 17, 18 or 26, and no APNs endpoint that is a delete — the documented endpoints
are `POST /3/device/<token>`, `POST /4/broadcasts`, and channel management.

> ⚠️ **A contradiction inside Apple's own docs, recorded and not relied on.** That June 2024 bullet
> reads *"Use an offline queue store to store multiple notifications per bundle ID when a device is
> inactive."* The current sending page and the metrics page both still say the opposite (**one**
> per bundle ID — quoted in §2c). No primary page documents how to opt into a queue store.
> **Do not design against the changelog bullet.**

**Verdict, iOS: not achievable.** "Remove from the lock screen, from the server" has no documented
mechanism for an alert notification. Replacement is achievable and reliable; removal is not.

### 2b. Android / FCM

**`collapse_key` is the wrong tool twice over.**

*"A collapsible message is a message that may be replaced by a new message **if it has yet to be
delivered to the device**"*
([Firebase](https://firebase.google.com/docs/cloud-messaging/customize-messages/collapsible-message-types)) —
it operates in FCM's queue, never in the shade. The REST field says the same:
*"An identifier of a group of messages that can be collapsed, so that only the last message gets
sent **when delivery can be resumed**. A maximum of 4 different collapse keys is allowed at any
given time."* ([Firebase](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages)).

And — the fact that catches most designs — **it does not apply to notification messages at all**:
*"**Notification messages are always collapsible and will ignore the `collapse_key` parameter.**"*

Its other limits: *"For Android, there is a limit of 100 messages that can be stored without
collapsing. If the limit is reached, all stored messages are discarded. When the device is back
online, it receives a special message indicating that the limit was reached"* — surfaced to the app
as `onDeletedMessages()`
([Firebase](https://firebase.google.com/docs/cloud-messaging/android/receive)) — and a per-device
collapsible throttle of *"a burst of 20 messages per app per device, with a refill of 1 message
every 3 minutes"*
([Firebase](https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas)), which `ttl: 0`
bypasses: *"FCM doesn't apply collapsible message throttling to messages with a time to live value
of 0 seconds"*
([Firebase](https://firebase.google.com/docs/cloud-messaging/customize-messages/setting-message-lifespan)).

**`tag` is the replace primitive, and the only field in the whole `Message` resource that touches a
displayed notification.** Verbatim: *"Identifier used to replace existing notifications in the
notification drawer. If not specified, each request creates a new notification. **If specified and a
notification with the same tag is already being shown, the new notification replaces the existing
one in the notification drawer.**"*
([Firebase](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages)). Expo exposes
it verbatim as `tag`.

**Removal: no FCM field exists.** The `Message` resource contains no `cancel`, `dismiss`, `clear` or
`remove`; the only other occurrence of "dismiss" is `sticky`, which is about user taps. The
documented route is a **data-only** message → `FirebaseMessagingService.onMessageReceived` →
`NotificationManager.cancel(tag, id)`
([Android](https://developer.android.com/reference/android/app/NotificationManager)). Through
`expo-notifications` the equivalent is a background notification task —
`Notifications.registerTaskAsync` + `TaskManager.defineTask` — calling `dismissNotificationAsync`.
Expo documents both the mechanism and its ceiling:

> *"Call `registerTaskAsync` to set a callback (task) that runs when a notification is received
> while the app is in foreground, background, or terminated."* … *"When the app is terminated, only
> a Headless Background Notification triggers the task execution. **However, the OS may decide not
> to deliver the notification to your app in some cases (e.g. when the device is in Doze mode on
> Android, or when you send too many notifications — Apple recommends to not send more than two or
> three per hour.**"*
> — [Expo](https://docs.expo.dev/versions/latest/sdk/notifications/)

This is not hypothetical: **Expo's own notification test app does exactly this**, calling
`Notifications.dismissNotificationAsync(taskPayload.notification.request.identifier)` from inside
`BACKGROUND_NOTIFICATION_TASK`
([expo/expo, `apps/notification-tester/src/registerTaskAsync.ts`](https://github.com/expo/expo/blob/main/apps/notification-tester/src/registerTaskAsync.ts)).
So the mechanism exists and is exercised. What it does not have is a delivery guarantee — Expo's own
advice is *"The rule of thumb is to prefer a regular Notification Message if you don't require
running JavaScript in the background."*

Expo's documented delivery matrix makes the split precise:

| Message type | Foreground | Background | Terminated |
|---|---|---|---|
| Notification Message (± data) | listener + JS task | **OS shows it, no JS runs** | **OS shows it, no JS runs** |
| Headless Background Notification | listener + JS task | **JS task runs** | **JS task runs** |

— [Expo](https://docs.expo.dev/push-notifications/what-you-need-to-know/). Read the middle column:
**the only message shape whose retraction code can run is the one whose display code must also run.**

**Four documented obstacles, in order of how much they hurt.**

1. **You cannot cancel a notification you did not post.** Google's delivery table is explicit:
   with a `notification` payload and the app in the background, *"the notification is delivered to
   the device's system tray"* and `onMessageReceived` **is not called**
   ([Firebase](https://firebase.google.com/docs/cloud-messaging/android/receive)). Worse, such
   messages are *proxied*: *"displayed by Google Play services on behalf of the app, **without any
   need to start the app**"*, the default *"for apps using Android Q+ and Google Play services
   version 19054000 or later. Messages sent through HTTP v1 API are proxied"*
   ([Firebase](https://firebase.google.com/docs/cloud-messaging/android-message-priority)).
   **Google does not document the notification id Play services uses**, so the app has nothing to
   pass to `cancel`. The opt-out is `AndroidNotification.proxy = DENY` — **which the Expo Push API
   does not expose.** To make the offer cancellable the app must post it itself from a data-only
   message, which makes the *offer* dependent on the app process.
2. **High-priority data messages that produce no notification get deprioritized.** *"High priority
   messages on Android are meant for time sensitive, user visible content, and should result in
   user-facing notifications. **If FCM detects a pattern in which messages don't result in
   user-facing notifications, your messages may be deprioritized to normal priority or delegated
   for handling by Google Play services. FCM uses 7 days of message behavior when determining
   whether to deprioritize or proxy messages; it makes this determination independently for every
   instance of your application.**"* And Android 13 made it a platform behaviour: *"System now
   downgrades the high priority messages if it detects an app consistently sending high-priority
   messages that don't result in a notification"*
   ([Android 13 behavior changes](https://developer.android.com/about/versions/13/behavior-changes-all)).
   **A withdrawal message is by construction a high-priority message that produces no notification.**
   Google's own advice — *"If your application doesn't always post notifications in response to
   High Priority FCMs, we recommend that you change the priority of these FCMs to `normal`"* — turns
   the retraction into a normal-priority message, which in Doze is *"stored by FCM until the device
   is out of Doze"*. This is a documented, self-defeating loop, not a theoretical risk.
3. **Doze and App Standby.** *"FCM high priority messages let you wake your app to engage the user.
   In Doze or App Standby mode, the system delivers the message and gives the app temporary access
   to network services and partial wakelocks"*; *"Normal priority messages… are delivered during
   the periodic Doze maintenance windows or as soon as the user wakes the device"*
   ([Android](https://developer.android.com/training/monitoring-device-state/doze-standby)). An app
   the user has not opened for **8 days** lands in the `restricted` bucket on Android 13+
   ([Android](https://developer.android.com/topic/performance/appstandby)) — a plausible state for
   a player who joined standby and waited. Note also: *"If the user swipes away the notification
   without tapping on it, the system doesn't consider that action to be an interaction with your
   app."*
4. **Force-stop — documented by Expo, not by Google. OEM restrictions — documented by nobody.**
   **Google's FCM documentation never mentions force-stop**; the nearest Google source is Android
   15's stopped-state change: *"the system also cancels all pending intents when the app enters the
   stopped state"*
   ([Android 15 behavior changes](https://developer.android.com/about/versions/15/behavior-changes-all)).
   Expo, however, states it plainly: *"if the user force-stops the app from device settings, it
   must be manually reopened for notifications to start working (this is a limitation of Android)"*
   ([Expo](https://docs.expo.dev/versions/latest/sdk/notifications/)). Separately, **Google does not
   document anywhere that OEM battery managers can prevent FCM delivery** — only that *"Every
   manufacturer can set their own criteria for how non-active apps are assigned to buckets."* That
   one is real operationally and has no citation; design as if a dismissal may simply never arrive.

Two smaller facts worth carrying: `onMessageReceived` *"should complete within 20 seconds"*
([Firebase](https://firebase.google.com/docs/reference/android/com/google/firebase/messaging/FirebaseMessagingService)),
and a high-priority FCM message does buy an execution window — *"An app is placed on the allowlist
when it handles a task that's visible to the user, such as: Handling a high-priority Firebase Cloud
Messaging (FCM) message"*
([Android](https://developer.android.com/about/versions/oreo/background)). Device-level caps are
generous for one message: *"240 messages per minute and 5,000 messages per hour to a single device"*.

**Verdict, Android: achievable, with a cost ADR-0052 did not price.** Replacement via `tag` is
reliable and needs no app process. True removal works whenever the app is not force-stopped and the
OS chooses to deliver — but only if the offer itself is posted by the app from a data-only message,
and the retraction stream is exactly the pattern Google documents as grounds for deprioritization.

### 2c. When the device was offline at the moment of withdrawal

This is the worst case on both platforms, and it is the one ADR-0052's twelve-hour backstop already
half-anticipates (*"a flat battery on Friday costs a Saturday-morning game"*).

**iOS.** From the sending page:

> *"As a best-effort service, **APNs may reorder notifications you send to the same device
> token**. If APNs can't deliver a notification immediately, it may store the notification for 30
> days or less, depending on the date you specify in the `apns-expiration` header."*
>
> *"**APNs stores only one notification per bundle ID.** When you send multiple notifications to the
> same device for a bundle ID, APNs selects only one notification to store. In most cases, the
> latest notification is stored. **However, this behavior isn't always guaranteed when multiple
> notifications are stored in a short duration.**"*
> — [Apple](https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns)

And from the metrics page: *"APNs persistent storage only stores one notification per application
per device… **Most of the time, it's the last notification sent, but because APNs doesn't have any
ordering guarantees, this isn't always the case.**"* Troubleshooting repeats it: *"APNs queues only
one notification at a time for each device… each new request might overwrite the previous request."*

So for offer A then withdrawal B while offline:

- **B as a replacement alert:** B *usually* wins the single slot and the phone shows only B. Not
  guaranteed. `apns-expiration` must be nonzero or B is dropped: *"If the value is `0`, APNs
  attempts to deliver the notification only once and doesn't store it."*
- **B as a silent push:** the killer case. A and B share the same one-slot-per-bundle-ID store, so
  either B evicts A (the user sees nothing — harmless) or A survives and B is dropped (**the user
  sees a stale offer that never goes away**). **Apple does not document which occurs.** And if B
  does survive, everything in §2a still applies to it.
- **Ordering:** no guarantee, stated three separate times by Apple. A retraction arriving *before*
  the offer it retracts is a documented possibility; it would dismiss nothing, and then the stale
  offer would appear.

**Android.** *"If the device isn't connected to FCM, the message is stored until a connection is
established"*; the default lifetime is *"a maximum period of four weeks"*; `ttl` ranges *"from 0 to
2,419,200 seconds (28 days)"*; *"A `ttl` value of 0 means messages that can't be delivered
immediately are discarded"*; and *"if the device hasn't connected to FCM for more than one month,
FCM still accepts the message but immediately discards it"*
([Firebase](https://firebase.google.com/docs/cloud-messaging/customize-messages/setting-message-lifespan)).

There **is** one genuinely good Android answer, and it only works before delivery: *"If the
`collapse_key` is set, and there's an existing message with the same collapse key and registration
token waiting for delivery, the old message is discarded and then new message takes its place."* So
if the offer never landed, a same-`collapse_key` withdrawal **replaces it in the queue** and the
phone sees only the withdrawal. Three caveats: it requires **data-only** messages (collapse_key is
ignored for notification messages), only **4** distinct collapse keys exist per device so keying
per-offer thrashes, and it does nothing once the offer has landed.

**Ordering on Android is explicitly refused**: *"FCM doesn't guarantee the order of delivery."*
([Firebase](https://firebase.google.com/docs/cloud-messaging/customize-messages/collapsible-message-types)).
There is no sequence field in the `Message` resource, so **any ordering must be carried in the
`data` payload as a version or timestamp and enforced client-side.** Nothing in ADR-0052 or the spec
delta says such a field exists.

**The honest summary:** on both platforms the retraction may arrive late, out of order, or not at
all — and on iOS it may additionally evict the very offer it was meant to retract, which is the one
harmless outcome. The only reliable cleanup is the app being opened, at which point `GET /now` tells
the truth and `dismissAllNotificationsAsync()` can sweep. **That mechanism is free and should exist
regardless of which option is chosen** — it just does not run until the player looks, which is
exactly the window ADR-0052 was covering.

### 2d. Does ADR-0052's silent withdrawal survive?

**It survives only under stated conditions, and on iOS the conditions are not met.**

- *"the card disappears from Now"* — **survives fully.** Server-side projection plus `GET /now`,
  already built by ADR-0038/0054.
- *"the delivered notification is removed from the lock screen"* — **does not survive on iOS**
  as anything better than best-effort cleanup. **Survives on Android** at the price of making the
  offer itself app-process-dependent (§2b obstacle 1) and of sending precisely the message pattern
  Google deprioritizes (obstacle 2).
- *"No second notification"* — **survives as literally written** only if removal is the mechanism.
  Under the quiet-replacement alternative there *is* a second notification, one documented not to
  light the screen or play a sound.

ADR-0052's *"Harder"* section already names the residual risk in the right words — *"Silent
withdrawal can read as a phone glitch."* The research adds that on iOS the more likely field failure
is the opposite one: **the notification that does not vanish**, on a phone whose owner then taps it
and finds the seat gone. That is the exact experience the ADR's hard constraint forbids — *"a seat
that is gone must never be presented as an exceptional card."* The card is safe, because Now
re-reads. The **lock screen is not**, and nothing on this map has said so before.

---

## 3. The 08:00 hold, and the wave latency floor

### Scheduling is a server concern. Nobody else offers it.

- **APNs:** no scheduling. `apns-expiration` sets an *upper* bound on delivery attempts, never a
  lower one. Apple documents no "send at" field.
- **FCM:** no scheduling in the HTTP v1 send API. `ttl` is likewise an upper bound. (The Firebase
  *console* schedules Notifications-composer campaigns; that is a marketing tool, not the send API,
  and it cannot express per-recipient local time.)
- **Expo:** no scheduling field in the Push API
  ([Expo](https://docs.expo.dev/push-notifications/sending-notifications/)).
  `expo-notifications` does expose `scheduleNotificationAsync`, but that is a **local**
  notification composed on the device — which cannot know about a vacancy the device has not been
  told about. ADR-0052 says it exactly: *"a phone cannot set its own alarm for a cancellation it
  has not heard about."*

So the 08:00 hold, the ten-minute wave gap, the one-hour exclusive clock and the twelve-hour
backstop are **all backend scheduling**, and the backend needs a durable timer store. Nothing in
`backend/` provides one: ADR-0038 records that Redis is declared in `pyproject.toml` and runs in
`docker-compose-local.yml` while *"no line of `backend/app/` imports it."* **The scheduler is the
largest unbuilt piece of ADR-0052 and it is entirely ours.** "08:00 **local**" additionally requires
a per-player timezone the backend can read; nothing in the Now set says where that comes from.

### The latency floor for a wave

For 3 devices, then 5 ten minutes later, transport is not the constraint by orders of magnitude.

| Stage | Number | Source |
|---|---|---|
| Expo batch size | ≤100 per request — a wave of 3, or of 5, is **one request** | [Expo](https://docs.expo.dev/push-notifications/sending-notifications/) |
| Expo rate | 600 notifications/second per project | [Expo](https://docs.expo.dev/push-notifications/sending-notifications/) |
| FCM project quota | 600,000 messages/minute (≈10,000/s) | [Firebase](https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas) |
| FCM per-device cap | 240/minute, 5,000/hour | [Firebase](https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas) |
| APNs | **No documented per-second ceiling.** *"APNs allows multiple concurrent streams for each connection, but don't assume a specific number of streams."* | [Apple](https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns) |
| APNs connection discipline | *"Keep your connections with APNs open across multiple notifications; do not repeatedly open and close connections. **APNs treats rapid connection and disconnection as a denial-of-service attack.**"* | [archived APNs guide](https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/CommunicatingwithAPNs.html) |

**Nobody publishes a delivery-latency guarantee, and Expo disclaims an SLA in those words:**
*"**The Expo push notification service does not have an SLA** and the FCM and APNs services also
may have occasional outages."*
([Expo](https://docs.expo.dev/push-notifications/sending-notifications/)). The only figure anybody
offers is soft — *"Most notifications are typically delivered within a few seconds"* — and after
handoff *"the push notification services from Google and Apple follow their policies to deliver the
notification to the device."* Apple's word is *"best-effort service"*. **A few seconds is the
expectation; nothing is the promise, so no number may be designed against.**

Expo also imposes an operational obligation the backend must budget for: *"**You must check your
push receipts.**"* Receipts come from a second endpoint (≤1000 ids per request), *"push receipts are
cleared after 24 hours"*, and *"We recommend checking push receipts 15 minutes after sending."*
Even then, *"Even if a receipt's `status` says `ok`, this doesn't guarantee that the device has
received the message."* The practical consequence for the wave design: **a receipt cannot tell the
scheduler whether wave 1 reached anybody in time to decide about wave 2.** The ten-minute gap is a
timer, not a feedback loop, and nothing available makes it one.

What *is* documented is the shape of the tail, and it is device-side:

- iOS `apns-priority: 10` is the only tier documented as *"send the notification immediately"*; `5`
  is *"based on power considerations"*, `1` is *"prevent awakening the device"*. An **alert** push
  at priority 10 is the fast tier and needs no app wake. A **silent** withdrawal is priority 5 by
  rule — the slow tier, by construction.
- Android `priority: "high"` is required to wake a Doze'd device; normal priority is *"stored by FCM
  until the device is out of Doze"*.

**Practical floor:** the dispatch is one HTTPS request — single-digit milliseconds of our time plus
network. The ten-minute wave gap is a scheduler tick, not a transport constraint. **The real latency
risk is the tail on a Doze'd, Low-Power or Scheduled-Summary device, which nobody bounds** (see §4).
For the open-call case ADR-0052 describes — *"a 21:00 seat freeing at 20:15 still fills by 20:40"* —
the offer should be an alert at priority 10 / `high`, the tier with the fewest documented reasons to
be late.

---

## 4. Permission in context

### Asking late is allowed — and Apple recommends it

Apple documents no restriction on when `requestAuthorization(options:completionHandler:)` (iOS 10+)
is called, and recommends deferring it:

> *"Make the request in a context that helps people understand why your app needs authorization. In
> a task-tracking app that sends reminder notifications, you might make the request after the person
> schedules a first task. **Sending the request in context provides a better experience than
> automatically requesting authorization on first launch**, because people can see the purpose your
> app's notifications serve."*
> — [Apple, *Asking permission to use notifications*](https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications)

The HIG says the same generally: *"Ideally, wait to request permission until people actually use an
app feature that requires access"*; *"Avoid requesting permission at launch unless the data or
resource is required for your app to function"*
([Apple HIG, Privacy](https://developer.apple.com/design/human-interface-guidelines/privacy)).
**ADR-0052's "at first standby join" is precisely the shape Apple describes.**

On **Android 13+ (API 33)**, `POST_NOTIFICATIONS` is a runtime permission and *"your app has
complete control over when the permission dialog is displayed"*
([Android](https://developer.android.com/develop/ui/views/notifications/notification-permission)).
Note the default: *"If a user installs your app on a device that runs Android 13 or higher, **your
app's notifications are off by default**."* Apps targeting 12L (API 32) or lower get the dialog
thrown at them by the system *"the first time your app starts an activity after you create a
notification channel"* — the worse outcome. **The app must target 33+ to ask deliberately.**

### Asking again after a refusal — both platforms say no

**iOS.** *"The first time your app calls the method, the system prompts the person to authorize the
requested interactions… **Subsequent calls to this method don't prompt the person again.**"*
([Apple](https://developer.apple.com/documentation/usernotifications/unusernotificationcenter/requestauthorization(options:completionhandler:))).
The call completes with `granted == false` and no UI. The only recourse is Settings:

| Symbol | Availability |
|---|---|
| `UIApplication.openSettingsURLString` | **iOS 8.0+** ([Apple](https://developer.apple.com/documentation/uikit/uiapplication/opensettingsurlstring)) |
| `UIApplication.openNotificationSettingsURLString` (Swift) | **iOS 16.0+** ([Apple](https://developer.apple.com/documentation/uikit/uiapplication/opennotificationsettingsurlstring)) |
| `UIApplicationOpenNotificationSettingsURLString` (Objective-C constant) | **iOS 15.4+** ([Apple](https://developer.apple.com/documentation/uikit/uiapplicationopennotificationsettingsurlstring)) |

The commonly-quoted "15.4" is the **Objective-C** spelling; the Swift name is iOS 16.

**Android 13+.** *"If the user taps Deny for a specific permission more than once during your app's
lifetime of installation on a device, the user will no longer see the system permissions dialog if
your app requests that permission again. The user's action implies 'don't ask again,' and is
considered a permanent denial."*
([Android](https://developer.android.com/training/permissions/requesting)) — **two denials.**
Harsher for apps targeting ≤32: *"If your app targets 12L or lower and the user taps Don't allow,
even just once, they aren't prompted again until they uninstall and reinstall your app, or you
update your app to target Android 13 or higher."* Swiping the dialog away is not a denial. The
recovery route is `Settings.ACTION_APP_NOTIFICATION_SETTINGS` (API 26+), with
`EXTRA_APP_PACKAGE`
([Android](https://developer.android.com/reference/android/provider/Settings#ACTION_APP_NOTIFICATION_SETTINGS)).

**Consequence for ADR-0052:** *"If permission is refused, no offer is made to that player at all"*
is not merely a product choice — **it is the only behaviour the OS leaves available**, because the
app cannot re-ask its way out. What the app *can* do is offer a route to Settings, from a screen,
never from a re-prompt.

### Reading the current state

`expo-notifications` exposes `getPermissionsAsync()` and `requestPermissionsAsync()`; the iOS option
set is `allowAlert`, `allowBadge`, `allowSound`, `allowCriticalAlerts`, `allowDisplayInCarPlay`,
**`allowProvisional`**, `provideAppNotificationSettings`
([Expo](https://docs.expo.dev/versions/latest/sdk/notifications/)). Underneath,
`UNAuthorizationStatus` has five cases — `notDetermined`, `denied`, `authorized` (all iOS 10),
`provisional` (**iOS 12**), `ephemeral` (**iOS 14**, App Clips)
([Apple](https://developer.apple.com/documentation/usernotifications/unauthorizationstatus)).
Android's read is `NotificationManagerCompat.areNotificationsEnabled()`
([Android](https://developer.android.com/reference/androidx/core/app/NotificationManagerCompat)).

**Three finer iOS reads matter here and none is currently in any spec.** `UNNotificationSettings`
also carries `lockScreenSetting` — *"The setting that indicates whether your app's notifications
appear on a device's Lock screen"* — plus `scheduledDeliverySetting` and `timeSensitiveSetting`
(both **iOS 15**)
([Apple](https://developer.apple.com/documentation/usernotifications/unnotificationsettings)). If
`scheduledDeliverySetting == .enabled` and `timeSensitiveSetting != .enabled`, an ordinary
(`active`) offer **will be held for the Scheduled Summary** — i.e. **that pair is the runtime answer
to "will this player see the offer inside the hour?"** A binary "notifications on/off" gate does not
capture it.

That also means the eligibility signal ADR-0052 needs — permitted or not — is richer than a boolean,
and it has to reach the **server**, because the cascade runs there. Nothing in the contract carries
it today.

### Provisional authorization — a trap for this one message

`allowProvisional` (iOS 12+) grants authorization **without any prompt**: *"the first time you call
this method, it automatically grants authorization"*. The cost is stated in one sentence, and it is
decisive:

> *"**The system delivers provisional notifications quietly — they don't interrupt the person with a
> sound or banner, or appear on the lock screen. Instead, they only appear in the notification
> center's history.** These notifications also include buttons that prompt the person to keep or
> turn off the notification."*
> — [Apple](https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications)

**Not on the lock screen.** ADR-0052's mechanism is *"the delivered notification is removed from the
lock screen"* — under provisional authorization there is nothing on the lock screen to remove, and
nothing there to see the offer on either.

It gets worse on the happy path. If the person presses **Keep**, Apple documents that *"The system
authorizes your app to send notifications, but **it doesn't give your app permission to show alerts,
play sounds, or badge the app icon. Your notification only appears in the notification center
history unless they change their notification settings.**"* **Apple does not document** what
`UNAuthorizationStatus` value results from Keep — read `getNotificationSettings` rather than assume.

For a one-hour exclusive offer this makes the pathology systematic rather than rare: a
provisionally-authorized player holds a seat nobody else can take, does not see it, and the
twelve-hour backstop takes it away — the consequence ADR-0052 already flags as its worst, promoted
from the flat-battery case to the common case. And the cascade would count that player as
*permitted*, which is exactly what ADR-0052's binary assumes means "will be interrupted".

**Apple does not document** whether `interruptionLevel` can override provisional quiet delivery. The
HIG's override table lists only three things Time Sensitive overrides — scheduled delivery, Focus,
Ring/Silent — and provisional quiet delivery is not among them. Treat it as undocumented, not as
"no", and do not design on it.

Blunt framing: **provisional authorization buys reach and spends urgency, and this message is made
entirely of urgency.**

### The Scheduled Summary, and what it would take to escape it

Interruption levels, all **iOS 15+**
([Apple](https://developer.apple.com/documentation/usernotifications/unnotificationinterruptionlevel)),
with the HIG's override table
([Apple HIG, Managing notifications](https://developer.apple.com/design/human-interface-guidelines/managing-notifications)):

| Level | Overrides scheduled delivery | Breaks through Focus | Overrides Ring/Silent |
|---|---|---|---|
| `passive` | No | No | No |
| `active` (**the default**) | No | No | No |
| `timeSensitive` | **Yes** | **Yes** | No |
| `critical` | Yes | Yes | Yes (requires an Apple-approved entitlement) |

So a default-level offer on a phone with Scheduled Summary on **can be held until the summary
fires**, which for a one-hour offer means it expires unseen. Escaping requires
`interruptionLevel: 'time-sensitive'` plus the Time Sensitive Notifications capability.

Two corrections to the common assumption about that capability:

- **`UNAuthorizationOptions.timeSensitive` is deprecated as of iOS 15.0**, in the same release it
  shipped, with the note *"Use time-sensitive entitlement."*
- **Apple publishes no documentation page for
  `com.apple.developer.usernotifications.time-sensitive`.** The only User Notifications entitlements
  with reference pages are `…critical-alerts` and `…filtering`. What *is* primary-source confirmed
  is that **"Time Sensitive Notifications" is listed on Apple's supported-capabilities reference**
  ([Apple](https://developer.apple.com/support/app-capabilities/)) as available to Apple Developer
  Program members and **not** marked development-only — i.e. it is a **self-serve Xcode capability,
  not an approval-gated entitlement** like Critical Alerts. That makes it cheaper than it looks.

But the HIG attaches a rule that bears directly on this message:

> *"**Never use the Time Sensitive interruption level to send a marketing notification.** People may
> have agreed to receive marketing notifications from your app, but such a notification must never
> break through a Focus or scheduled delivery setting."*
>
> *"**Use the Time Sensitive interruption level only for notifications that are relevant in the
> moment.** … make sure the notification is about an event that's happening now or **will happen
> within an hour**."*

An exclusive offer with a one-hour clock fits the hour rule exactly, and is transactional rather
than promotional — a seat the player asked for has become available. Whether ADR-0052's message is
framed that way, and whether App Review would agree, is a decision, not a fact.

---

## 5. What provisioning a human must do — the checklist for [#26](https://github.com/Raketa02/Raketa/issues/26)

Ordered. **👤 = a human at a web console; an agent cannot do it.** **💳 = a paid account.** Nothing
here may be done by an agent on its own initiative — [`CLAUDE.md`](../../../../CLAUDE.md) forbids
creating real credential files, and [`docs/environments.md`](../../../environments.md) governs where
the resulting secrets live.

### A. Prerequisites

1. 👤💳 **Apple Developer Program membership.** *"A paid Apple Developer Account is required to
   generate credentials"* ([Expo](https://docs.expo.dev/push-notifications/push-notifications-setup/)).
   Currently USD 99/year.
2. 👤 **Confirm the Apple account role.** *"On individual Apple Developer accounts, only the Account
   Holder role can generate app signing credentials. On an organization Apple Developer account, the
   Account Holder and Admin roles can always generate app signing credentials, and the App Manager
   role can generate credentials when a user with this role has Access to Certificates,
   Identifiers."*
   ([Expo](https://docs.expo.dev/app-signing/apple-developer-program-roles-and-permissions/))
3. 👤 **An Expo account and an EAS project.** There is no `eas.json` in the repo; `eas init` creates
   the project and the `projectId` that `getExpoPushTokenAsync` requires. **No paid EAS plan is
   needed** — the free tier includes *"15 Android and 15 iOS builds"* per month
   ([Expo pricing](https://expo.dev/pricing)), and the push service itself is free at every tier.

### B. Apple — the APNs key

4. 👤 **Register the bundle identifier** `com.raketa.player` (from
   [`app.config.ts`](../../../../frontend_player/app.config.ts)) as an App ID at
   developer.apple.com. **The Push Notifications capability does not have to be toggled by hand:**
   *"EAS Build automatically synchronizes capabilities on the Apple Developer Console with your
   local entitlements configuration when you run `eas build`"*
   ([Expo](https://docs.expo.dev/build-reference/ios-capabilities/)), and the `expo-notifications`
   plugin writes the `aps-environment` entitlement. Expo notes *"The iOS APNs entitlement is always
   set to 'development'. Xcode automatically changes this to 'production' in the archive generated
   by a release build."* The failure symptom if the key is missing is the string
   `No valid aps-environment entitlement string found`.
5. 👤 **Create an APNs Auth Key (`.p8`), not a certificate.** Expo: *"The default behavior is to use
   the modern approach, but developers may opt-in to the legacy approach by providing a p12
   certificate."* Keys *"do not expire"*, one key works for any number of apps, and *"You can have a
   maximum of 2 APN keys associated with your Apple Developer account"*
   ([Expo](https://docs.expo.dev/app-signing/app-credentials/)). **The two-key cap is the thing that
   bites later** — burn one carelessly and there is one left. Revoking a key breaks push for every
   app using it; device tokens and Expo push tokens are *not* invalidated by rotation.
   - Easiest route: `eas credentials` → iOS → sign in with the Apple ID and let EAS generate and
     store the key. Expo prompts for exactly this during the first iOS build ("Generating a new
     Apple Push Notifications service key"). *"If you are not using EAS Build, run `eas credentials`
     manually."* A human must log in through EAS CLI once; federated/SSO Apple accounts cannot, and
     need an App Store Connect API token with Admin access instead.
   - Manual route: developer.apple.com → Keys → **+** → name → tick **Apple Push Notification
     service** → Configure → Download. *"The Apple Developer console lets you download an APNs Auth
     Key **only when it is created**."*
   - Note: `credentials.json` (local credentials) **has no field for an APNs push key** — local
     credentials cover signing only, so this credential lives with EAS or with the backend, never in
     the repo.
6. 👤 **Register the test device** before the first internal-distribution build, or it installs
   nowhere.

### C. Google — FCM v1

7. 👤 **Create a Firebase project** at console.firebase.google.com
   ([Expo](https://docs.expo.dev/push-notifications/fcm-credentials/)).
8. 👤 **Add an Android app** with package name `com.raketa.player` — it must match
   `android.package` exactly.
9. 👤 **Download `google-services.json`**, place it in the project, and set
   `expo.android.googleServicesFile` in the app config to its path. **This one Expo says may be
   committed** — *"You may commit this file to your repository since it contains public-facing
   identifiers"* ([Expo](https://docs.expo.dev/push-notifications/fcm-credentials/)). It is still
   generated by a human at a console, not by an agent.
   - ⚠️ Documented gotcha worth writing into the ticket verbatim: *"If the API key in
     **google-services.json** (the `client.api_key.current_key` field) is restricted … allow the
     **FCM Registration API** and the **Firebase Installations API**, or leave the key unrestricted.
     Under Application restrictions, use the SHA-1 from Release > Setup > App Integrity > App signing
     key certificate in the Google Play Console, **not your upload key**. A mismatch makes the
     Firebase Installations API return `403 PERMISSION_DENIED` … and your app never receives a push
     token."*
10. 👤 **Generate the service account key.** Firebase console → Project settings → Service accounts →
    *"Click Generate New Private Key, then confirm by clicking Generate Key. Securely store the JSON
    file containing the private key."* **This is the sensitive one** — Expo's instruction is to add
    it to `.gitignore` *"since it contains sensitive data"*, and
    [`CLAUDE.md`](../../../../CLAUDE.md) forbids an agent from creating it. (Reusing an existing
    service account instead requires the **Firebase Cloud Messaging API Admin** IAM role.)
11. 👤 **Upload it to EAS** — `eas credentials` → Android → production → Google Service Account, or
    the EAS dashboard under Credentials → Service Credentials → FCM V1 service account key.
    *(If bare FCM is chosen instead, this JSON becomes a backend secret rather than an EAS
    credential — same artefact, different destination.)* **FCM legacy server keys are not an option:**
    the legacy API was deprecated 2023-06-20 and shut down 2024-07-20, and Expo's push service has
    defaulted to FCM v1 since 2024-05-13, requiring Expo SDK 51 or newer on the client
    ([Expo blog](https://expo.dev/blog/fcm-v1-migration-deadline-changed-to-july-20th)) — SDK 52
    clears that bar.

### D. The app — agent work, listed so the ticket is complete

12. Install `expo-notifications` (+ `expo-device`; and `expo-task-manager` **only if** the
    background-dismissal path is chosen) at the versions SDK 52 pins.
13. Add `'expo-notifications'` to `plugins` in
    [`app.config.ts`](../../../../frontend_player/app.config.ts). The documented plugin properties
    are `icon`, `color`, `defaultChannel`, `sounds` and — the one that matters here —
    **`enableBackgroundRemoteNotifications`** (iOS, default `false`), which is what adds
    `remote-notification` to `UIBackgroundModes`. **Silent-push dismissal on iOS does not work
    without it**, and CNG means it **must** be set as a plugin property, never in a hand-edited
    native file. (`useNextNotificationsApi` is gone — it is absent from the SDK 57 app-config
    schema; do not add it.)
14. Create the Android notification channel at startup with `setNotificationChannelAsync` — it is
    the only lever over sound and importance on Android, and on **Android 13 it must be called
    before `getExpoPushTokenAsync`**, because the OS permission prompt will not appear until at
    least one channel exists
    ([Expo](https://docs.expo.dev/push-notifications/push-notifications-setup/)).
15. `getExpoPushTokenAsync({ projectId })`, with `projectId` read from
    `Constants?.expoConfig?.extra?.eas?.projectId ?? Constants?.easConfig?.projectId`. Register the
    token with the backend and handle rotation (`addPushTokenListener`), per the architecture
    reference's *"support token rotation; synchronize push token lifecycle with backend"*
    ([§121](../../player-app/react_native_expo_production_architecture.md)).
16. Build a **development build** (`eas build --profile development`) — where the Apple credential
    prompt fires, and what ADR-0013 already mandates as the working environment. Push cannot be
    tested in Expo Go on Android at all since SDK 53.

### E. Optional, each a separate human step

17. 👤 **Time Sensitive Notifications capability** — self-serve in Xcode / the developer account
    ([Apple](https://developer.apple.com/support/app-capabilities/)); needed only if the offer must
    escape the Scheduled Summary and Focus. No Apple approval required. Read the HIG rules in §4
    first.
18. 👤 **Notification filtering entitlement** — `com.apple.developer.usernotifications.filtering`,
    **by application only**: *"To apply for this entitlement, see
    https://developer.apple.com/contact/request/notification-service"*. It suppresses an *incoming*
    notification and does not solve retraction, so it is listed for completeness rather than
    recommended.

### Testing hazard to write into the ticket

Apple: *"These limits are disabled when testing your app from Xcode."* Any silent-push-based
withdrawal **will pass every manual test on a development build and fail in production.** If that
path is chosen, the acceptance test must run on a TestFlight or release build. The Android analogue
is the 7-day deprioritization window: a fresh install behaves better than a two-week-old one.

---

## 6. What contradicts an existing record

| Where | The contradiction |
|---|---|
| [ADR-0013](../../../adr/0013-player-app-runtime-architecture.md) "Not adopted now" lists *"`expo-network`/netinfo"* among dependencies *"not added to `package.json`"* | `expo-network` **is** in [`frontend_player/package.json`](../../../../frontend_player/package.json) at `~7.0.5`. Unrelated to push, but the ADR's dependency list has drifted from the manifest |
| [ADR-0052](../../../adr/0052-a-vacancy-is-offered-not-announced.md): *"the delivered notification is removed from the lock screen"* | No documented server-side mechanism on iOS; conditional and self-limiting on Android. See the Verdict |
| ADR-0052's hard constraint: *"a seat that is gone must never be presented as an exceptional card"* | Holds for the **card** (Now re-reads). **Does not hold for the lock screen**, where a stale offer can persist indefinitely on either platform. The constraint was written about the screen and is silently weaker on the notification |
| ADR-0052: *"Apple and Google provisioning is human work an agent cannot do"* | **Confirmed and broader than stated** — beyond credentials, one *capability* (Notification filtering) is granted by Apple only on application. Time Sensitive, by contrast, is **cheaper** than feared: a self-serve capability, no approval |
| ADR-0052: *"Permission is requested in context… If permission is refused, no offer is made"* | **Confirmed, and it is the only option** — neither OS lets an app re-prompt. But the boolean is too coarse on iOS: `scheduledDeliverySetting` + `timeSensitiveSetting` decide whether a one-hour offer is seen inside the hour, and nothing carries them to the server |
| [ADR-0038](../../../adr/0038-now-is-polled-the-push-is-specified-and-deferred.md): *"A backgrounded app learns nothing until next open"* | Still true for everything except this one message — and the **retraction is worse than that**: a backgrounded app may learn nothing even with a push sent |
| [`deltas/shelves-and-offers.md`](../deltas/shelves-and-offers.md) §5: *"Held to 08:00 local"* | Requires a per-player timezone on the server. Nothing in the Now set names its source |
| Apple's own docs | The June 2024 UserNotifications changelog says *"store multiple notifications per bundle ID"*; the sending page and metrics page both still say one. Recorded, not designed against |

---

## 7. What remains open

This is a research ticket. The following are decisions, and this file deliberately makes none of
them.

1. **Which withdrawal mechanism.** Three are on the table and they are genuinely different products:
   - **(a) Silent removal** — ADR-0052 as written. On Android it works when the app can run and the
     offer was posted by the app; on iOS it is best-effort cleanup Apple documents as unguaranteed,
     throttled to *"two or three per hour"*, and invisible in development testing.
   - **(b) Quiet replacement** — same `collapseId`/`tag`, new text (*"that seat has gone"*),
     `interruptionLevel: 'passive'` on iOS and a low-importance channel on Android. Server-driven, no
     app wake, survives force-quit, works from the offline store. Costs a second notification that
     ADR-0052 forbids — one documented not to light the screen or play a sound. It also answers the
     ADR's own *"vanishing reads as a phone glitch"* worry.
   - **(c) Nothing** — leave the stale notification; the tap opens Now and shows the truth. Zero
     mechanism, zero failure modes, worst read, and it is what happens by default whenever (a)
     fails.
2. **Whether `interruptionLevel: 'passive'` actually suppresses the alert on a
   collapse-*replacement*.** Apple documents `passive` for presentation and collapse-id for merging
   and **never documents the two together**. Option (b) rests entirely on this. Answerable only by
   measurement on a real device, and it should be measured before (b) is chosen.
3. **Whether the Android offer becomes a data-only message.** Required for cancellability; costs the
   Play-services proxy path, so the offer itself starts depending on the app process. `proxy: DENY`
   is not reachable through the Expo Push API, which couples this to question 4.
4. **Transport: Expo Push Service or bare APNs/FCM.** Expo is cheaper on both sides and expresses
   everything §2 needs except `proxy` and `notification_priority`. Bare removes a third party from
   the path and unlocks those fields. Reversible on the server; the client library is the same
   either way.
5. **Whether this message claims Time Sensitive.** It is a self-serve capability, so the cost is
   low — but the HIG forbids it for marketing notifications and requires the event to be *"happening
   now or within an hour"*. Whether ADR-0052's offer is transactional or promotional is a framing
   decision with App Review consequences.
6. **Where the scheduler lives.** 08:00-local holds, ten-minute waves, one-hour exclusive clocks and
   twelve-hour backstops all need durable timers. `backend/` has none; ADR-0038 records Redis as
   declared and unused. No ADR governs this and it is the biggest unbuilt piece.
7. **Where the player's timezone comes from**, without which "08:00 local" is undefined.
8. **How permission state reaches the cascade** — and whether it is a boolean or the richer iOS read
   (`lockScreenSetting`, `scheduledDeliverySetting`, `timeSensitiveSetting`). A stale value means a
   seat frozen for somebody who cannot be told.
9. **What the offer notification's identity is.** ADR-0052 says several offers dispatch as **one**
   notification (*"3 seats are free for you"*). One notification retracted when **one** of three
   seats is taken is not a removal — it is a rewrite (*"2 seats are free for you"*). **That is
   option (b)'s shape, not option (a)'s, and it may settle question 1 on its own.**
10. **Whether the payload carries a version.** Both platforms explicitly refuse ordering guarantees.
    Any correct client needs a monotonic version or timestamp in `data` and must ignore stale
    messages. Nothing in ADR-0052 or the spec delta says such a field exists.
11. **What happens on a second device.** A player with a phone and a tablet holds two delivered
    notifications for one offer. Nothing says whether an offer is per-player or per-device, and the
    retraction must reach every token.
12. **Whether the SDK 52 → 57 upgrade is a prerequisite.** `expo-notifications` at the SDK 52 pin is
    five majors behind current. Nothing found says SDK 52 cannot do this; nothing found says Expo
    still supports it.

---

### Provenance

Read on 2026-08-21. **Apple:** `developer.apple.com/documentation/usernotifications`, `…/activitykit`,
`…/bundleresources/entitlements`, `…/uikit`, `…/foundation`, `…/updates/usernotifications`,
`developer.apple.com/design/human-interface-guidelines/{notifications,managing-notifications,privacy}`,
`developer.apple.com/support/app-capabilities/`, and the archived *Local and Remote Notification
Programming Guide*. **Google:** `firebase.google.com/docs/cloud-messaging/*`,
`firebase.google.com/docs/reference/fcm/rest/v1/projects.messages`, and `developer.android.com`
(NotificationManager, Doze/App Standby, background execution limits, behavior changes for Android
13/14/15, notification permission). **Expo:** `docs.expo.dev/push-notifications/*`,
`docs.expo.dev/app-signing/*`, `docs.expo.dev/versions/latest/sdk/notifications`, and
`expo.dev/changelog`.

Repo files read: [`docs/adr/0013`](../../../adr/0013-player-app-runtime-architecture.md),
[`0038`](../../../adr/0038-now-is-polled-the-push-is-specified-and-deferred.md),
[`0052`](../../../adr/0052-a-vacancy-is-offered-not-announced.md),
[`0054`](../../../adr/0054-now-refreshes-when-asked-never-on-a-timer.md),
[`deltas/live-delivery.md`](../deltas/live-delivery.md),
[`deltas/shelves-and-offers.md`](../deltas/shelves-and-offers.md),
[`docs/specs/player-app/react_native_expo_production_architecture.md`](../../player-app/react_native_expo_production_architecture.md) §121,
[`frontend_player/package.json`](../../../../frontend_player/package.json),
[`frontend_player/app.config.ts`](../../../../frontend_player/app.config.ts).

**Nothing was executed.** Unlike [`fit-model.md`](fit-model.md) and
[`state-table.md`](state-table.md), no claim here is tagged `[EXEC]`: there is no device, no
credential and no build, so every statement is documentation. Question 2 of §7 is the one that most
needs measurement before it is trusted.

No file under `backend/` or `frontend_player/` was modified.
