import pytest
from flask import Flask
from app import db


def setup_test_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    # Use in-memory sqlite for both default and sqlite_db bind
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    # !!!!Remove this after adopting numbering into main app and remove the demo databases
    app.config["SQLALCHEMY_BINDS"] = {"sqlite_db": "sqlite:///:memory:"}
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Re-init db with this app for testing context
    db.init_app(app)
    return app


@pytest.fixture()
def test_app():
    app = setup_test_app()
    with app.app_context():
        # Import models here so they bind to the test-configured db
        from models_demo import DemoNumber, NumberConfirmationRequired, OutOfOrderNumber
        # Create tables
        db.create_all()
        yield {
            "DemoNumber": DemoNumber,
            "NumberConfirmationRequired": NumberConfirmationRequired,
            "OutOfOrderNumber": OutOfOrderNumber,
        }
        # Teardown: drop tables
        db.drop_all()


def test_confirmation_required_when_prefix_exists(test_app):
    DemoNumber = test_app["DemoNumber"]
    NumberConfirmationRequired = test_app["NumberConfirmationRequired"]

    # Seed DB with two entries sharing the same prefix ABC-DE001
    from models import TypeEnum

    n1 = DemoNumber(value="ABC-DE001-00", entry_type=TypeEnum.drawing)
    n2 = DemoNumber(value="ABC-DE001-01", entry_type=TypeEnum.drawing)

    db.session.add_all([n1, n2])
    db.session.commit()

    with pytest.raises(NumberConfirmationRequired) as excinfo:
        DemoNumber._generate_drawing_value("ABC-DE001")

    exc = excinfo.value
    assert exc.suggested_value == "ABC-DE001-02"
    assert "The following entries exist for ABC-DE001:" in str(exc)
    assert "ABC-DE001-00" in str(exc)
    assert "ABC-DE001-01" in str(exc)

def test_out_of_order_suggests_next(test_app):
    DemoNumber = test_app["DemoNumber"]
    OutOfOrderNumber = test_app["OutOfOrderNumber"]

    # Seed DB with last entry ABC-DE001-00
    from models import TypeEnum
    n1 = DemoNumber(value="ABC-DE001-00", entry_type=TypeEnum.drawing)
    db.session.add(n1)
    db.session.commit()

    with pytest.raises(OutOfOrderNumber) as excinfo:
        DemoNumber._generate_drawing_value("ABC-DE003")

    exc = excinfo.value
    assert exc.suggested_next == "ABC-DE002-00"


def test_accepts_next_in_sequence_when_no_prior(test_app):
    DemoNumber = test_app["DemoNumber"]

    # Seed DB with last entry ABC-DE001-00
    from models import TypeEnum
    n1 = DemoNumber(value="ABC-DE001-00", entry_type=TypeEnum.drawing)
    db.session.add(n1)
    db.session.commit()

    # No prior entries for stub 'ABC-DE002'
    result = DemoNumber._generate_drawing_value("ABC-DE002")
    assert result == "ABC-DE002-00"


def test_generate_raises_on_no_user_value(test_app):
    DemoNumber = test_app["DemoNumber"]
    with pytest.raises(ValueError):
        DemoNumber._generate_drawing_value("")


def test_auto_increment_when_no_3digit_provided(test_app):
    DemoNumber = test_app["DemoNumber"]
    from models import TypeEnum

    # Seed with existing ABC-DE001-00 so next should be ABC-DE002-00 when stub 'ABC-DE' used
    n1 = DemoNumber(value="ABC-DE001-00", entry_type=TypeEnum.drawing)
    db.session.add(n1)
    db.session.commit()

    result = DemoNumber._generate_drawing_value("ABC-DE")
    assert result == "ABC-DE002-00"


def test_out_of_order_with_no_prior_suggests_001(test_app):
    DemoNumber = test_app["DemoNumber"]
    OutOfOrderNumber = test_app["OutOfOrderNumber"]

    # No prior entries for stub 'ABC-DE' -> provided 002 should be rejected and suggest 001
    with pytest.raises(OutOfOrderNumber) as excinfo:
        DemoNumber._generate_drawing_value("ABC-DE002")

    exc = excinfo.value
    assert exc.suggested_next == "ABC-DE001-00"


def test_generate_number_returns_none_when_not_applicable(test_app):
    DemoNumber = test_app["DemoNumber"]
    from models import TypeEnum, ChangeControlledEnum

    # Not change controlled -> should not create a number for drawing
    res = DemoNumber._generate_number(ChangeControlledEnum.no.value, TypeEnum.drawing.value, "ABC-DE")
    assert res is None


def test_rejects_provided_number_too_short(test_app):
    DemoNumber = test_app["DemoNumber"]
    # Numeric suffix of length 2 should be rejected by backend validation
    with pytest.raises(ValueError):
        DemoNumber._generate_drawing_value("ABC-DE01")


def test_rejects_provided_number_too_long(test_app):
    DemoNumber = test_app["DemoNumber"]
    # Numeric suffix of length 4 should be rejected by backend validation
    with pytest.raises(ValueError):
        DemoNumber._generate_drawing_value("ABC-DE0001")
