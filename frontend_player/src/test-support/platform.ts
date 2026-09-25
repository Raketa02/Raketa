/**
 * Hand-written fakes for the four platform ports.
 *
 * Beside `transport.ts` and for the same reason: a test states what the world outside the
 * app does, and everything inside it runs for real. The socket is one such edge; the OS
 * permission dialog and the photo picker are two more, and neither can be driven from a
 * test at all — a native module has no JS implementation underneath it. The **live
 * channel** is the socket again, in its long-lived shape.
 *
 * These are **fakes, not mocks**: they behave like the thing they replace rather than
 * recording that they were called. A test sets what the player will answer and what the
 * device holds, then exercises the screen. That is what makes them worth having — a stub
 * that returns `'granted'` unconditionally proves a screen works only for players who say
 * yes, which is the case that was never in doubt.
 *
 * The device behaviour they model, and which is easy to get wrong by hand:
 *
 * - **A blocked permission cannot be asked for again.** The OS answers instantly and
 *   negatively without showing anything, so `requestPermission()` ignores the answer the
 *   test set. A screen that loops on "ask again" against a blocked permission loops
 *   forever, and this is where that gets caught.
 * - **A refused location produces no fix.** `getCurrentPositionAsync` genuinely fails
 *   without permission, so the real port answers `null` and this one does too.
 * - **A cropping pick answers with one picture.** The OS crop frame is attached to a single
 *   choice, so `allowsEditing` and multi-select cannot both be honoured — a fake that handed
 *   back three from a cropping pick would prove a step works against a picker that does not
 *   exist. See `FakeImagePicking.library`.
 * - **Picking is not gated on the permission**, and deliberately so — the real port does
 *   not consult one either. On iOS the system picker opens without any grant at all, and
 *   a fake that refused would prove a screen handles a refusal the phone never makes. A
 *   test that wants an empty pick says so with `library: []`.
 * - **Neither permission port ever rejects**, because neither real one does.
 * - **A live channel opens saying `connecting` and says nothing more on its own.** The real
 *   one reports `live` when a socket answers and `lost` when one fails, and neither is
 *   something a test should have to wait for — so every transition after the first is the
 *   suite's to drive, and *not live on a cold open* is the default rather than a case
 *   somebody has to remember to set up. See `fakeLiveStream`.
 *
 * Not app code — nothing under `src/` outside tests imports this, so Metro never bundles
 * it.
 */

import type {
  ClipboardPort,
  SharePort,
  FollowLive,
  HapticsPort,
  ImagePickingPort,
  LiveStreamPort,
  LiveStreamStatus,
  LiveTyping,
  LocationFix,
  LocationPort,
  PermissionState,
  PickedImage,
} from '@/shared/lib/platform';

/** The bits every port fake shares: what the state is, and what asking would make it. */
interface FakePermission {
  /** The current permission. Assign to start a test somewhere other than unasked. */
  state: PermissionState;
  /**
   * What the player answers the next time they are asked. Ignored while `state` is
   * `'blocked'`, exactly as the OS ignores it.
   */
  answer: PermissionState;
}

export interface FakeLocation extends LocationPort, FakePermission {
  /**
   * What the device would report. `null` is a device that cannot see the sky — a fix is
   * also withheld whenever the permission is not `'granted'`.
   */
  fix: LocationFix | null;
  /** How many times a fix was asked for, so a test can prove it was asked once. */
  readonly reads: number;
}

export interface FakeImagePicking extends ImagePickingPort, FakePermission {
  /**
   * What the player would choose, in the order they would choose it.
   *
   * A plain pick truncates it to the caller's limit, as a picker does. **A cropping pick
   * answers with one** — the next one not yet handed over — because the real port's crop
   * frame is attached to a single choice, so successive presses walk this list the way a
   * player pressing *Add a photo* three times walks their own library. Assigning to it
   * starts the walk again, which is how a test says *and then they chose that one instead*.
   *
   * Handed over whatever the permission says — see the note above.
   */
  library: readonly PickedImage[];
  /**
   * Whether the picker respects the limit it was opened with. True by default.
   *
   * A caller may **not** assume it does. The limit is handed to a native module and
   * honoured on the far side of a boundary this app does not own, and design-system 6.9
   * requires the step to refuse a surplus in words precisely because the row of three
   * cannot say anything about one on its own. Set this false to be the picker that hands
   * back more than it was asked for, and prove the step survives it.
   *
   * It covers the single-answer rule too: a picker that ignores its limit is a picker that
   * ignores the crop frame's, so `false` hands back the whole list from a cropping pick as
   * well. Both are one boundary this app does not own, and a test that wants a surplus wants
   * it whichever call produced it.
   */
  honoursLimit: boolean;
  /** Every limit the picker was opened with, in order. */
  readonly limits: readonly number[];
  /**
   * The crop ratio each pick asked for, in order — `undefined` where it asked for none.
   *
   * Recorded because *the player is offered a crop frame* is a claim about the step that is
   * otherwise invisible: the pictures come back looking the same either way, so nothing a
   * screen renders could prove the frame was ever opened.
   */
  readonly crops: readonly (readonly [number, number] | undefined)[];
}

/** A permission answer, with the one rule the OS applies itself. */
function settle(fake: FakePermission): PermissionState {
  // A permanently refused permission is not re-asked: the OS resolves it without showing
  // anything, and the state cannot change from inside the app.
  if (fake.state !== 'blocked') fake.state = fake.answer;
  return fake.state;
}

/**
 * A device whose position a test decides.
 *
 * Defaults to the ordinary path — never asked, says yes, knows where it is — so a test
 * that cares about one refusal states only that refusal.
 */
export function fakeLocation(
  initial: Partial<Pick<FakeLocation, 'state' | 'answer' | 'fix'>> = {},
): FakeLocation {
  let reads = 0;

  const fake: FakeLocation = {
    state: initial.state ?? 'undetermined',
    answer: initial.answer ?? 'granted',
    fix:
      initial.fix === undefined
        ? { latitude: 41.3874, longitude: 2.1686, accuracyMetres: 12 }
        : initial.fix,

    get reads() {
      return reads;
    },

    getPermission: async () => fake.state,
    requestPermission: async () => settle(fake),

    readFix: async () => {
      reads += 1;
      return fake.state === 'granted' ? fake.fix : null;
    },
  };

  return fake;
}

/**
 * A photo library a test decides the contents of.
 *
 * Defaults to a player who has not been asked, would say yes, and has no pictures —
 * because "the player picked nothing" is the case a photos screen must survive, and a
 * default that handed one over would hide it.
 */
export function fakeImagePicking(
  initial: Partial<Pick<FakeImagePicking, 'state' | 'answer' | 'library' | 'honoursLimit'>> = {},
): FakeImagePicking {
  const limits: number[] = [];
  const crops: (readonly [number, number] | undefined)[] = [];

  let held: readonly PickedImage[] = initial.library ?? [];
  /** How far a run of cropping picks has walked `held`. Reset whenever it is reassigned. */
  let taken = 0;

  const fake: FakeImagePicking = {
    state: initial.state ?? 'undetermined',
    answer: initial.answer ?? 'granted',
    honoursLimit: initial.honoursLimit ?? true,

    get library() {
      return held;
    },
    set library(pictures: readonly PickedImage[]) {
      held = pictures;
      taken = 0;
    },

    get limits() {
      return limits;
    },
    get crops() {
      return crops;
    },

    getPermission: async () => fake.state,
    requestPermission: async () => settle(fake),

    pickImages: async ({ limit, cropTo }) => {
      limits.push(limit);
      crops.push(cropTo);

      // A picker that does not honour its limit does not honour the crop frame's either:
      // one boundary, one way of being wrong about it.
      if (!fake.honoursLimit) return held;

      // A cropping pick is single-select on both platforms, so it answers with the one
      // picture this run of presses has got to and nothing after it.
      if (cropTo !== undefined) {
        const next = held[taken];
        if (next === undefined) return [];
        taken += 1;
        return [next];
      }

      return held.slice(0, limit);
    },
  };

  return fake;
}

/**
 * A live channel a test decides the fate of.
 *
 * The only fake here whose *far side* is a socket rather than a native module, which changes
 * one thing about how it is used: a suite that does not stub this port still gets a fake
 * rather than the device, because the device implementation would open a real connection.
 * See `onboardingRouter`'s `WithPorts`.
 */
export interface FakeLiveStream extends LiveStreamPort {
  /** The rooms being followed right now, in the order they were opened. */
  readonly following: readonly string[];
  /**
   * Every room ever followed, including a second follow of one already open.
   *
   * *One stream per open conversation, and never a second for the Chats list* is a claim about
   * counts, and a list of the rooms currently open cannot see a stream opened twice and
   * closed once.
   */
  readonly opened: readonly string[];
  /** Say the channel answered. */
  connect: (conversationId: string) => void;
  /** Say the attempt failed, the channel was severed, or there is nothing to connect over. */
  lose: (conversationId: string) => void;
  /** Say the app went to the background and the channel was closed deliberately. */
  background: (conversationId: string) => void;
  /** Deliver a nudge — *this room moved*, which is the whole of what one says. */
  nudge: (conversationId: string) => void;
  /**
   * Deliver a typing frame — who is typing in this room, right now. **An empty list is the
   * clear**, and the server sends one only when the answer changes, never on a tick.
   */
  typing: (conversationId: string, playerIds: LiveTyping['playerIds']) => void;
}

/**
 * A channel that opens, reports `connecting`, and then does exactly what a test tells it.
 *
 * Nothing happens on its own, which is the point: every state this port can be in is one a
 * screen draws differently, and a fake that connected by itself would make *live* the only
 * one a suite could reach without fighting a timer.
 */
export function fakeLiveStream(): FakeLiveStream {
  /** Per room: how to report, and how many follows are open. Kept after the last close. */
  const rooms = new Map<string, FollowLive[]>();
  const opened: string[] = [];

  function tell(conversationId: string, status: LiveStreamStatus): void {
    for (const ask of rooms.get(conversationId) ?? []) ask.onStatus(status);
  }

  const fake: FakeLiveStream = {
    get following() {
      return [...rooms].flatMap(([room, asks]) => asks.map(() => room));
    },
    get opened() {
      return opened;
    },

    follow: (ask) => {
      opened.push(ask.conversationId);
      const asks = rooms.get(ask.conversationId) ?? [];
      asks.push(ask);
      rooms.set(ask.conversationId, asks);

      // The real port says this synchronously, from inside `follow`: a room that has just
      // opened is connecting, and *not live* is not drawn about it.
      ask.onStatus('connecting');

      return () => {
        const open = rooms.get(ask.conversationId) ?? [];
        rooms.set(
          ask.conversationId,
          open.filter((one) => one !== ask),
        );
      };
    },

    connect: (conversationId) => tell(conversationId, 'live'),
    lose: (conversationId) => tell(conversationId, 'lost'),
    background: (conversationId) => tell(conversationId, 'closed'),

    nudge: (conversationId) => {
      for (const ask of rooms.get(conversationId) ?? []) ask.onNudge({ conversationId });
    },

    typing: (conversationId, playerIds) => {
      for (const ask of rooms.get(conversationId) ?? []) {
        ask.onTyping({ conversationId, playerIds });
      }
    },
  };

  return fake;
}

/**
 * The motor, as a test can count it.
 *
 * The one fake here that records rather than behaves, and it is honest about why: a buzz has no
 * state a screen reads back, so the only fact about one is whether it happened and how often.
 * *Exactly one as the word lands, and none under reduced motion* is a claim about a count.
 */
export interface FakeHaptics extends HapticsPort {
  /** Every buzz asked for, in order. Two kinds: the yes screen's success, the deck's light tick. */
  readonly felt: readonly ('success' | 'light')[];
}

export function fakeHaptics(): FakeHaptics {
  const felt: ('success' | 'light')[] = [];
  return {
    get felt() {
      return felt;
    },
    success: () => {
      felt.push('success');
    },
    light: () => {
      felt.push('light');
    },
  };
}

/** One picked image, for a test that needs a picture and does not care which. */
export function pickedImage(overrides: Partial<PickedImage> = {}): PickedImage {
  return {
    uri: 'file:///photos/one.jpg',
    width: 1200,
    height: 1600,
    mimeType: 'image/jpeg',
    fileName: 'one.jpg',
    ...overrides,
  };
}

/**
 * **A clipboard holding what the suite put on it** — Join a group's Paste chip reads it, and a
 * group page's Copy link writes it. Neither rejects, as the device's port never does: nothing on
 * it is `''`, and a write lands unless the suite said the OS refuses it.
 */
export interface FakeClipboard extends ClipboardPort {
  /** What is on the clipboard now. Assign to copy something between two presses. */
  text: string;
  /** Whether a write lands. Set `false` to be the phone that refused one. */
  writable: boolean;
}

export function fakeClipboard(text = ''): FakeClipboard {
  const clipboard: FakeClipboard = {
    text,
    writable: true,
    readText: () => Promise.resolve(clipboard.text),
    writeText: (written) => {
      if (clipboard.writable) clipboard.text = written;
      return Promise.resolve(clipboard.writable);
    },
  };
  return clipboard;
}

/**
 * **A share sheet that records what it was handed** — a group page's Share the link opens it.
 * Every open is kept, in order, and settles at once as though the player closed it: the device's
 * port never rejects, and a dismissal is not something the page answers.
 */
export interface FakeShare extends SharePort {
  /** Every text the sheet was opened with, oldest first. */
  readonly shared: string[];
}

export function fakeShare(): FakeShare {
  const shared: string[] = [];
  return {
    shared,
    shareText: (message) => {
      shared.push(message);
      return Promise.resolve();
    },
  };
}
