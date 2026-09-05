"""The one place that knows where the sibling checkouts live.

`$OTC` is this file's own grandparent -- never inferred from cwd. Everything
else (`apicula`, `nextpnr`, the pipeline docs dir) is resolved from there,
overridable by an environment variable so a different checkout can be pointed
at without editing code.
"""
import os

#: `$OTC` -- the `open-toolchain` checkout carrying `tools/`.
OTC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sibling(name, env):
    """`$OTC/../<name>`, overridable by `$<env>` -- the sibling-checkout layout."""
    return os.environ.get(env) or os.path.join(os.path.dirname(OTC_ROOT), name)


#: Fallbacks tried after the sibling layout, oldest known checkouts last.
_APICULA_FALLBACKS = (
    "/Users/alex/fine-line/.atelier/worktrees/"
    "2026-09-03-open-toolchain-gw5ast-7e84/apicula",
    "/Users/alex/fine-line/apicula",
    "/Users/alex/fine-line/vendor/apicula",
)

#: The pipeline docs dir (documents only) -- `spec-primitives.md` is read from
#: here, never written here.
_PIPELINE_DOCS_FALLBACKS = (
    "/Users/alex/fine-line/.atelier/worktrees/"
    "2026-09-03-open-toolchain-gw5ast-7e84/.atelier/pipelines/"
    "2026-09-03-open-toolchain-gw5ast-7e84",
    "/Users/alex/fine-line/.atelier/pipelines/"
    "2026-09-03-open-toolchain-gw5ast-7e84",
)

#: A checkout is the apicula one only if it carries the harness.
_APICULA_MARKER = ("fuzz", "gw5ast138c", "harness", "evidence.py")


def apicula_candidates():
    return [os.environ.get("FL_APICULA"),
            sibling("apicula", "APICULA_DIR")] + list(_APICULA_FALLBACKS)


def apicula_root():
    """The apicula checkout carrying `fuzz/gw5ast138c/harness/evidence.py`."""
    for candidate in apicula_candidates():
        if candidate and os.path.isfile(os.path.join(candidate, *_APICULA_MARKER)):
            return candidate
    return None


def pipeline_docs_candidates():
    return [os.environ.get("FL_PIPELINE_DOCS")] + list(_PIPELINE_DOCS_FALLBACKS)


def default_spec_primitives():
    """`spec-primitives.md`: `$OTC` first (test fixtures and any checkout that
    carries its own copy beside `tools/`), then the pipeline docs dir."""
    local = os.path.join(OTC_ROOT, "spec-primitives.md")
    if os.path.isfile(local):
        return local
    for docs in pipeline_docs_candidates():
        if not docs:
            continue
        candidate = os.path.join(docs, "spec-primitives.md")
        if os.path.isfile(candidate):
            return candidate
    return local
