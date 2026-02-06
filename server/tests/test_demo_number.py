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
        from models import Number, NumberConfirmationRequired, OutOfOrderNumber
        # Create tables
        db.create_all()
        yield {
            "Number": Number,
            "NumberConfirmationRequired": NumberConfirmationRequired,
            "OutOfOrderNumber": OutOfOrderNumber,
        }
        # Teardown: drop tables
        db.drop_all()


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
