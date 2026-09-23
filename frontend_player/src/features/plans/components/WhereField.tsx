/**
 * **Where** — a capped one-line box on 6.13's field, and the one slot that needs a control beside
 * it.
 *
 * A day and an hour are taps; a place is typed, so something has to say *this is what I meant*.
 * That control is what the write hangs off, and it is closed on a box that could not be recorded
 * — the rule being `mayRecordPlace`'s rather than this file's, because the control that closes and
 * the act that refuses are two readers of one question.
 *
 * ## It is a note and never a court
 *
 * ADR-0144 refuses, in writing: **no id, no lookup, no autocomplete, no reuse, no geocode**, and
 * nothing anywhere reads it. So there is no suggestion list under this box and never will be —
 * one club will be spelled four ways and nothing will notice, which is what refusing a venue
 * record costs and what keeps *the court* out of a build with no booking, no inventory and no
 * owner.
 *
 * ## The cap is drawn as a refusal rather than as a `maxLength`
 *
 * A `maxLength` would swallow the tail of a paste, and the server's own words about this field are
 * that neither an empty value nor an over-long one is silently fixed: *a shortened note is one the
 * person who typed it believes they wrote whole, in front of the other people on the court.* So
 * the box takes everything, the sentence under it says what is wrong, and the control stays shut
 * until it is not. That is the opposite of the composer one feature over, and the difference is
 * that **this cap is a number this client knows**: the message cap is deliberately off the wire,
 * so a client guessing at one would be inventing the very refusal it was trying to pre-empt.
 *
 * `autoCorrect` and `autoCapitalize` are left at the platform's defaults, because this is prose a
 * person writes rather than an identifier — and `autoComplete` is **off**: there is nothing on a
 * phone's list of saved values that is a place four people agreed to meet.
 */

import { StyleSheet, View } from 'react-native';

import { Button, TextField, theme } from '@/shared/ui';

import { mayRecordPlace, tidyPlace, PLACE_CAP } from '../domain/slots';

import {
  PLACE_FIELD_LABEL,
  PLACE_PLACEHOLDER,
  PLACE_TOO_LONG,
  RECORD_PLACE,
} from './planPresentation';

export interface WhereFieldProps {
  readonly written: string;
  readonly onChange: (written: string) => void;
  readonly onRecord: () => void;
}

export function WhereField({ written, onChange, onRecord }: WhereFieldProps) {
  const tooLong = tidyPlace(written).length > PLACE_CAP;

  return (
    <View style={s.body}>
      <TextField
        label={PLACE_FIELD_LABEL}
        placeholder={PLACE_PLACEHOLDER}
        value={written}
        onChangeText={onChange}
        autoComplete="off"
        {...(tooLong ? { error: PLACE_TOO_LONG } : {})}
      />

      <Button label={RECORD_PLACE} disabled={!mayRecordPlace(written)} onPress={onRecord} />
    </View>
  );
}

const s = StyleSheet.create({
  body: { gap: theme.space.sm, paddingTop: theme.space.sm },
});
