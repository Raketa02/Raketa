/**
 * The design system's primitives, as one import surface.
 *
 * Components are built with the features that need them — this barrel grows as they land,
 * and there is exactly one implementation of each. The prototype kept a second copy of
 * its card, bar and popover in a deck and recorded that they had drifted.
 */

export { Bar, type BarProps } from "./Bar";
export {
  BottomSheet,
  behindSheet,
  type BottomSheetProps,
  type FocusTarget,
} from "./BottomSheet";
export { Button, type ButtonProps, type ButtonSize, type ButtonVariant } from "./Button";
export { Card, PressableCard, type CardProps, type PressableCardProps } from "./Card";
export { CloseControl, type CloseControlProps } from "./CloseControl";
export { Hairline, type HairlineProps } from "./Hairline";
export { Note, type NoteProps, type NoteVariant } from "./Note";
export { ScreenHeader, type ScreenHeaderProps } from "./ScreenHeader";
export { Tag, type TagProps, type TagVariant } from "./Tag";
export { theme, type BandKey, type SportKey, type Theme } from "./theme";
