"""``python -m scripts.taskdef_boot`` — boot the ECS task definition.

Run from ``backend/``. It reads ``deploy/ecs/taskdef.json``, builds the settings
object out of exactly what that file supplies to the container, and reports what
the application would do with it.

  exit 0  every container definition boots
  exit 1  one does not — the report names the variable
  exit 2  it could not run — no task definition, or one that is not readable

**There is no list of required variables here, and that is the whole design.**
The obvious way to write this check is to enumerate the variables a deployment
must supply and compare the two sets. That would make this file a *fourth* place
the same fact is written — after ``app/core/config.py``, ``docs/environments.md``
and the task definition itself — and the failure being fixed (#341) is precisely
that three such places disagreed for eleven days without anything noticing. So
the check does not ask what is required. It **executes the authority**: it hands
``Settings`` what the task definition supplies and lets the refusals speak. A
refusal added to ``config.py`` tomorrow is enforced here the same afternoon, with
nothing to remember to update.

**What stands in for a secret.** A ``secrets`` entry names a variable whose value
lives in Secrets Manager and is not knowable here — nor should it be; this check
creates nothing and reads nothing from AWS. What it can assert is *presence*:
the container will have that variable set to something. So each secret is
supplied as a placeholder, shaped like the field's own default (a URL stays a
URL) and guaranteed to differ from it, because the shipped default is exactly
what several refusals exist to reject. The limit is worth stating plainly: this
check proves the task definition supplies every variable the application demands,
and cannot prove the *values* behind those ARNs are right.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from app.core.config import ConfigurationError, Settings

#: Repository-relative, resolved from this file so the script runs from anywhere.
TASKDEF = Path(__file__).resolve().parents[1] / "deploy" / "ecs" / "taskdef.json"

#: A host that is guaranteed not to resolve. `.invalid` is reserved by RFC 2606
#: for exactly this, so a placeholder that ever escaped into a real deployment
#: would fail loudly at connect time rather than reaching something.
PLACEHOLDER_HOST = "taskdef-boot-check.invalid"

RULE = "────────────────────────────────────────────────────────────────────────────"


class Unreadable(RuntimeError):
    """The task definition could not be read. Exit 2, never a silent pass."""


@dataclass(frozen=True)
class Container:
    """What one container definition supplies to the process it starts."""

    name: str
    #: `environment` entries — name and value, both committed in the file.
    values: dict[str, str]
    #: `secrets` entries — names only. The values are ARNs into Secrets Manager.
    secrets: tuple[str, ...]

    @property
    def supplied(self) -> frozenset[str]:
        return frozenset(self.values) | frozenset(self.secrets)


def read_taskdef(path: Path = TASKDEF) -> list[Container]:
    """Every container definition in the file, as what it supplies."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Unreadable(f"no task definition at {path}") from None
    except json.JSONDecodeError as bad:
        raise Unreadable(f"{path} is not valid JSON: {bad}") from None

    definitions = document.get("containerDefinitions")
    if not isinstance(definitions, list) or not definitions:
        raise Unreadable(f"{path} defines no containers")

    containers = []
    for index, definition in enumerate(definitions):
        name = definition.get("name") or f"#{index}"
        try:
            entries = definition.get("environment", [])
            values = {e["name"]: str(e["value"]) for e in entries}
            secrets = tuple(s["name"] for s in definition.get("secrets", []))
        except (TypeError, KeyError) as bad:
            raise Unreadable(
                f"container '{name}' has an environment or secrets entry "
                f"without a name and value: {bad}"
            ) from None
        containers.append(Container(name=name, values=values, secrets=secrets))
    return containers


def placeholder(name: str) -> str:
    """Stand in for a secret whose value lives in Secrets Manager.

    When the field's default is a URL the placeholder keeps its scheme, so a rule
    keyed on shape still sees something it recognises; otherwise it is an opaque
    token. It is never *equal* to the default, because "still the shipped
    default" is what several refusals check for.

    **`docs/environments.md` rule 5 says no placeholder hostname is written
    anywhere, and this does not break it.** That rule is about configuration —
    a config file or template naming a host describes infrastructure that is
    supposed to exist, and none does. Nothing here is configuration: this string
    is constructed in memory, reaches no file, and is thrown away with the
    settings object. `.invalid` is reserved by RFC 2606 and cannot resolve, so
    even a copy of it that escaped would fail loudly rather than reach something.
    """
    field = Settings.model_fields.get(name)
    default = field.default if field is not None else None
    if isinstance(default, str) and "://" in default:
        scheme = default.split("://", 1)[0]
        return f"{scheme}://{PLACEHOLDER_HOST}"
    return f"set-from-secrets-manager-{name}"


def boot(container: Container) -> str | None:
    """Construct `Settings` from what this container supplies.

    Returns the refusal, or `None` if the container would start.

    The process environment is scrubbed of every setting name first, and the
    `.env` file is disabled. Both leak in the same direction — they make a
    variable the task definition *omits* look supplied — which is the direction a
    passing check cannot be distinguished from a working one. A laptop with a
    populated `backend/.env` must not get a greener answer than the runner.

    **The variables go into the environment, not into the constructor**, because
    that is the door the container puts them through and the two doors do not
    behave alike. `Settings` forbids an unknown keyword argument and raises; the
    environment source ignores a name it does not recognise, exactly as the real
    process would. A task definition that grows an `OTEL_*` or an AWS variable
    is a container that still boots, and a check that read those as constructor
    arguments would fail the build over one — a false red on a guardrail being
    the surest way to teach people to route around it. Complex fields decode by
    a different path too: `ALLOW_ORIGINS` is `NoDecode` and is split by this
    module's own validator only when it arrives as a string from the environment.
    """
    supplied: dict[str, str] = dict(container.values)
    for secret in container.secrets:
        supplied[secret] = placeholder(secret)

    scrubbed = {k: v for k, v in os.environ.items() if k not in Settings.model_fields}
    restore = dict(os.environ)
    os.environ.clear()
    os.environ.update(scrubbed)
    os.environ.update(supplied)
    try:
        Settings(_env_file=None)
        return None
    except ConfigurationError as refused:
        return str(refused)
    except Exception as bad:  # a value that will not coerce to its field's type
        return f"{type(bad).__name__}: {bad}"
    finally:
        os.environ.clear()
        os.environ.update(restore)


def report(container: Container, refusal: str) -> list[str]:
    """The failure, said in the task definition's own terms.

    The refusal names a variable; whether that variable is *absent from the file*
    or *present with a value the application rejects* decides which of two very
    different edits fixes it, and the settings object has no way to know which.

    **Reading the variable out of the message is a hint, never the verdict.**
    Every refusal in `config.py` opens with the variable it is about — that is a
    documented constraint on refusal messages, not a coincidence — but nothing
    enforces the position. A refusal reworded to open with something else costs
    this function its second paragraph and costs the check nothing: the refusal
    is printed verbatim above it either way, and the exit code is decided by
    whether `Settings` constructed, not by this parse.
    """
    variable = refusal.split(" ", 1)[0].strip(":")
    lines = [
        f"  Container '{container.name}' would not start:",
        "",
        f"    {refusal}",
        "",
    ]
    if variable in Settings.model_fields and variable not in container.supplied:
        lines += [
            f"    The task definition supplies no {variable} — it is in neither",
            "    'environment' nor 'secrets'. Add it. A variable carrying a",
            "    credential belongs in 'secrets', in the same templated shape as",
            "    the entries already there; one that does not belongs in",
            "    'environment' with its value committed.",
        ]
    elif variable in container.values:
        lines += [
            f"    The task definition sets {variable} to "
            f"'{container.values[variable]}' in 'environment'. Change the value.",
        ]
    elif variable in container.secrets:
        lines += [
            f"    The task definition supplies {variable} from Secrets Manager, so",
            "    the value this check stood in for is not the problem — the",
            "    refusal is about something else in the configuration.",
        ]
    return lines


def main() -> int:
    try:
        containers = read_taskdef()
    except Unreadable as unreadable:
        print(f"taskdef boot: {unreadable}", file=sys.stderr)
        return 2

    failures: list[list[str]] = []
    for container in containers:
        refusal = boot(container)
        supplied = len(container.values) + len(container.secrets)
        if refusal is None:
            print(
                f"  {container.name}: boots — "
                f"{len(container.values)} environment, "
                f"{len(container.secrets)} secrets, "
                f"APP_ENV={container.values.get('APP_ENV', 'local (default)')}"
            )
        else:
            print(
                f"  {container.name}: REFUSED — {supplied} variables supplied",
                file=sys.stderr,
            )
            failures.append(report(container, refusal))

    if not failures:
        print()
        print(f"OK — every container definition in {TASKDEF.name} boots.")
        return 0

    print(file=sys.stderr)
    print(RULE, file=sys.stderr)
    print("  THE TASK DEFINITION CANNOT BOOT", file=sys.stderr)
    print(RULE, file=sys.stderr)
    print(file=sys.stderr)
    for lines in failures:
        for line in lines:
            print(line, file=sys.stderr)
        print(file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
