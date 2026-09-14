/**
 * **The yes screen** — the screen a yes lands on: the faces, one word, two doors
 * ([ADR-0166](../../../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md);
 * [#433](https://github.com/Raketa02/Raketa/issues/433),
 * [#434](https://github.com/Raketa02/Raketa/issues/434)).
 *
 * One screen, two faces, keyed by **which yes** it is. Tomek taps *I'm in* on Ewa's tennis
 * challenge; the reply lands; the phone becomes this. The app's one dark ground with a radial
 * glow, no tab bar, no header, the status bar kept with light content. Reader first: his tile,
 * `vs`, her tile — on a padel four his tile, his partner's (or an outlined empty seat), `vs`,
 * the other two. Under the tiles the one lime word **Challenge!**, whatever standing the reply
 * came back with, and two pills: *Open the chat* and *Later*. Nothing else is drawn — *after
 * accepting, a player already knows who they will play with.*
 *
 * Or Tomek taps *Let's play* on Marek's card, and the reply comes back `mutual` and names a
 * challenge: the same screen opens as **a mutual's**, wherever he is by then — his tile and
 * Marek's, side by side, **no `vs` and no empty seat in every sport** (in tennis they are
 * opponents, in padel partners with a side to fill; the screen says only *you two* and leaves
 * the court's shape to the chat), the word **Matched!**, the same two pills.
 *
 * ## It reads everything it draws from the challenge the cache holds
 *
 * A route parameter is not app state. The challenge screen underneath wrote the accept's reply
 * into the detail entry, and this screen reads that entry as held (`useHeldChallenge`) rather
 * than re-reading it — and after a mutual, where the deck never held it, the same read fetches
 * it on open, and the entrance waits for it. The seats arrive in wire order and are folded by
 * which yes this is: `sidesForReader` into the reader's side first and the reader first within
 * it, with a seat a **person** only when its occupant has accepted — the room's own membership
 * rule, so the picture and the row he lands on next agree — or `pairForReader` into you and
 * everybody else who has said yes, and nobody deciding. A bad or foreign parameter — no
 * challenge, or one the reader holds no accepted seat on — draws nothing and leaves by
 * *Later*'s own door.
 *
 * **The reader's own face costs one read.** The other players' photographs come off the seat
 * cards the challenge carries; nothing carries the reader's own onto a court, so it comes off
 * their own record through `player_record`'s public surface — a new feature edge, held open by
 * the boundary script. The entrance waits for that read (`ready`), so no tile swaps mid-slide,
 * and the poster stands in if it does not answer.
 *
 * ## The awaited door moved here, and runs from the moment the screen opens
 *
 * The bounded rooms-list poll — 750 ms apart, up to 6 s — and the rule that a yes which
 * completed the court waits for the row to carry its game are `useAwaitedChatDoor`'s, unchanged
 * and reused from the conversations feature; what moved is the caller. It runs from open, so by
 * the time most players tap *Open the chat* the room is already known. The button shows *busy*
 * until it is, and is never disabled: past the bound the tap lands on the **Chats list**, where
 * the row will appear. *No door rather than a dead one* — here the door is the list.
 *
 * ## The exits, and where each lands — the same landing from both entries, by two moves
 *
 * - ***Open the chat*** → `[Chats list, the room]`, so back from the room is the Chats list and
 *   never the celebration. After a challenge's yes the list is already under the challenge
 *   screen, and the move is a `dismissTo` down to it; after a mutual's the player is wherever
 *   the reply found them — the deck, another tab — and the move is **the tab's own**: the shell
 *   lays `[Chats list]` down (`openTab`), the Play session ending on the way exactly as it does
 *   on a tab press, and the held deal surviving it in the cache, so Play finds the same deal
 *   when the player comes back. Then the room is pushed over the list.
 * - ***Later***, and Android back → after a challenge's yes the Chats list, the challenge
 *   screen popped with it; after a mutual's a plain **pop** — the deck's next card, or wherever
 *   the player was when the reply landed.
 * - The iOS swipe-back is off on this route (the shell's `Stack.Screen`), because a swipe that
 *   popped to the challenge screen underneath would land somewhere *Later* never does.
 *
 * The screen is one-shot: every exit removes it and nothing re-shows it. *Not this time* never
 * comes here, and the challenge screen's own *Open the chat* arm on later visits is untouched.
 *
 * ## What a listener gets
 *
 * One header whose label is the whole picture as a sentence — *Challenge! You and Ola.N against
 * Kuba.W and Zofia.B*, *and an empty seat* where one is; *Matched! You and Marek.P* — announced
 * once as the faces land, and built from whole handles: the initials over a poster are a
 * drawing and reach no sentence (ADR-0166 §3). The tiles and the `vs` merge into it, and the
 * two doors are the only other elements on the screen.
 *
 * ## The shell stands its bar down, and the screen takes both edges
 *
 * `barStandsDown` names this route beside the room's: the bar is not rendered rather than hidden,
 * so the screen is the whole phone — and, as in the room, the bottom safe-area inset has no
 * owner, so the screen takes it on its own frame. A stack screen, no modal presentation.
 */

import { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { router, usePathname } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useCurrentUser } from '@/features/auth/types';
import {
  CONVERSATION_ROUTE,
  OPEN_THE_CHAT,
  useAwaitedChatDoor,
} from '@/features/conversations/types';
import { useOwnFace } from '@/features/player_record/types';
import { openTab } from '@/features/shell/types';
import { useHardwareBack } from '@/shared/lib/platform';
import { Button, theme, useLiveRegion } from '@/shared/ui';

import type { DetailSeat } from '../domain/challengeDetail';
import {
  pairForReader,
  sidesForReader,
  tilesIn,
  withOwnFace,
  type YesSeat,
  type YesSides,
} from '../domain/yesScreen';
import { useHeldChallenge } from '../hooks/useChallenge';
import { CHATS_LIST_ROUTE, type WhichYes } from '../schemas/routeParams';

import { YesEntrance } from './YesEntrance';
import { YesGround } from './YesGround';
import { YesTile } from './YesTile';
import { LATER, VS, YES_SENTENCE, YES_WORD } from './yesScreenPresentation';

export interface YesScreenProps {
  /** Validated by `schemas/routeParams.ts` before it reaches here; the route does that. */
  readonly challengeId: string;
  /** Which yes this is — a challenge's or a mutual's. Decides the word, the picture and where *Later* lands. */
  readonly which: WhichYes;
}

export function YesScreen({ challengeId, which }: YesScreenProps) {
  const me = useCurrentUser().data?.id;
  const { data: detail, isPending } = useHeldChallenge(challengeId);
  const own = useOwnFace(me);
  const pathname = usePathname();
  const face = FACE[which];

  const sides = detail === undefined || me === undefined ? undefined : face.fold(detail.seats, me);

  /**
   * **What is waited for is the reply's to say**, and the reply is the standing the cache
   * holds: `ON` means this yes completed the court and a game exists, so the wait is for the row
   * to carry it; anything else waits for the room alone.
   */
  const { door, arrived, expired } = useAwaitedChatDoor(
    challengeId,
    detail?.standing === 'ON' ? 'the-room-and-its-game' : 'the-room',
  );

  /**
   * *Open the chat* has been pressed and the room is being waited for. Route-local: it is a fact
   * about a press, and leaving the screen throws it away.
   */
  const [going, setGoing] = useState(false);

  useHardwareBack(face.later);

  // A bad or foreign parameter draws nothing and leaves — once the read has answered, either
  // way — by *Later*'s own door.
  const foreign = !isPending && me !== undefined && sides === undefined;
  useEffect(() => {
    if (foreign) face.later();
  }, [foreign, face]);

  useEffect(() => {
    if (!going) return;
    if (arrived && door !== undefined) {
      face.landOnTheChatsList(pathname);
      router.push({ pathname: CONVERSATION_ROUTE, params: { conversationId: door } });
    } else if (expired) {
      face.landOnTheChatsList(pathname);
    }
  }, [going, arrived, door, expired, face, pathname]);

  // Said once, as the faces land — the same sentence the header is named by.
  const spoken = YES_SENTENCE[which];
  useLiveRegion(sides === undefined || !own.settled ? null : spoken(sides));

  if (sides === undefined || detail === undefined) {
    // The ground alone: the read is still coming, or the screen is about to leave. Nothing
    // else is drawn, because a picture of nobody is not a picture.
    return (
      <View style={s.screen}>
        <StatusBar style="light" />
        <YesGround />
      </View>
    );
  }

  // The reader's own tile carries their own face; every other tile carries what its seat does.
  const picture = withOwnFace(sides, own.photoUrl);
  const size = tilesIn(picture) > 2 ? theme.size.yesTile.doubles : theme.size.yesTile.singles;

  return (
    <View style={s.screen}>
      <StatusBar style="light" />
      <YesGround />
      <SafeAreaView style={s.frame} edges={['top', 'bottom']} testID="yes-screen">
        <YesEntrance
          ready={own.settled}
          label={spoken(sides)}
          left={<Side seats={picture.yours} size={size} />}
          between={face.vs ? <Text style={s.vs}>{VS}</Text> : undefined}
          right={<Side seats={picture.theirs} size={size} />}
          word={<Text style={s.word}>{YES_WORD[which]}</Text>}
          buttons={
            <View style={s.doors}>
              <Button
                label={OPEN_THE_CHAT}
                variant="volt"
                shape="pill"
                size="lg"
                busy={going}
                onPress={() => setGoing(true)}
              />
              <Button label={LATER} variant="onDark" shape="pill" size="lg" onPress={face.later} />
            </View>
          }
        />
      </SafeAreaView>
    </View>
  );
}

/**
 * **What one face of the screen decides** — the fold, the `vs`, and the two moves out. Keyed by
 * which yes it is, below, as a `Record` over the same union the word and the sentence are keyed
 * by, for the same reason: a third yes fails to compile here rather than falling into an `else`
 * arm and drawing the wrong picture or popping to the wrong place.
 */
interface Face {
  /** The picture: the court in two sides, or you and them. */
  readonly fold: (seats: readonly DetailSeat[], playerId: string) => YesSides | undefined;
  /** Whether the small `vs` stands between the halves — the court's, and never the pair's. */
  readonly vs: boolean;
  /** *Later*, the device's back, and where a foreign parameter leaves to. */
  readonly later: () => void;
  /**
   * **The move that puts the Chats list at the bottom of the stack** — the first of *Open the
   * chat*'s two moves, and the whole of its landing past the bound. Handed the pathname the
   * screen is on, which the shell's own move measures a press against.
   */
  readonly landOnTheChatsList: (from: string) => void;
}

const FACE: Readonly<Record<WhichYes, Face>> = {
  /**
   * After *I'm in*: the court in two sides, the `vs` between them, and the Chats list under
   * everything — it is already beneath the challenge screen, so both moves are a pop down to
   * it: a `dismissTo` rather than the shell's reset, which would remount the list and end a
   * Play session that is not running.
   */
  challenge: {
    fold: sidesForReader,
    vs: true,
    later: () => router.dismissTo(CHATS_LIST_ROUTE),
    landOnTheChatsList: () => router.dismissTo(CHATS_LIST_ROUTE),
  },
  /**
   * After a mutual: you and them with nothing between, and the player wherever the reply found
   * them — the deck, the builder, another tab. *Later* is a plain pop — the deck's next card, or
   * wherever that was — and the list where there is nothing to pop to, which is a cold link to
   * the route and not a yes anybody just said. *Open the chat* has no list under it to pop to,
   * so its first move is **the tab's own** (`openTab`): the shell lays `[Chats list]` down and
   * ends the Play session on the way exactly as a press of the column would, while the deal it
   * dealt on stays held in the cache for the next visit — *from the deck this switches the tab;
   * Play keeps its held deck* (ADR-0166 §1).
   */
  mutual: {
    fold: pairForReader,
    vs: false,
    later: () => {
      if (router.canGoBack()) router.back();
      else router.dismissTo(CHATS_LIST_ROUTE);
    },
    landOnTheChatsList: (from) => openTab('chats', from),
  },
};

/** One side of the court — one tile in singles, two a small step apart in doubles. */
function Side({ seats, size }: { readonly seats: readonly YesSeat[]; readonly size: number }) {
  return (
    <View style={s.side}>
      {seats.map((seat, at) => (
        <YesTile key={`seat-${at}`} seat={seat} size={size} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1 },
  frame: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: theme.size.gutter,
  },
  side: { flexDirection: 'row', gap: theme.space.xs },
  // The mock's `vs` measures 15 / 700 — `h2` exactly, a second use recorded — in the on-dark
  // eyebrow grey the record names. Decorative: the sentence says *against*.
  vs: { ...theme.type.h2, color: theme.color.onDarkEyebrow },
  word: { ...theme.type.yesWord, color: theme.color.volt },
  doors: { flexDirection: 'row', gap: theme.space.xs },
});
