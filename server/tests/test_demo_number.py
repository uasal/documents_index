import pytest
from flask import Flask
from app import db


def setup_test_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    # Use in-memory sqlite for both default and sqlite_db bind
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Re-init db with this app for testing context
    db.init_app(app)
    return app


@pytest.fixture()
def test_app():
    app = setup_test_app()
    with app.app_context():
        # Import models here so they bind to the test-configured db
        from models import (
            Number,
            NumberConfirmationRequired,
            NumberGenerationError,
            OutOfOrderNumber,
        )
        # Create tables
        db.create_all()
        yield {
            "Number": Number,
            "NumberConfirmationRequired": NumberConfirmationRequired,
            "NumberGenerationError": NumberGenerationError,
            "OutOfOrderNumber": OutOfOrderNumber,
        }
        # Teardown: drop tables
        db.drop_all()


@pytest.fixture()
def with_tn_series():
    """Registers a 'TN' series for the duration of a test and rebuilds the
    document patterns from it, mimicking the one line change that extending the
    scheme would require."""
    import models

    original_series = dict(models.DOC_SERIES)
    original_patterns = (models.DOC_STUB_PATTERN, models.DOC_VALUE_PATTERN)

    models.DOC_SERIES["TN"] = {"label": "Technical Note", "width": 3}
    models.DOC_STUB_PATTERN, models.DOC_VALUE_PATTERN = models._build_doc_patterns()

    yield

    models.DOC_SERIES.clear()
    models.DOC_SERIES.update(original_series)
    models.DOC_STUB_PATTERN, models.DOC_VALUE_PATTERN = original_patterns


def _add_numbers(*values):
    """Seeds the db with document-type numbers."""
    from models import Number, TypeEnum

    db.session.add_all(
        [Number(value=value, entry_type=TypeEnum.document) for value in values]
    )
    db.session.commit()


def test_confirmation_required_when_prefix_exists(test_app):
    Number = test_app["Number"]
    NumberConfirmationRequired = test_app["NumberConfirmationRequired"]

    # Seed DB with two entries sharing the same prefix ABC-DE001
    from models import TypeEnum

    n1 = Number(value="ABC-DE001-00", entry_type=TypeEnum.drawing)
    n2 = Number(value="ABC-DE001-01", entry_type=TypeEnum.drawing)

    db.session.add_all([n1, n2])
    db.session.commit()

    with pytest.raises(NumberConfirmationRequired) as excinfo:
        Number._generate_drawing_value("ABC-DE001")

    exc = excinfo.value
    assert exc.suggested_value == "ABC-DE001-02"
    assert "The following entries exist for ABC-DE001:" in str(exc)
    assert "ABC-DE001-00" in str(exc)
    assert "ABC-DE001-01" in str(exc)

def test_out_of_order_suggests_next(test_app):
    Number = test_app["Number"]
    OutOfOrderNumber = test_app["OutOfOrderNumber"]

    # Seed DB with last entry ABC-DE001-00
    from models import TypeEnum
    n1 = Number(value="ABC-DE001-00", entry_type=TypeEnum.drawing)
    db.session.add(n1)
    db.session.commit()

    with pytest.raises(OutOfOrderNumber) as excinfo:
        Number._generate_drawing_value("ABC-DE003")

    exc = excinfo.value
    assert exc.suggested_next == "ABC-DE002-00"


def test_accepts_next_in_sequence_when_no_prior(test_app):
    Number = test_app["Number"]

    # Seed DB with last entry ABC-DE001-00
    from models import TypeEnum
    n1 = Number(value="ABC-DE001-00", entry_type=TypeEnum.drawing)
    db.session.add(n1)
    db.session.commit()

    # No prior entries for stub 'ABC-DE002'
    result = Number._generate_drawing_value("ABC-DE002")
    assert result == "ABC-DE002-00"


def test_generate_raises_on_no_user_value(test_app):
    Number = test_app["Number"]
    with pytest.raises(ValueError):
        Number._generate_drawing_value("")


def test_auto_increment_when_no_3digit_provided(test_app):
    Number = test_app["Number"]
    from models import TypeEnum

    # Seed with existing ABC-DE001-00 so next should be ABC-DE002-00 when stub 'ABC-DE' used
    n1 = Number(value="ABC-DE001-00", entry_type=TypeEnum.drawing)
    db.session.add(n1)
    db.session.commit()

    result = Number._generate_drawing_value("ABC-DE")
    assert result == "ABC-DE002-00"


def test_out_of_order_with_no_prior_suggests_001(test_app):
    Number = test_app["Number"]
    OutOfOrderNumber = test_app["OutOfOrderNumber"]

    # No prior entries for stub 'ABC-DE' -> provided 002 should be rejected and suggest 001
    with pytest.raises(OutOfOrderNumber) as excinfo:
        Number._generate_drawing_value("ABC-DE002")

    exc = excinfo.value
    assert exc.suggested_next == "ABC-DE001-00"


def test_generate_number_returns_none_when_not_applicable(test_app):
    Number = test_app["Number"]
    from models import TypeEnum, ChangeControlledEnum

    # Not change controlled -> should not create a number for drawing
    res = Number._generate_number(ChangeControlledEnum.no.value, TypeEnum.drawing.value, "ABC-DE")
    assert res is None


def test_rejects_provided_number_too_short(test_app):
    Number = test_app["Number"]
    # Numeric suffix of length 2 should be rejected by backend validation
    with pytest.raises(ValueError):
        Number._generate_drawing_value("ABC-DE01")


def test_rejects_provided_number_too_long(test_app):
    Number = test_app["Number"]
    # Numeric suffix of length 4 should be rejected by backend validation
    with pytest.raises(ValueError):
        Number._generate_drawing_value("ABC-DE0001")


def test_drawing_reports_unparseable_existing_entry(test_app):
    """An existing entry sharing the stub but not following the pattern used to
    blow up with an AttributeError while building its own error message."""
    Number = test_app["Number"]
    NumberGenerationError = test_app["NumberGenerationError"]
    from models import TypeEnum

    db.session.add(Number(value="ABC-DEXX-00", entry_type=TypeEnum.drawing))
    db.session.commit()

    with pytest.raises(NumberGenerationError) as excinfo:
        Number._generate_drawing_value("ABC-DE")

    assert "ABC-DEXX-00" in str(excinfo.value)


# --- document numbers ---------------------------------------------------------

def test_doc_value_starts_at_001(test_app):
    Number = test_app["Number"]
    assert Number._generate_doc_value("STP-LAZ-ESC") == "STP-LAZ-ESC-001"


def test_doc_value_increments(test_app):
    Number = test_app["Number"]
    _add_numbers("STP-LAZ-ESC-001", "STP-LAZ-ESC-002")
    assert Number._generate_doc_value("STP-LAZ-ESC") == "STP-LAZ-ESC-003"


def test_doc_departments_have_independent_counters(test_app):
    Number = test_app["Number"]
    _add_numbers("STP-LAZ-ESC-001", "STP-LAZ-ESC-002", "STP-LAZ-ESC-003")
    assert Number._generate_doc_value("STP-LAZ-PM") == "STP-LAZ-PM-001"
    assert Number._generate_doc_value("STP-LAZ-SE") == "STP-LAZ-SE-001"


def test_doc_value_ignores_drawing_numbers_sharing_the_prefix(test_app):
    Number = test_app["Number"]
    from models import TypeEnum

    db.session.add(Number(value="STP-LAZ-ESC-FA001-00", entry_type=TypeEnum.drawing))
    db.session.commit()
    _add_numbers("STP-LAZ-ESC-001")

    assert Number._generate_doc_value("STP-LAZ-ESC") == "STP-LAZ-ESC-002"


def test_doc_value_not_derived_from_string_ordering(test_app):
    """The next number is the highest parsed counter, not the highest entry by
    string order, so a value that sorts above the sequence cannot hijack it."""
    Number = test_app["Number"]
    _add_numbers("STP-LAZ-ESC-001", "STP-LAZ-ESC-002")
    # 'TN005' sorts above '002' (letters sort above digits) but is not part of
    # the base series, so it must be ignored entirely.
    _add_numbers("STP-LAZ-ESC-TN005")

    assert Number._generate_doc_value("STP-LAZ-ESC") == "STP-LAZ-ESC-003"


def test_unregistered_stub_is_rejected(test_app):
    Number = test_app["Number"]
    NumberGenerationError = test_app["NumberGenerationError"]

    for stub in ["STP-LAZ-XX", "STP-LAZ-ESC-TN", "ESC", "", None]:
        with pytest.raises(NumberGenerationError):
            Number._generate_doc_value(stub)


def test_sequence_exhaustion_is_reported(test_app):
    Number = test_app["Number"]
    NumberGenerationError = test_app["NumberGenerationError"]
    _add_numbers("STP-LAZ-SW-999")

    with pytest.raises(NumberGenerationError) as excinfo:
        Number._generate_doc_value("STP-LAZ-SW")

    assert "exhausted" in str(excinfo.value)


def test_generate_number_for_document_ignores_change_control(test_app):
    Number = test_app["Number"]
    from models import TypeEnum, ChangeControlledEnum

    for change_controlled in [ChangeControlledEnum.no.value, ChangeControlledEnum.yes.value]:
        number = Number._generate_number(
            change_controlled, TypeEnum.document.value, "STP-LAZ-PM"
        )
        assert number is not None
        assert number.entry_type == TypeEnum.document
        db.session.add(number)
        db.session.commit()

    assert Number._generate_doc_value("STP-LAZ-PM") == "STP-LAZ-PM-003"


def test_generate_number_for_document_without_stub_returns_none(test_app):
    Number = test_app["Number"]
    from models import TypeEnum, ChangeControlledEnum

    assert Number._generate_number(
        ChangeControlledEnum.no.value, TypeEnum.document.value, ""
    ) is None


# --- extending the scheme with a TN series ------------------------------------

def test_tn_series_has_its_own_counter(test_app, with_tn_series):
    Number = test_app["Number"]
    _add_numbers("STP-LAZ-ESC-001", "STP-LAZ-ESC-002")

    assert Number._generate_doc_value("STP-LAZ-ESC-TN") == "STP-LAZ-ESC-TN001"


def test_tn_and_base_series_do_not_collide(test_app, with_tn_series):
    """The regression this scheme is designed around: the two series share a
    prefix but must never see each other's counters, in either direction."""
    Number = test_app["Number"]
    _add_numbers("STP-LAZ-ESC-001", "STP-LAZ-ESC-TN001", "STP-LAZ-ESC-TN002")

    assert Number._generate_doc_value("STP-LAZ-ESC") == "STP-LAZ-ESC-002"
    assert Number._generate_doc_value("STP-LAZ-ESC-TN") == "STP-LAZ-ESC-TN003"


def test_tn_stub_is_offered_once_registered(test_app, with_tn_series):
    Number = test_app["Number"]
    values = [entry["value"] for entry in Number.document_stubs()]

    assert "STP-LAZ-ESC" in values
    assert "STP-LAZ-ESC-TN" in values
