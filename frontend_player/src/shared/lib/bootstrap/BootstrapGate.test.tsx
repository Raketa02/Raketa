import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import { Text } from "react-native";
import * as SplashScreen from "expo-splash-screen";

import { BootstrapGate } from "./BootstrapGate";

jest.mock("expo-splash-screen", () => ({
  preventAutoHideAsync: jest.fn(async () => {}),
  hideAsync: jest.fn(async () => {}),
}));

const hideAsync = jest.mocked(SplashScreen.hideAsync);

function deferred() {
  let resolve!: () => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<void>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

/** The splash only leaves once the tree behind it has laid out. */
function layOutTheApp() {
  fireEvent(screen.getByTestId("app-root"), "layout", {
    nativeEvent: { layout: { x: 0, y: 0, width: 390, height: 844 } },
  });
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("BootstrapGate", () => {
  it("shows nothing and keeps the splash up while the sequence runs", async () => {
    const startup = deferred();

    render(
      <BootstrapGate run={() => startup.promise}>
        <Text>the app</Text>
      </BootstrapGate>,
    );

    expect(screen.queryByText("the app")).toBeNull();
    expect(hideAsync).not.toHaveBeenCalled();

    startup.resolve();
    await waitFor(() => expect(screen.getByText("the app")).toBeTruthy());
  });

  it("hides the splash only after the app has laid out", async () => {
    render(
      <BootstrapGate run={async () => {}}>
        <Text>the app</Text>
      </BootstrapGate>,
    );

    await waitFor(() => expect(screen.getByText("the app")).toBeTruthy());
    expect(hideAsync).not.toHaveBeenCalled();

    layOutTheApp();
    expect(hideAsync).toHaveBeenCalledTimes(1);

    layOutTheApp();
    expect(hideAsync).toHaveBeenCalledTimes(1);
  });

  it("shows why the launch failed instead of hanging on the splash", async () => {
    render(
      <BootstrapGate
        run={() =>
          Promise.reject(new Error("Invalid app configuration — EXPO_PUBLIC_API_URL: Required"))
        }
      >
        <Text>the app</Text>
      </BootstrapGate>,
    );

    await waitFor(() => expect(screen.getByText(/EXPO_PUBLIC_API_URL/)).toBeTruthy());
    expect(screen.queryByText("the app")).toBeNull();

    layOutTheApp();
    expect(hideAsync).toHaveBeenCalledTimes(1);
  });
});
