#!/usr/bin/env bash
# The public site's tokens rule (ADR-0187 §6): no literal colour or size outside src/ui/tokens.css,
# and src/ui/tokens.ts, which repeats the few the preview image needs because Satori cannot read a
# custom property. Every component reads var(--…). The favicon, src/app/icon.svg, is not scanned:
# the browser draws it on its own, and it can read no custom property.
#
# - In CSS: a hex colour, rgb()/hsl(), or a length in px, rem, em, vw or vh. A media query's
#   width is the one literal CSS allows no variable for, so lines opening with @media are
#   exempt.
# - In TypeScript: the same, written as a string, which is how one reaches an element. Issue
#   numbers in comments (#500) are not colours, which is why TS is only checked inside quotes.
#
# Reports every offending line and fails if there is one.
set -euo pipefail
cd "$(dirname "$0")/.."

css_literal='#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|(^|[^-a-zA-Z0-9_.])[0-9]*\.?[0-9]+(px|rem|em|vw|vh)\b'
ts_literal="['\"\`](#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\(|[0-9]*\.?[0-9]+(px|rem|em|vw|vh))"

found=$(
  {
    grep -rnE "$css_literal" src --include='*.css' | grep -v '^src/ui/tokens\.css:' |
      grep -vE '^[^:]+:[0-9]+:[[:space:]]*@media' || true
    grep -rnE "$ts_literal" src --include='*.ts' --include='*.tsx' |
      grep -vE '^src/(generated/|ui/tokens\.ts:)' || true
  }
)

if [[ -n "$found" ]]; then
  echo "A literal colour or size outside src/ui/tokens.css (and tokens.ts, for the preview image):" >&2
  echo "$found" >&2
  echo "Add a token to src/ui/tokens.css and read it with var(--…)." >&2
  exit 1
fi
echo "tokens: no literal colour or size outside src/ui/tokens.css and src/ui/tokens.ts"
