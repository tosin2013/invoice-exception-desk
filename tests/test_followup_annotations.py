"""Stage 2 annotation store, assignment, and queue attachment contract."""

import json
from datetime import date
from pathlib import Path

import pytest

from invoice_desk import (
    ANNOTATION_STORE_VERSION,
    DEFAULT_ANNOTATION_STORE_PATH,
    AnnotationError,
    AnnotationStoreDuplicateIdentityError,
    AnnotationStoreMalformedError,
    AnnotationStoreUnreadableError,
    AnnotationStoreVersionError,
    AnnotationStoreWriteError,
    AnnotationValueTypeError,
    InvoiceNotAcceptedError,
    accepted_invoice_identities,
    attach_annotations,
    build_followup_queue,
    followup_queue,
    import_invoices,
    load_annotations,
    set_notes,
    set_owner,
)
from invoice_desk import annotations as annotations_module

AS_OF = date(2026, 10, 15)
ROOT = Path(__file__).resolve().parents[1]
HEADER = "issuer,invoice_id,issue_date,due_date,amount_cents,currency,paid_cents"
REQUIRED_FIELDS = ("issuer", "invoice_id", "owner", "notes")


def frozen_result():
    return import_invoices((ROOT / "data/invoices.csv").read_text(encoding="utf-8"), AS_OF)


def imported(*rows):
    return import_invoices("\n".join([HEADER, *rows]), AS_OF)


def invoice(issuer, invoice_id, balance=100, paid=0):
    return f"{issuer},{invoice_id},2026-01-01,2026-01-01,{balance + paid},USD,{paid}"


def store_path(tmp_path):
    return tmp_path / "followup_annotations.json"


def write_document(path, document):
    path.write_text(json.dumps(document), encoding="utf-8")


def record(issuer="Acme Cleaning Co", invoice_id="INV-1001", owner="", notes=""):
    return {
        "issuer": issuer,
        "invoice_id": invoice_id,
        "owner": owner,
        "notes": notes,
    }


def without_annotations(queue):
    return [
        {key: value for key, value in item.items() if key not in ("owner", "notes")}
        for item in queue
    ]


def test_missing_store_is_empty_and_creates_nothing(tmp_path):
    path = store_path(tmp_path)
    result = frozen_result()

    assert load_annotations(path) == {}
    queue = followup_queue(result, path)

    assert queue == build_followup_queue(result)
    assert all(item["owner"] is None and item["notes"] is None for item in queue)
    assert not path.exists()
    assert list(tmp_path.iterdir()) == []


def test_default_path_and_error_hierarchy():
    assert DEFAULT_ANNOTATION_STORE_PATH == (
        ROOT / "state" / "followup_annotations.json"
    )
    assert ANNOTATION_STORE_VERSION == 1
    for error in (
        AnnotationStoreUnreadableError,
        AnnotationStoreMalformedError,
        AnnotationStoreVersionError,
        AnnotationStoreDuplicateIdentityError,
        AnnotationStoreWriteError,
        AnnotationValueTypeError,
        InvoiceNotAcceptedError,
    ):
        assert issubclass(error, AnnotationError)


def test_load_missing_and_valid_empty_store(tmp_path):
    assert load_annotations(store_path(tmp_path)) == {}

    path = store_path(tmp_path)
    write_document(path, {"version": 1, "annotations": []})
    assert load_annotations(path) == {}


def test_set_owner_and_set_notes_change_only_target(tmp_path):
    path = store_path(tmp_path)
    result = frozen_result()
    identities = accepted_invoice_identities(result)

    set_owner(identities, "Acme Cleaning Co", "INV-1001", "Dana", store_path=path)
    set_notes(
        identities,
        "Acme Cleaning Co",
        "INV-1002",
        "Call Tuesday.",
        store_path=path,
    )

    stored = load_annotations(path)
    assert stored[("Acme Cleaning Co", "INV-1001")] == record(
        invoice_id="INV-1001", owner="Dana"
    )
    assert stored[("Acme Cleaning Co", "INV-1002")] == record(
        invoice_id="INV-1002", notes="Call Tuesday."
    )
    assert len(stored) == 2


def test_attach_preserves_order_and_maps_empty_strings_to_none(tmp_path):
    path = store_path(tmp_path)
    document = {
        "version": 1,
        "annotations": [
            record(owner="", notes=""),
            record(
                issuer="Bright Path Facilities",
                invoice_id="INV-1012",
                owner="Dana",
                notes="",
            ),
            record(invoice_id="INV-1003", owner="", notes="Follow up."),
        ],
    }
    write_document(path, document)
    source = build_followup_queue(frozen_result())

    attached = attach_annotations(source, path)

    assert without_annotations(attached) == without_annotations(source)
    assert [item["position"] for item in attached] == [
        item["position"] for item in source
    ]
    by_id = {item["invoice_id"]: item for item in attached}
    assert by_id["INV-1001"]["owner"] is None
    assert by_id["INV-1001"]["notes"] is None
    assert by_id["INV-1012"]["owner"] == "Dana"
    assert by_id["INV-1012"]["notes"] is None
    assert by_id["INV-1003"]["owner"] is None
    assert by_id["INV-1003"]["notes"] == "Follow up."
    assert all(
        item["owner"] is None and item["notes"] is None
        for item in attached
        if item["invoice_id"] not in ("INV-1012", "INV-1003")
    )
    assert source == build_followup_queue(frozen_result())


def test_whitespace_only_owner_is_attached_as_unassigned(tmp_path):
    path = store_path(tmp_path)
    write_document(
        path,
        {
            "version": 1,
            "annotations": [record(owner="   ", notes="Keep exactly.")],
        },
    )

    attached = attach_annotations(build_followup_queue(frozen_result()), path)
    by_id = {item["invoice_id"]: item for item in attached}

    assert by_id["INV-1001"]["owner"] is None
    assert by_id["INV-1001"]["notes"] == "Keep exactly."


def test_writer_normalizes_whitespace_owner_and_omits_empty_record(tmp_path):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())
    write_document(
        path,
        {
            "version": 1,
            "annotations": [
                record(owner="   ", notes="Keep exactly."),
                record(invoice_id="INV-1002", owner="   ", notes=""),
            ],
        },
    )

    set_notes(
        identities,
        "Bright Path Facilities",
        "INV-1012",
        "Trigger a rewrite.",
        store_path=path,
    )

    document = json.loads(path.read_text(encoding="utf-8"))
    by_identity = {
        (item["issuer"], item["invoice_id"]): item
        for item in document["annotations"]
    }
    assert by_identity[("Acme Cleaning Co", "INV-1001")]["owner"] == ""
    assert by_identity[("Acme Cleaning Co", "INV-1001")]["notes"] == "Keep exactly."
    assert ("Acme Cleaning Co", "INV-1002") not in by_identity


def test_two_identities_do_not_cross_contaminate_and_reload(tmp_path):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())

    set_owner(identities, "Acme Cleaning Co", "INV-1001", "Dana", store_path=path)
    set_notes(identities, "Bright Path Facilities", "INV-1012", "Call AP.", store_path=path)

    first = load_annotations(path)
    second = load_annotations(path)
    assert first == second
    assert first[("Acme Cleaning Co", "INV-1001")]["owner"] == "Dana"
    assert first[("Acme Cleaning Co", "INV-1001")]["notes"] == ""
    assert first[("Bright Path Facilities", "INV-1012")]["owner"] == ""
    assert first[("Bright Path Facilities", "INV-1012")]["notes"] == "Call AP."
    assert len(first) == 2


def test_multiline_and_non_ascii_notes_round_trip(tmp_path):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())
    notes = "Première ligne — café.\nDeuxième ligne ☎.\n"

    set_notes(identities, "Acme Cleaning Co", "INV-1001", notes, store_path=path)

    stored = load_annotations(path)
    assert stored[("Acme Cleaning Co", "INV-1001")]["notes"] == notes
    attached = attach_annotations(build_followup_queue(frozen_result()), path)
    by_id = {item["invoice_id"]: item for item in attached}
    assert by_id["INV-1001"]["notes"] == notes


def test_clearing_one_field_leaves_the_other_and_both_drops_record(tmp_path):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())
    identity = ("Acme Cleaning Co", "INV-1001")

    set_owner(identities, *identity, "Dana", store_path=path)
    set_notes(identities, *identity, "Call.", store_path=path)
    set_owner(identities, *identity, None, store_path=path)
    assert load_annotations(path)[identity]["owner"] == ""
    assert load_annotations(path)[identity]["notes"] == "Call."

    set_notes(identities, *identity, "Call.", store_path=path)
    set_owner(identities, *identity, "Dana", store_path=path)
    set_notes(identities, *identity, None, store_path=path)
    assert load_annotations(path)[identity]["owner"] == "Dana"
    assert load_annotations(path)[identity]["notes"] == ""

    set_owner(identities, *identity, "Dana", store_path=path)
    set_notes(identities, *identity, "", store_path=path)
    set_owner(identities, *identity, "   ", store_path=path)
    assert identity not in load_annotations(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["annotations"] == []


def test_non_accepted_identity_is_refused_without_touching_store(tmp_path):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())
    set_owner(identities, "Acme Cleaning Co", "INV-1001", "Dana", store_path=path)
    before = path.read_bytes()

    with pytest.raises(InvoiceNotAcceptedError):
        set_owner(identities, "Acme Cleaning Co", "INV-9001", "Dana", store_path=path)
    with pytest.raises(InvoiceNotAcceptedError):
        set_notes(
            identities,
            "Acme Cleaning Co",
            "INV-9001",
            "notes",
            store_path=path,
        )
    assert path.read_bytes() == before


@pytest.mark.parametrize("bad_owner", [5, b"x", ["a"]])
def test_set_owner_rejects_non_string_without_creating_store(tmp_path, bad_owner):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())

    with pytest.raises(AnnotationValueTypeError):
        set_owner(
            identities,
            "Acme Cleaning Co",
            "INV-1001",
            bad_owner,
            store_path=path,
        )

    assert not path.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("bad_owner", [5, b"x", ["a"]])
def test_set_owner_rejects_non_string_without_changing_existing_store(
    tmp_path, bad_owner
):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())
    set_notes(identities, "Acme Cleaning Co", "INV-1001", "Keep.", store_path=path)
    before = path.read_bytes()

    with pytest.raises(AnnotationValueTypeError):
        set_owner(
            identities,
            "Acme Cleaning Co",
            "INV-1001",
            bad_owner,
            store_path=path,
        )

    assert path.read_bytes() == before


@pytest.mark.parametrize("bad_notes", [5, b"x", ["a"]])
def test_set_notes_rejects_non_string_without_creating_store(tmp_path, bad_notes):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())

    with pytest.raises(AnnotationValueTypeError):
        set_notes(
            identities,
            "Acme Cleaning Co",
            "INV-1001",
            bad_notes,
            store_path=path,
        )

    assert not path.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("bad_notes", [5, b"x", ["a"]])
def test_set_notes_rejects_non_string_without_changing_existing_store(
    tmp_path, bad_notes
):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())
    set_owner(identities, "Acme Cleaning Co", "INV-1001", "Dana", store_path=path)
    before = path.read_bytes()

    with pytest.raises(AnnotationValueTypeError):
        set_notes(
            identities,
            "Acme Cleaning Co",
            "INV-1001",
            bad_notes,
            store_path=path,
        )

    assert path.read_bytes() == before


def test_annotation_for_absent_identity_is_retained_and_reappears(tmp_path):
    path = store_path(tmp_path)
    with_identity = imported(invoice("A", "INV-1"), invoice("A", "INV-2"))
    without_identity = imported(invoice("A", "INV-2"))
    identity = ("A", "INV-1")

    set_owner(
        accepted_invoice_identities(with_identity),
        *identity,
        "Dana",
        store_path=path,
    )

    absent_queue = followup_queue(without_identity, path)
    assert [item["invoice_id"] for item in absent_queue] == ["INV-2"]
    assert absent_queue[0]["owner"] is None
    assert load_annotations(path)[identity]["owner"] == "Dana"

    present_queue = followup_queue(with_identity, path)
    by_id = {item["invoice_id"]: item for item in present_queue}
    assert by_id["INV-1"]["owner"] == "Dana"


def test_annotation_changes_never_reorder_the_queue(tmp_path):
    path = store_path(tmp_path)
    result = frozen_result()
    identities = accepted_invoice_identities(result)
    before = followup_queue(result, path)

    set_owner(identities, "Acme Cleaning Co", "INV-1001", "Dana", store_path=path)
    set_notes(identities, "Acme Cleaning Co", "INV-1002", "Later.", store_path=path)
    set_notes(identities, "Bright Path Facilities", "INV-1012", "Now.", store_path=path)
    after = followup_queue(result, path)

    assert without_annotations(after) == without_annotations(before)
    assert [item["invoice_id"] for item in after] == [
        item["invoice_id"] for item in before
    ]
    assert [item["position"] for item in after] == [
        item["position"] for item in before
    ]


def test_malformed_json_is_reported_and_bytes_are_untouched(tmp_path):
    path = store_path(tmp_path)
    path.write_bytes(b"{not json")
    before = path.read_bytes()

    with pytest.raises(AnnotationStoreMalformedError):
        load_annotations(path)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "document",
    [
        [],
        "text",
        123,
        {"annotations": []},
        {"version": "1", "annotations": []},
        {"version": 1.0, "annotations": []},
        {"version": True, "annotations": []},
        {"version": 1, "annotations": {}},
        {"version": 1, "annotations": ["not an object"]},
        {"version": 1, "annotations": [{"issuer": "A", "invoice_id": "I", "owner": ""}]},
        {
            "version": 1,
            "annotations": [
                {"issuer": "A", "invoice_id": "I", "owner": "", "notes": "", "extra": 1}
            ],
        },
        {
            "version": 1,
            "annotations": [
                {"issuer": "A", "invoice_id": "I", "owner": 5, "notes": ""}
            ],
        },
        {
            "version": 1,
            "annotations": [
                {"issuer": "", "invoice_id": "I", "owner": "", "notes": ""}
            ],
        },
        {
            "version": 1,
            "annotations": [
                {"issuer": "A", "invoice_id": "", "owner": "", "notes": ""}
            ],
        },
        {"version": 1, "annotations": [], "extra": 1},
    ],
)
def test_malformed_documents_are_reported_and_bytes_are_untouched(
    tmp_path, document
):
    path = store_path(tmp_path)
    write_document(path, document)
    before = path.read_bytes()

    with pytest.raises(AnnotationStoreMalformedError):
        load_annotations(path)
    assert path.read_bytes() == before


def test_unsupported_version_is_reported_and_bytes_are_untouched(tmp_path):
    path = store_path(tmp_path)
    write_document(path, {"version": 2, "annotations": [record(owner="Dana")]})
    before = path.read_bytes()

    with pytest.raises(AnnotationStoreVersionError):
        load_annotations(path)
    assert path.read_bytes() == before


def test_duplicate_identity_is_reported_and_bytes_are_untouched(tmp_path):
    path = store_path(tmp_path)
    duplicate = record(owner="Dana")
    write_document(path, {"version": 1, "annotations": [duplicate, dict(duplicate)]})
    before = path.read_bytes()

    with pytest.raises(AnnotationStoreDuplicateIdentityError):
        load_annotations(path)
    assert path.read_bytes() == before


def test_unreadable_paths_are_reported_and_bytes_are_untouched(tmp_path):
    directory = tmp_path / "as-directory.json"
    directory.mkdir()
    with pytest.raises(AnnotationStoreUnreadableError):
        load_annotations(directory)

    path = store_path(tmp_path)
    path.write_bytes(b"\xff\xfe\x00")
    before = path.read_bytes()
    with pytest.raises(AnnotationStoreUnreadableError):
        load_annotations(path)
    assert path.read_bytes() == before


def test_assignment_on_invalid_store_does_not_overwrite(tmp_path):
    path = store_path(tmp_path)
    path.write_bytes(b"{broken")
    before = path.read_bytes()
    identities = accepted_invoice_identities(frozen_result())

    with pytest.raises(AnnotationStoreMalformedError):
        set_owner(identities, "Acme Cleaning Co", "INV-1001", "Dana", store_path=path)
    assert path.read_bytes() == before

    write_document(path, {"version": 9, "annotations": []})
    before = path.read_bytes()
    with pytest.raises(AnnotationStoreVersionError):
        set_notes(identities, "Acme Cleaning Co", "INV-1001", "notes", store_path=path)
    assert path.read_bytes() == before


def test_replace_failure_keeps_previous_store_and_removes_temp_file(
    tmp_path, monkeypatch
):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())
    set_owner(identities, "Acme Cleaning Co", "INV-1001", "Dana", store_path=path)
    before = path.read_bytes()

    def fail_replace(source, target):
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(annotations_module.os, "replace", fail_replace)

    with pytest.raises(AnnotationStoreWriteError):
        set_notes(
            identities,
            "Acme Cleaning Co",
            "INV-1001",
            "new notes",
            store_path=path,
        )

    assert path.read_bytes() == before
    assert [entry.name for entry in tmp_path.iterdir()] == [path.name]
    stored = load_annotations(path)
    assert stored[("Acme Cleaning Co", "INV-1001")]["owner"] == "Dana"
    assert stored[("Acme Cleaning Co", "INV-1001")]["notes"] == ""


def test_fsync_failure_keeps_previous_store_and_removes_temp_file(
    tmp_path, monkeypatch
):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())
    set_owner(identities, "Acme Cleaning Co", "INV-1001", "Dana", store_path=path)
    before = path.read_bytes()

    def fail_fsync(descriptor):
        raise OSError("simulated fsync failure")

    monkeypatch.setattr(annotations_module.os, "fsync", fail_fsync)

    with pytest.raises(AnnotationStoreWriteError):
        set_owner(
            identities,
            "Acme Cleaning Co",
            "INV-1001",
            "Zoë",
            store_path=path,
        )

    assert path.read_bytes() == before
    assert [entry.name for entry in tmp_path.iterdir()] == [path.name]
    stored = load_annotations(path)
    assert stored[("Acme Cleaning Co", "INV-1001")]["owner"] == "Dana"


def test_file_write_failure_keeps_previous_store_and_removes_temp_file(
    tmp_path, monkeypatch
):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())
    set_owner(identities, "Acme Cleaning Co", "INV-1001", "Dana", store_path=path)
    before = path.read_bytes()
    real_fdopen = annotations_module.os.fdopen

    class FailingHandle:
        def __init__(self, handle):
            self._handle = handle

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return self._handle.__exit__(exc_type, exc, traceback)

        def write(self, text):
            raise OSError("simulated write failure")

        def flush(self):
            self._handle.flush()

        def fileno(self):
            return self._handle.fileno()

    def failing_fdopen(descriptor, *args, **kwargs):
        return FailingHandle(real_fdopen(descriptor, *args, **kwargs))

    monkeypatch.setattr(annotations_module.os, "fdopen", failing_fdopen)

    with pytest.raises(AnnotationStoreWriteError):
        set_owner(
            identities,
            "Acme Cleaning Co",
            "INV-1001",
            "Zoë",
            store_path=path,
        )

    assert path.read_bytes() == before
    assert [entry.name for entry in tmp_path.iterdir()] == [path.name]
    stored = load_annotations(path)
    assert stored[("Acme Cleaning Co", "INV-1001")]["owner"] == "Dana"


def test_successful_write_is_utf8_sorted_and_newline_terminated(tmp_path):
    path = store_path(tmp_path)
    identities = accepted_invoice_identities(frozen_result())

    set_notes(
        identities,
        "Bright Path Facilities",
        "INV-1012",
        "Deuxième ligne — café.",
        store_path=path,
    )
    set_owner(identities, "Acme Cleaning Co", "INV-1001", "Zoë", store_path=path)

    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert "Zoë" in text
    assert "Deuxième" in text
    assert "\\u" not in text

    document = json.loads(text)
    assert document["version"] == 1
    pairs = [(item["issuer"], item["invoice_id"]) for item in document["annotations"]]
    assert pairs == sorted(pairs)
    assert pairs == [
        ("Acme Cleaning Co", "INV-1001"),
        ("Bright Path Facilities", "INV-1012"),
    ]
    assert all(set(item) == set(REQUIRED_FIELDS) for item in document["annotations"])
