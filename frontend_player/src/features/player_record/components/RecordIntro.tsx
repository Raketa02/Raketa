/**
 * **Their intro, as the record draws it** — one line they wrote, inside the drawing's own curly
 * quotation marks (`introLine`), `muted`, and **upright**: this app loads no italic Archivo, and a
 * `fontStyle` on a custom family is ignored on Android and synthesised on iOS, so the marks carry
 * *their words* rather than a slant (the record header's note). Never truncated.
 *
 * The record's header draws it under the nickname; **the vibe sheet** (#803; the Home rows screens
 * §6.3, *as the record draws it*) under the photos — one drawing, so the two never differ.
 */

import { StyleSheet, Text } from 'react-native';

import { theme } from '@/shared/ui';

import { introLine } from './recordPresentation';

export function RecordIntro({ intro }: { readonly intro: string }) {
  return <Text style={s.intro}>{introLine(intro)}</Text>;
}

const s = StyleSheet.create({
  // The deck card's role for the same line, on paper instead of over a photograph: a sentence to
  // read rather than small print, and in `muted` because it is what they said and not what the
  // platform measured.
  intro: { ...theme.type.rlLabel, color: theme.color.muted },
});
