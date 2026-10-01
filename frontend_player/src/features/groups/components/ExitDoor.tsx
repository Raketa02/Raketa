/**
 * **The way out of a group** — *Delete the group* for an Owner alone, *Leave the group* for
 * everybody else, each behind a confirmation sheet, and then the Groups list
 * ([#514](https://github.com/Raketa02/Raketa/issues/514), PRD #500 stories 77–79; play 57–60).
 *
 * **The sheet is the departure's shape** (`LeaveSheet`'s, for its reasons): a real modal whose
 * title names the moment rather than the act, a close named by what it keeps, focus on the title
 * rather than on the destructive act, and the act named once, by the button that does it. What
 * leaving does is said before it happens — an Owner's group passes to whoever has been in it
 * longest, with the requests waiting — and so is the way back in, under the group's rule.
 *
 * **Closing the sheet takes the act back**, even one the network is still holding while the phone
 * is offline — it would otherwise leave the group whenever the connection came back, from whatever
 * page the player was on by then (#529 F5).
 *
 * **The sheet is the surface while the act is in flight**: the door has no line of its own to say
 * a refusal on, so the sheet stays up, its act busy, and a refusal is said on it in words with the
 * act still there. The two that mean the count moved since the page was read — somebody joined an
 * Owner's group, or everybody else left it — re-read the group (`useExitGroup`), and the door
 * under the sheet becomes the one that works.
 *
 * **Success lands on the Groups list**, a `dismissTo` down the stack — the page and anything
 * pushed over it go — with the card already gone and a toast saying what happened.
 *
 * The door is drawn as 6.1's `secondary` button where the mocks draw it in a dark red: red is
 * *ended badly* (1.3) and coral is closed at six (1.2), and the sheet in front of it is what makes
 * it deliberate. Recorded in design-system Part 16 for the product owner.
 */

import { router } from 'expo-router';
import { useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { codeMessage } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';
import { behindOverlay, BottomSheet, Button, Note, theme } from '@/shared/ui';

import type { Group } from '../domain/group';
import { groupExit } from '../domain/groupInfo';
import { useExitGroup } from '../hooks/useGroupWrites';

import { GROUPS_LIST_ROUTE } from './groupRoutes';
import { EXIT_REFUSALS, EXIT_WORDS, exitSheetBody } from './groupsPresentation';

export function ExitDoor({ group }: { readonly group: Group }) {
  const exit = groupExit(group);
  const words = EXIT_WORDS[exit];
  const { act, takeBack } = useExitGroup(group.id);
  const [open, setOpen] = useState(false);
  const door = useRef<View>(null);

  // Closing is *stay*: an act the network is still holding is taken back with it (#529).
  function close() {
    setOpen(false);
    takeBack();
  }

  function confirm() {
    act.mutate(exit, {
      onSuccess: () => {
        router.dismissTo(GROUPS_LIST_ROUTE);
        showToast({ message: words.done, tone: 'ok' });
      },
    });
  }

  return (
    <>
      {/* Hidden from a screen reader while the sheet is up — one label on the door and on the act,
          so the first press reaches the door and the second the act. The sheet is a sibling. */}
      <View ref={door} {...behindOverlay(open)}>
        <Button label={words.door} variant="secondary" size="lg" onPress={() => setOpen(true)} />
      </View>

      <BottomSheet
        visible={open}
        onClose={close}
        title={words.title}
        closeLabel={words.close}
        returnFocusTo={door}
      >
        <View style={s.block}>
          {exitSheetBody(exit, group).map((line) => (
            <Text key={line} style={s.body}>
              {line}
            </Text>
          ))}
        </View>

        {/* Said on the sheet because the door has nowhere to say it. `alert`: it appeared
            without being asked for. */}
        {act.error === null ? null : (
          <View style={s.note}>
            <Note variant="coral" accessibilityRole="alert">
              {codeMessage(EXIT_REFUSALS, act.error)}
            </Note>
          </View>
        )}

        <View style={s.action}>
          <Button
            label={words.door}
            size="lg"
            busy={act.isPending}
            busyLabel={words.busy}
            onPress={confirm}
          />
        </View>
      </BottomSheet>
    </>
  );
}

const s = StyleSheet.create({
  block: { paddingTop: theme.space.sm, gap: theme.space.xs },
  body: { ...theme.type.tiny, color: theme.color.ink },
  note: { paddingTop: theme.space.sm },
  action: { paddingTop: theme.space.md },
});
