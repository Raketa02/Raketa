/**
 * The onboarding feature's only public surface.
 *
 * `src/app/` and other features import from here and from nowhere else inside this
 * folder — ESLint blocks the deep paths. Anything not re-exported below is an internal
 * detail this feature is free to change.
 */

export { DataScreen } from './components/DataScreen';
export { DoneScreen } from './components/DoneScreen';
export { EntryUnavailableScreen } from './components/EntryUnavailableScreen';
export { QuestionScreen } from './components/QuestionScreen';
export { ResultScreen } from './components/ResultScreen';
export { ReviewScreen } from './components/ReviewScreen';
export { SportsPickerScreen } from './components/SportsPickerScreen';
export { WelcomeScreen } from './components/WelcomeScreen';

export type { SkillRating } from './domain/SkillRating';

export { onboardingKeys } from './hooks/onboardingKeys';

/**
 * What this player is rated at, and the two spellings of a sport.
 *
 * All three are read by **other features**, and each is here for the same reason: onboarding
 * is where a rating is made and where the wire's `PADEL` first met this app's `padel`, so a
 * second table or a second query key elsewhere would be a second answer to a question this
 * feature already owns. `sport.ts`'s own rule is that *the two spellings meet in `mappers/`,
 * and only there* — singular, which is what makes this a re-export rather than a promotion.
 *
 * The callers today are Play's sport chips (`useSkillRatings`, `toWireSport` on the search
 * request) and the Player profile's surface read (`toSport` over the declaration map).
 */
export { useSkillRatings } from './hooks/useSkillRatings';
export { toSport, toWireSport } from './mappers/onboardingMappers';

/**
 * What a sport is called, and the colour it wears.
 *
 * Presentation the wire does not carry, decided here because onboarding drew the first sport.
 * Play quotes the name in two places — the chip row, and `UPDATE_PLAY_INTENT`'s *"your last
 * five {sport} searches"* — and a copy deck quoting a name is never a second table of names
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §1).
 */
export { sportColour, sportLabel, sportShortLabel } from './components/sportPresentation';

/**
 * The four Band names, and which of the four a served name refers to.
 *
 * Presentation the wire does not carry, decided here because onboarding drew the first Level
 * bar. The **record sheet is the second**
 * ([#384](https://github.com/Raketa02/Raketa/issues/384)) and it draws the same bar: the four
 * labels beneath it and the key that highlights one of them are a fact about the *vocabulary*
 * rather than about either screen, so a second table would be a second answer to a question
 * this feature already owns — `sportLabel`'s own argument, one row down.
 *
 * **The edges are not here and must never be.** They are deliberately uneven, they were wrong
 * once already, and they travel on the response; what a name maps to is which segment lights
 * up, and a band this build has never heard of gets no colour rather than a guessed one.
 */
export { BAND_NAMES, bandPresentation, type BandPresentation } from './components/bandPresentation';

/**
 * **The result card, drawn once per rating on the Skill passport**
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2): `Verdict` is the dark card the result screen draws, unchanged, and the passport puts a
 * sport tag and a status chip across its top. The explainers and the pressed-mark shape travel
 * with it because the passport draws the card's popover, one for every card, as the result
 * screen draws its own. `ratingStatusLabel` is the chip's word and the card's row, cited.
 */
export {
  Verdict,
  VerdictPopover,
  useVerdictExplainer,
  type Explaining,
  type RatingVerdict,
  type VerdictProps,
} from './components/Verdict';
export { ratingStatusLabel } from './components/bandPresentation';
export { useSports } from './hooks/useSports';

/**
 * The entry gate. The *decision* is exported, never the redirect: where a player belongs
 * is this feature's rule, and which route expresses it is the routing layer's.
 */
export {
  useEntryDecision,
  type EntryDecision,
  type EntryUnavailable,
} from './hooks/useEntryDecision';

/**
 * A walk through onboarding is over when the player is in the app. The gate is the one
 * place that knows they are, so it is the one place that says so — see the hook for why
 * this is the definition rather than a convention. **It hands the gate where the pass
 * began**, because a pass begun at the Skill passport ends on the passport
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3), and which route that is belongs to the route file that lands it.
 */
export { useEndOnboardingPass, type PassLanding } from './hooks/useEndOnboardingPass';
export type { PassOrigin } from './domain/onboardingPass';

/**
 * **The second door into the pass** — the Skill passport's *Add a sport* (ADR-0179 §3). The
 * chip starts the sport's assessment through the picker's own start, begins a pass of that
 * one sport at the question route, and the pass ends back on the passport. The act crosses
 * the surface; the store does not.
 */
export { useAddASport, type AddASport } from './hooks/useAddASport';
export { STARTING_LABEL } from './components/startPresentation';

/**
 * Whether a link may drop a player straight into a sport's questionnaire. A pass has two
 * doors — the picker and the passport's chip — and a link is neither: one naming a sport
 * outside the running pass sends the player to welcome rather than into the middle of a
 * flow with nothing honest to show.
 */
export { useOnboardingAdmission, type OnboardingAdmission } from './hooks/useOnboardingAdmission';

/** Route params are untrusted input, so the route that reads them validates them here. */
export { parseAssessmentRouteParams, type AssessmentRouteParams } from './schemas/routeParams';
