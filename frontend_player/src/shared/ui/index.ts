/**
 * The design system's primitives, as one import surface.
 *
 * Components are built with the features that need them — this barrel grows as they land,
 * and there is exactly one implementation of each. The prototype kept a second copy of
 * its card, bar and popover in a deck and recorded that they had drifted.
 */

export {
  AvailabilityGrid,
  type AvailabilityGridCell,
  type AvailabilityGridProps,
  type AvailabilityGridRow,
} from './AvailabilityGrid';
export { Bar, type BarProps } from './Bar';
export { BottomSheet, type BottomSheetProps } from './BottomSheet';
export { Button, type ButtonProps, type ButtonSize, type ButtonVariant } from './Button';
export { Card, PressableCard, type CardProps, type PressableCardProps } from './Card';
export { Chip, type ChipProps } from './Chip';
export { CloseControl, type CloseControlProps } from './CloseControl';
export { ConfidenceRing, type ConfidenceRingProps } from './ConfidenceRing';
export {
  CourtPoster,
  COURT_POSTER_SPACE,
  type CourtPosterFraming,
  type CourtPosterProps,
} from './CourtPoster';
export { DarkCard, type DarkCardProps } from './DarkCard';
export { Hairline, type HairlineProps, type HairlineVariant } from './Hairline';
export { InfoGlyph, type InfoGlyphProps } from './InfoGlyph';
export {
  LevelBar,
  type LevelBarLegend,
  type LevelBarProps,
  type LevelBarVariant,
} from './LevelBar';
export { Note, type NoteProps, type NoteVariant } from './Note';
export {
  PhotoAddTile,
  PhotoPosterTile,
  PhotoRow,
  PhotoTile,
  type PhotoAddTileProps,
  type PhotoPosterTileProps,
  type PhotoRowProps,
  type PhotoTileFoot,
  type PhotoTileProps,
} from './PhotoTile';
export { InfoMark, Popover, type InfoMarkProps, type PopoverProps } from './Popover';
export { QuestionNavigator, type QuestionNavigatorProps } from './QuestionNavigator';
export { RadiusSlider, type RadiusSliderProps } from './RadiusSlider';
export { Row, type RowProps, type RowVariant } from './Row';
export { ScreenHeader, type ScreenHeaderProps } from './ScreenHeader';
export { Tag, type TagProps, type TagVariant } from './Tag';
export { Tick } from './Tick';
export { TickBox, type TickBoxProps } from './TickBox';
export { behindOverlay, useReducedMotion, type FocusTarget } from './overlay';
export { theme, type BandKey, type SportKey, type Theme } from './theme';
