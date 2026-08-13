import { theme } from "@/shared/ui/theme";

import { appFonts } from "./fonts";

/**
 * The design system picks a weight by naming a family. If the theme names a family the
 * bootstrap sequence never loads, that text falls back to the system font on device —
 * visible to a human, invisible to every other test in the suite.
 */
describe("the loaded font families", () => {
  const loaded = Object.keys(appFonts);

  it.each(Object.entries(theme.font.sans))("loads the sans %s weight (%s)", (_weight, family) => {
    expect(loaded).toContain(family);
  });

  it.each(Object.entries(theme.font.mono))("loads the mono %s weight (%s)", (_weight, family) => {
    expect(loaded).toContain(family);
  });

  it("loads nothing the theme does not name", () => {
    const named: string[] = [...Object.values(theme.font.sans), ...Object.values(theme.font.mono)];

    expect(loaded.filter((family) => !named.includes(family))).toEqual([]);
  });
});
