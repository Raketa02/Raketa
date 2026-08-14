/**
 * Metro resolves a `.ttf` import to an asset id; TypeScript needs telling.
 *
 * Declared here because `fonts.ts` is the only module that imports one. The alternative —
 * importing from `@expo-google-fonts/<family>` — pulls that package's index, which
 * `require`s every weight and italic it ships, and Metro has no tree-shaking to undo it.
 */
declare module "*.ttf" {
  const asset: number;
  export default asset;
}
