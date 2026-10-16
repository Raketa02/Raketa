/**
 * React Native's focus registry, typed by hand for the one module that reads it.
 *
 * It is not public API. `payments.tsx` is the only importer: it needs the focused input, and it
 * needs to forget a focus without sending a native blur. `blurInput` only forgets — unlike
 * `Keyboard.dismiss()`, it sends nothing to the view.
 */
declare module 'react-native/Libraries/Components/TextInput/TextInputState' {
  const TextInputState: {
    currentlyFocusedInput(): unknown;
    blurInput(textField: unknown): void;
  };
  export default TextInputState;
}
