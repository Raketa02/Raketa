/**
 * **What stands in for a room that is not there** — still coming, refused, or gone.
 *
 * Three states with one sentence each, and none of them invents a fourth. It is a component
 * rather than a block repeated in two screens because both doors under `/chats/conversation/…`
 * land on the same nothing: the room and the game behind it are one read, so a room that is not
 * there is not there for either.
 *
 * **The read still in flight draws nothing at all** —
 * [10.1](../../../../docs/design-system.md#101-screen-structure) forbids a spinner in this slot,
 * and a terminal sentence drawn over a room that lands a frame later is the failure that rule is
 * about from the other side.
 *
 * A room that is **gone** never reaches this: `roomIsGone` leaves the screen instead, which is
 * §3.7's own answer. What lands here is a read that failed for some other reason, and a record
 * whose sport this build cannot name.
 *
 * **It takes the top inset, and only that one.** The header it draws stands where the room's
 * will, and a header under the clock for the length of a read is the same bug for the length of
 * a read ([#400](https://github.com/Raketa02/Raketa/issues/400)). The bottom edge is not taken
 * because nothing here reaches it: on the room's own route the bar is down and the room takes
 * that edge once it lands, and behind the *Details* door the bar is drawn and owns it.
 */

import { StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { recoveryMessage, type AppError } from '@/shared/errors';
import { Note, ScreenHeader, theme } from '@/shared/ui';

import { CONVERSATION_SCREEN_TITLE, NO_CONVERSATION_HERE } from './conversationPresentation';

export interface RoomAbsentProps {
  /** True while there is still a read that could produce one. */
  readonly arriving: boolean;
  readonly error: AppError | null;
}

export function RoomAbsent({ arriving, error }: RoomAbsentProps) {
  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      {/* 10.3's header, over the word a room has before it can be named by the people in it —
          the real title is the handles, and there are none to draw yet. */}
      <ScreenHeader title={CONVERSATION_SCREEN_TITLE} onBack={router.back} />

      <View style={s.body}>
        {arriving ? null : error !== null ? (
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(error)}
          </Note>
        ) : (
          <Text style={s.line}>{NO_CONVERSATION_HERE}</Text>
        )}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { paddingHorizontal: theme.size.gutter },
  line: { ...theme.type.tiny, color: theme.color.muted },
});
