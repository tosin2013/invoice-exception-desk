"""Versioned local annotation persistence for the follow-up queue.

Owners and notes live in one UTF-8 JSON document keyed by the exact
``(issuer, invoice_id)`` pair. Reads validate the whole store and never write;
writes serialize the complete next document and atomically replace the target.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .queue import build_followup_queue

DEFAULT_ANNOTATION_STORE_PATH = (
    Path(__file__).resolve().parent.parent / "state" / "followup_annotations.json"
)
ANNOTATION_STORE_VERSION = 1

_RECORD_FIELDS = ("issuer", "invoice_id", "owner", "notes")
_DOCUMENT_FIELDS = ("version", "annotations")


class AnnotationError(Exception):
    """Base class for all annotation store and assignment errors."""


class AnnotationStoreUnreadableError(AnnotationError):
    """The store exists but cannot be opened, read, or decoded as UTF-8."""


class AnnotationStoreMalformedError(AnnotationError):
    """The store's JSON or document/record shape is invalid."""


class AnnotationStoreVersionError(AnnotationError):
    """The store declares a version other than the supported integer 1."""


class AnnotationStoreDuplicateIdentityError(AnnotationError):
    """Two store records share the same (issuer, invoice_id) pair."""


class AnnotationStoreWriteError(AnnotationError):
    """The next store could not be durably written and replaced."""


class InvoiceNotAcceptedError(AnnotationError):
    """An assignment targets an identity absent from the accepted set."""


class AnnotationValueTypeError(AnnotationError):
    """An owner or notes value is neither a string nor ``None``.

    The accepted-identity check runs first, so this is raised only for an
    accepted identity. It is raised before the store is loaded or written, so a
    rejected value never creates a store file or modifies an existing one.
    """


def _resolved_path(store_path):
    if store_path is None:
        return DEFAULT_ANNOTATION_STORE_PATH
    return Path(store_path)


def _validate_document(document):
    if not isinstance(document, dict):
        raise AnnotationStoreMalformedError("annotation store is not a JSON object")
    if "version" not in document:
        raise AnnotationStoreMalformedError("annotation store has no version")
    version = document["version"]
    if type(version) is not int:
        raise AnnotationStoreMalformedError("annotation store version is not an integer")
    if version != ANNOTATION_STORE_VERSION:
        raise AnnotationStoreVersionError(
            f"unsupported annotation store version: {version}"
        )
    if set(document) != set(_DOCUMENT_FIELDS):
        raise AnnotationStoreMalformedError(
            "annotation store must contain exactly version and annotations"
        )

    records = document["annotations"]
    if not isinstance(records, list):
        raise AnnotationStoreMalformedError("annotations is not a list")

    annotations = {}
    for raw_record in records:
        if not isinstance(raw_record, dict):
            raise AnnotationStoreMalformedError("annotation record is not an object")
        if set(raw_record) != set(_RECORD_FIELDS):
            raise AnnotationStoreMalformedError(
                "annotation record must contain exactly issuer, invoice_id, owner, notes"
            )
        if any(type(raw_record[field]) is not str for field in _RECORD_FIELDS):
            raise AnnotationStoreMalformedError(
                "annotation record fields must all be strings"
            )
        issuer = raw_record["issuer"]
        invoice_id = raw_record["invoice_id"]
        if not issuer or not invoice_id:
            raise AnnotationStoreMalformedError(
                "annotation record issuer and invoice_id must be non-empty"
            )

        identity = (issuer, invoice_id)
        if identity in annotations:
            raise AnnotationStoreDuplicateIdentityError(
                f"duplicate annotation identity: {identity!r}"
            )
        annotations[identity] = {
            "issuer": issuer,
            "invoice_id": invoice_id,
            "owner": raw_record["owner"],
            "notes": raw_record["notes"],
        }
    return annotations


def load_annotations(store_path=None) -> dict[tuple[str, str], dict[str, str]]:
    """Load and validate the whole store, returning an empty mapping if missing.

    The file is never created or modified here. A missing file is an empty
    annotation set; any unreadable, malformed, unsupported, or duplicate store
    raises its documented error.
    """
    path = _resolved_path(store_path)
    if not path.exists():
        return {}

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AnnotationStoreUnreadableError(
            f"annotation store cannot be read: {path}"
        ) from exc

    try:
        document = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise AnnotationStoreMalformedError(
            f"annotation store is not valid JSON: {path}"
        ) from exc

    return _validate_document(document)


def _fsync_directory(directory):
    if os.name != "posix":
        return
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _write_annotations(annotations, store_path):
    path = _resolved_path(store_path)
    records = []
    for issuer, invoice_id in sorted(annotations):
        annotation = annotations[(issuer, invoice_id)]
        owner = annotation.get("owner") or ""
        if not owner.strip():
            owner = ""
        notes = annotation.get("notes") or ""
        if not owner and not notes:
            continue
        records.append(
            {
                "issuer": issuer,
                "invoice_id": invoice_id,
                "owner": owner,
                "notes": notes,
            }
        )

    document = {"version": ANNOTATION_STORE_VERSION, "annotations": records}
    text = json.dumps(document, ensure_ascii=False, indent=2) + "\n"

    temporary_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(
            prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
        _fsync_directory(path.parent)
    except Exception as exc:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
        raise AnnotationStoreWriteError(
            f"annotation store cannot be written: {path}"
        ) from exc


def _set_field(accepted_identities, issuer, invoice_id, field, value, store_path):
    identity = (issuer, invoice_id)
    if identity not in set(accepted_identities):
        raise InvoiceNotAcceptedError(
            f"invoice identity is not accepted: {identity!r}"
        )

    annotations = load_annotations(store_path)
    annotation = annotations.get(
        identity,
        {"issuer": issuer, "invoice_id": invoice_id, "owner": "", "notes": ""},
    )
    annotation[field] = value

    if not annotation["owner"] and not annotation["notes"]:
        annotations.pop(identity, None)
    else:
        annotations[identity] = annotation
    _write_annotations(annotations, store_path)


def set_owner(
    accepted_identities,
    issuer,
    invoice_id,
    owner,
    *,
    store_path=None,
) -> None:
    """Assign or clear the owner for one accepted identity.

    ``None`` or a whitespace-only owner clears the owner. Notes are preserved.
    An identity that is not currently accepted raises
    :class:`InvoiceNotAcceptedError` before any value validation, and the store
    is never touched. For an accepted identity, an owner that is neither a
    string nor ``None`` raises :class:`AnnotationValueTypeError` before the
    store is read or written.
    """
    identity = (issuer, invoice_id)
    if identity not in set(accepted_identities):
        raise InvoiceNotAcceptedError(
            f"invoice identity is not accepted: {identity!r}"
        )
    if owner is not None and not isinstance(owner, str):
        raise AnnotationValueTypeError(
            f"owner must be a string or None, not {type(owner).__name__}"
        )
    if owner is None:
        normalized = ""
    else:
        normalized = owner if owner.strip() else ""
    _set_field(
        accepted_identities,
        issuer,
        invoice_id,
        "owner",
        normalized,
        store_path,
    )


def set_notes(
    accepted_identities,
    issuer,
    invoice_id,
    notes,
    *,
    store_path=None,
) -> None:
    """Assign or clear notes for one accepted identity.

    ``None`` or ``""`` clears the notes; any other text is preserved exactly,
    including whitespace, newlines, punctuation, and non-ASCII characters. The
    owner is preserved. An identity that is not currently accepted raises
    :class:`InvoiceNotAcceptedError` before any value validation, and the store
    is never touched. For an accepted identity, notes that are neither a string
    nor ``None`` raise :class:`AnnotationValueTypeError` before the store is
    read or written.
    """
    identity = (issuer, invoice_id)
    if identity not in set(accepted_identities):
        raise InvoiceNotAcceptedError(
            f"invoice identity is not accepted: {identity!r}"
        )
    if notes is not None and not isinstance(notes, str):
        raise AnnotationValueTypeError(
            f"notes must be a string or None, not {type(notes).__name__}"
        )
    normalized = "" if notes is None else notes
    _set_field(
        accepted_identities,
        issuer,
        invoice_id,
        "notes",
        normalized,
        store_path,
    )


def attach_annotations(queue, store_path=None) -> list[dict]:
    """Return a new queue with stored owners/notes on exact identity matches.

    Order and positions are preserved. Stored empty strings become ``None``;
    an empty or whitespace-only owner becomes ``None`` while a non-blank owner
    keeps its exact stored text. Records for identities absent from the queue
    are ignored but retained.
    """
    annotations = load_annotations(store_path)
    attached = []
    for item in queue:
        copy = dict(item)
        annotation = annotations.get((item["issuer"], item["invoice_id"]))
        if annotation is None:
            copy["owner"] = None
            copy["notes"] = None
        else:
            owner = annotation["owner"]
            copy["owner"] = owner if owner.strip() else None
            copy["notes"] = annotation["notes"] or None
        attached.append(copy)
    return attached


def followup_queue(import_result, store_path=None) -> list[dict]:
    """Compose the pure queue builder with the annotation attachment step."""
    return attach_annotations(build_followup_queue(import_result), store_path)
