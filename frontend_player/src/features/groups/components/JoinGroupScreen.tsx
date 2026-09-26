/**
 * **Join a group** — a back arrow, the title and one field, and nothing else until something is
 * typed (play 23–37; stories 29–44; #512).
 *
 * **One field for everything**: a club's name or district, a group's name, or a group link pasted
 * out of WhatsApp. **Paste** drops the clipboard into it in one tap; while there is text it
 * becomes **✕**, which clears the text and the answer (stories 30, 31). **Every keystroke asks
 * again** (story 32) — the search hook's note says why nothing is debounced.
 *
 * **Three ways of saying there is nothing**, each its own: a club with no groups says so on its
 * card; a link that leads nowhere is *Nothing at that link*, a dead link rather than a typo; text
 * that matched nothing is *No match for "…"*, quoting what was searched for (stories 34, 37, 38).
 *
 * The field takes the focus as the screen opens (play 23 draws the caret in it): there is one
 * thing to do here, and it is type.
 *
 * **A group link opens it with the link already in the field** (#520, story 46), so the answer under
 * it is that group — exactly as if it had been pasted. Then there is nothing to type, so the keyboard
 * stays down and the group is in view.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useClipboard } from '@/shared/lib/platform';
import { Chip, CloseControl, ScreenHeader, TextField, theme } from '@/shared/ui';

import { searchOutcome } from '../domain/groupRules';
import { useJoinSearch, type ClubSearchState } from '../hooks/useClubSearch';

import { ClubResultCard } from './ClubResultCard';
import { nearTheEnd, SCROLL_EVENT_EVERY_MS } from './pageEnd';
import { ReadFailure } from './ReadFailure';
import { GROUPS_COPY } from './groupsCopy';
import { noMatchFor } from './groupsPresentation';

const COPY = GROUPS_COPY.joinGroup;

export interface JoinGroupScreenProps {
  /** The group link that opened the screen, spelled by the route from the code it checked. */
  readonly link?: string;
}

export function JoinGroupScreen({ link }: JoinGroupScreenProps = {}) {
  const clipboard = useClipboard();
  const [typed, setTyped] = useState(link ?? '');
  const search = useJoinSearch(typed);

  async function paste() {
    const pasted = (await clipboard.readText()).trim();
    if (pasted !== '') setTyped(pasted);
  }

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader title={COPY.title} onBack={() => router.back()} backLabel={COPY.back} />

      <View style={s.field}>
        <TextField
          label={COPY.field}
          labelHidden
          placeholder={COPY.field}
          value={typed}
          onChangeText={setTyped}
          autoFocus={link === undefined}
          autoCorrect={false}
          autoCapitalize="none"
          returnKeyType="search"
          trailing={
            typed === '' ? (
              <Chip
                label={COPY.paste}
                accessibilityLabel={COPY.pasteLabel}
                onPress={() => void paste()}
              />
            ) : (
              <CloseControl accessibilityLabel={COPY.clearLabel} onPress={() => setTyped('')} />
            )
          }
        />
      </View>

      <ScrollView
        contentContainerStyle={s.content}
        keyboardShouldPersistTaps="handled"
        scrollEventThrottle={SCROLL_EVENT_EVERY_MS}
        onScroll={(event) => {
          if (nearTheEnd(event.nativeEvent)) search.loadMore();
        }}
      >
        <Answer search={search} />
      </ScrollView>
    </SafeAreaView>
  );
}

function Answer({ search }: { readonly search: ClubSearchState }) {
  if (search.error !== null && search.answer === undefined) {
    return <ReadFailure error={search.error} onRetry={search.retry} />;
  }

  if (search.answer === undefined) return null;

  const outcome = searchOutcome(search.answer);
  switch (outcome.kind) {
    case 'clubs':
      return (
        <>
          {search.answer.clubs.map((club) => (
            <ClubResultCard key={club.id} club={club} />
          ))}
        </>
      );
    case 'nothing-at-link':
      return <Text style={s.nothing}>{COPY.nothingAtLink}</Text>;
    case 'no-match':
      return <Text style={s.nothing}>{noMatchFor(outcome.text)}</Text>;
  }
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  field: { paddingHorizontal: theme.size.gutter, paddingBottom: theme.space.sm },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  nothing: {
    ...theme.type.tiny,
    color: theme.color.muted,
    textAlign: 'center',
    paddingVertical: theme.space.lg,
  },
});
