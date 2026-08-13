import { bootstrapApp, type BootstrapSteps } from "./bootstrapApp";

function deferred() {
  let resolve!: () => void;
  const promise = new Promise<void>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

describe("bootstrapApp", () => {
  it("does not resolve until the fonts have loaded", async () => {
    const fonts = deferred();
    let resolved = false;

    const steps: BootstrapSteps = {
      validateConfig: () => {},
      loadFonts: () => fonts.promise,
    };

    const run = bootstrapApp(steps).then(() => {
      resolved = true;
    });

    await Promise.resolve();
    expect(resolved).toBe(false);

    fonts.resolve();
    await run;
    expect(resolved).toBe(true);
  });

  it("validates config before spending a launch on fonts", async () => {
    const order: string[] = [];

    await bootstrapApp({
      validateConfig: () => {
        order.push("config");
      },
      loadFonts: async () => {
        order.push("fonts");
      },
    });

    expect(order).toEqual(["config", "fonts"]);
  });

  it("fails when the config does, without loading fonts", async () => {
    const loadFonts = jest.fn(async () => {});

    await expect(
      bootstrapApp({
        validateConfig: () => {
          throw new Error("EXPO_PUBLIC_API_URL: Required");
        },
        loadFonts,
      }),
    ).rejects.toThrow("EXPO_PUBLIC_API_URL: Required");

    expect(loadFonts).not.toHaveBeenCalled();
  });
});
