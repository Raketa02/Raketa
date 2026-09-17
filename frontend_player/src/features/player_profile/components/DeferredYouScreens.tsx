/**
 * **The five screens that land with their contract** — Photos, Tags, Intro, Who you play with
 * and Game suggestions, each one `tiny` line saying what it is and that the edit lands with
 * the read that carries the fact.
 *
 * The rows are on the tab because the facts are the player's and the tab is where they read
 * them ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1); the screens are the onboarding steps reused, and the steps need the profile read to
 * carry what they edit — the fields [#466](https://github.com/Raketa02/Raketa/issues/466)
 * added, which this client reads on [#471](https://github.com/Raketa02/Raketa/issues/471)
 * (photos, tags, intro — one piece of work, ADR-0170 §5) and
 * [#472](https://github.com/Raketa02/Raketa/issues/472) (gender and preference, the opt-in).
 * Until then each screen is 10.1's empty state: a title, one present-tense line naming what
 * the screen **is**, and never *coming soon*. The line is `DEFERRED_ROW`'s, keyed with the
 * row's, so the two cannot come apart; the ticket that builds a screen replaces its entry
 * here and its row draws the live line the read then serves.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, Text } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { theme } from '@/shared/ui';

import { DEFERRED_ROW, type DeferredRowKey } from './youProfilePresentation';

/**
 * Which group each of the five was opened from — the eyebrow its screen wears.
 *
 * Read at render and not at load: the shell's surface imports this feature's rows and this
 * file imports the shell's words, and a table built while the shell's module is still
 * evaluating would hold `undefined` where the words go.
 */
function groupOf(row: DeferredRowKey): string {
  return row === 'whoYouPlayWith' || row === 'gameSuggestions'
    ? YOU_COPY.groups.findingPlayers
    : YOU_COPY.groups.onYourCard;
}

function DeferredYouScreen({ row }: { readonly row: DeferredRowKey }) {
  const router = useRouter();

  return (
    <ShellScreen eyebrow={groupOf(row)} title={DEFERRED_ROW[row].title} onBack={router.back}>
      <Text style={s.line}>{DEFERRED_ROW[row].screenLine}</Text>
    </ShellScreen>
  );
}

export const PhotosScreen = () => <DeferredYouScreen row="photos" />;
export const TagsScreen = () => <DeferredYouScreen row="tags" />;
export const IntroScreen = () => <DeferredYouScreen row="intro" />;
export const WhoYouPlayWithScreen = () => <DeferredYouScreen row="whoYouPlayWith" />;
export const GameSuggestionsScreen = () => <DeferredYouScreen row="gameSuggestions" />;

const s = StyleSheet.create({
  line: { ...theme.type.tiny, color: theme.color.muted },
});
