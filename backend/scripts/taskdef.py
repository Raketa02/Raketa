"""``python -m scripts.taskdef`` — the ECS task definition, against the app it runs.

Run from ``backend/``. It reads ``deploy/ecs/taskdef.json`` and asks two questions
of it, both answered by exercising the application rather than by describing it.

  **Would the container start?** The settings object is built out of exactly what
  the file supplies, and its refusals are the verdict (#341).

  **Would the container be killed mid-shutdown?** The container's ``stopTimeout``
  is compared against gunicorn's ``--graceful-timeout`` in
  ``docker/api/startup.prod.sh`` (#345).

  exit 0  every container definition starts, and outlives its own drain
  exit 1  one does not — the report names the variable or the number
  exit 2  it could not run — a file missing, or one that is not readable

**Neither question holds a list or a number of its own, and that is the whole
design.** The obvious way to write the first is to enumerate the variables a
deployment must supply; the obvious way to write the second is to type 30 in
here. Either would make this file *one more place* the same fact is written —
after ``app/core/config.py``, ``docker/api/startup.prod.sh``,
``docs/environments.md`` and the task definition itself — and both defects being
fixed are exactly what happens when those copies disagree and nothing notices.

So the check restates nothing. It **executes the authority**: it hands
``Settings`` what the task definition supplies and lets the refusals speak, and
it reads ``--graceful-timeout`` out of the entrypoint that passes it. A refusal
added to ``config.py`` tomorrow, or a drain window widened in the entrypoint, is
enforced here the same afternoon with nothing to remember to update.

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
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from app.core.config import ConfigurationError, Settings

#: Repository-relative, resolved from this file so the script runs from anywhere.
TASKDEF = Path(__file__).resolve().parents[1] / "deploy" / "ecs" / "taskdef.json"

#: A host that is guaranteed not to resolve. `.invalid` is reserved by RFC 2606
#: for exactly this, so a placeholder that ever escaped into a real deployment
#: would fail loudly at connect time rather than reaching something.
PLACEHOLDER_HOST = "taskdef-check.invalid"

#: The entrypoint that runs in the image the task definition names. The number
#: this check reads out of it — gunicorn's ``--graceful-timeout`` — is **the one
#: that leads**: it is how long the application gives itself to drain, and every
#: other deadline is chosen to outlive it.
STARTUP = Path(__file__).resolve().parents[1] / "docker" / "api" / "startup.prod.sh"

#: What the committed task definition writes where an image tag will go. The
#: deploy workflow substitutes it, so in this repository it marks exactly the
#: container built from this tree — which is the one, and the only one, that runs
#: `STARTUP`. A sidecar added later would carry somebody else's image and its own
#: shutdown behaviour, and holding it to gunicorn's number would be a confident
#: assertion about a process this repository does not build.
BUILD_PLACEHOLDER = "__IMAGE__"

#: How the two files are named in a failure: as a reader would type them, from
#: the repository root rather than from wherever this happens to be running.
TASKDEF_SAID = "backend/deploy/ecs/taskdef.json"
STARTUP_SAID = "backend/docker/api/startup.prod.sh"

#: What Fargate does with a `stopTimeout` nobody set, and the range it accepts.
#: Both are AWS's numbers, not this repository's — the API reference for
#: ContainerDefinition states that an unspecified value defaults to 30 seconds
#: and that valid values for Fargate are 2-120.
#:
#: The default is the reason an *absent* key is a finding rather than a silence:
#: 30 is exactly the graceful timeout, so leaving it out does not mean "no
#: deadline", it means the agent's SIGKILL lands on the same second the gunicorn
#: master would have force-killed its own stragglers.
FARGATE_DEFAULT_STOP_TIMEOUT = 30
FARGATE_MIN_STOP_TIMEOUT = 2
FARGATE_MAX_STOP_TIMEOUT = 120

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
    #: `stopTimeout`, or `None` where the file does not set one — which is not
    #: the same as no deadline. See `FARGATE_DEFAULT_STOP_TIMEOUT`.
    stop_timeout: int | None
    #: `image`, verbatim. Only `BUILD_PLACEHOLDER` identifies this repository's
    #: own container, and only that one runs the entrypoint read below.
    image: str

    @property
    def is_ours(self) -> bool:
        return self.image == BUILD_PLACEHOLDER

    @property
    def supplied(self) -> frozenset[str]:
        return frozenset(self.values) | frozenset(self.secrets)

    @property
    def kill_deadline(self) -> int:
        """Seconds from SIGTERM to SIGKILL, as the agent will actually apply it."""
        if self.stop_timeout is None:
            return FARGATE_DEFAULT_STOP_TIMEOUT
        return self.stop_timeout


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

        stop_timeout = definition.get("stopTimeout")
        if stop_timeout is not None and not isinstance(stop_timeout, int):
            raise Unreadable(
                f"container '{name}' has a stopTimeout that is not an integer: "
                f"{stop_timeout!r}"
            )

        containers.append(
            Container(
                name=name,
                values=values,
                secrets=secrets,
                stop_timeout=stop_timeout,
                image=str(definition.get("image", "")),
            )
        )
    return containers


def read_graceful_timeout(path: Path = STARTUP) -> int:
    """Gunicorn's `--graceful-timeout`, read from the entrypoint that sets it.

    Read rather than restated, for the reason the variable set above is executed
    rather than listed: a number copied into this file would be a second place
    the same fact is written, and the whole subject here is two places that
    disagreed.

    **Comments are cut before matching, and that is not fastidiousness.** The
    entrypoint now carries a paragraph about this very flag directly above it —
    written by the same commit as this function — so a scan of the raw text would
    be one sentence away from reading its own documentation as configuration. A
    `# --graceful-timeout 60 would be wrong` written later is exactly the shape
    that would do it, whether it sits on its own line or after a live one.

    Every live occurrence must agree, rather than the first one winning: two
    different values would mean the entrypoint has two gunicorn invocations, and
    picking one silently is how a check ends up asserting about a process nobody
    runs.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise Unreadable(f"no production entrypoint at {path}") from None

    found = {
        int(hit.group(1))
        for line in (raw.split("#", 1)[0] for raw in text.splitlines())
        if (hit := re.search(r"--graceful-timeout[ \t]+(\d+)", line))
    }

    if not found:
        raise Unreadable(
            f"{path.name} does not pass --graceful-timeout to gunicorn. Either "
            f"the flag moved or the entrypoint changed shape; this check cannot "
            f"guess what the application gives itself to drain."
        )
    if len(found) > 1:
        raise Unreadable(
            f"{path.name} passes --graceful-timeout more than once, with "
            f"different values: {sorted(found)}. Which one the container gets "
            f"depends on which gunicorn actually runs, and this check will not "
            f"guess."
        )
    return found.pop()


def shutdown_deadline(container: Container, graceful: int) -> str | None:
    """Whether the container outlives its own drain. Returns the complaint.

    **Strictly greater, not greater-or-equal.** Equal is the defect #345 was
    filed for rather than a boundary case: the agent's SIGKILL and the gunicorn
    master's own force-kill land on the same second, so the master never reliably
    reaches the line where it reaps its workers and exits. A container that
    exits because it was killed and one that exits because it finished look
    different in exactly one place — the logs nobody reads during an incident.
    """
    if container.stop_timeout is not None:
        outside = (
            container.stop_timeout < FARGATE_MIN_STOP_TIMEOUT
            or container.stop_timeout > FARGATE_MAX_STOP_TIMEOUT
        )
        if outside:
            return (
                f"stopTimeout is {container.stop_timeout}, outside the "
                f"{FARGATE_MIN_STOP_TIMEOUT}-{FARGATE_MAX_STOP_TIMEOUT} seconds "
                f"Fargate accepts. RegisterTaskDefinition rejects this, which is "
                f"a slow way to find out."
            )

    if container.kill_deadline > graceful:
        return None

    if container.stop_timeout is None:
        return (
            f"stopTimeout is not set, so Fargate supplies "
            f"{FARGATE_DEFAULT_STOP_TIMEOUT} — and gunicorn's --graceful-timeout "
            f"is {graceful}. That is a dead heat, not a margin: the agent's "
            f"SIGKILL lands on the same second the master would have force-killed "
            f"its stragglers. Set stopTimeout explicitly, above {graceful}."
        )
    return (
        f"stopTimeout is {container.stop_timeout} and gunicorn's "
        f"--graceful-timeout is {graceful}. The container is killed before the "
        f"application has finished the drain it was given, so a deploy severs "
        f"connections the process had already promised to keep. Raise "
        f"stopTimeout above {graceful} — the graceful timeout leads, and this "
        f"deadline follows it."
    )


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
        graceful = read_graceful_timeout()
    except Unreadable as unreadable:
        print(f"taskdef: {unreadable}", file=sys.stderr)
        return 2

    if not any(container.is_ours for container in containers):
        print(
            f"taskdef: no container in {TASKDEF.name} carries the image "
            f"placeholder {BUILD_PLACEHOLDER}, so this check cannot tell which "
            f"one runs {STARTUP.name}. Refusing rather than holding somebody "
            f"else's image to this repository's shutdown behaviour.",
            file=sys.stderr,
        )
        return 2

    failures: list[list[str]] = []
    status: list[str] = []
    for container in containers:
        supplied = len(container.values) + len(container.secrets)

        refusal = boot(container)
        if refusal is None:
            status.append(
                f"  {container.name}: starts — "
                f"{len(container.values)} environment, "
                f"{len(container.secrets)} secrets, "
                f"APP_ENV={container.values.get('APP_ENV', 'local (default)')}"
            )
        else:
            status.append(
                f"  {container.name}: REFUSED — {supplied} variables supplied"
            )
            failures.append(report(container, refusal))

        if not container.is_ours:
            status.append(
                f"  {container.name}: not this repository's image — "
                f"drain not asserted"
            )
            continue

        # Asked even of a container that would not start, because the two are
        # unrelated edits in unrelated files and reporting one at a time would
        # make somebody run the gate twice to learn both.
        complaint = shutdown_deadline(container, graceful)
        if complaint is None:
            status.append(
                f"  {container.name}: drains — gunicorn is given {graceful}s, "
                f"SIGKILL at {container.kill_deadline}s"
            )
        else:
            status.append(f"  {container.name}: KILLED MID-SHUTDOWN")
            failures.append(
                [
                    f"  Container '{container.name}' is killed before it has "
                    f"finished stopping:",
                    "",
                    f"    {complaint}",
                    "",
                    '    The number that leads is gunicorn\'s '
                    '--graceful-timeout, in',
                    f"    {STARTUP_SAID}. This deadline follows it and never",
                    "    the other way round: a longer drain does not help a "
                    "connection",
                    "    that has already been closed, and it delays the deploy "
                    "for every",
                    f"    other request in the process. Set it in {TASKDEF_SAID}.",
                ]
            )

    if not failures:
        for line in status:
            print(line)
        print()
        print(
            f"OK — every container definition in {TASKDEF.name} starts, "
            f"and outlives its own drain."
        )
        return 0

    for line in status:
        print(line, file=sys.stderr)
    print(file=sys.stderr)
    print(RULE, file=sys.stderr)
    print("  THE TASK DEFINITION DISAGREES WITH THE APPLICATION", file=sys.stderr)
    print(RULE, file=sys.stderr)
    print(file=sys.stderr)
    for lines in failures:
        for line in lines:
            print(line, file=sys.stderr)
        print(file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
