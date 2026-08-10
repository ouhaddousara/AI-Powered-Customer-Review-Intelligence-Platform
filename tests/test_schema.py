"""Unit tests for src/ingestion/schema.py"""

from datetime import date

from src.ingestion.schema import Review, make_review_id


def test_make_review_id_is_deterministic():
    id1 = make_review_id("json", "user123:1234567890")
    id2 = make_review_id("json", "user123:1234567890")
    assert id1 == id2


def test_make_review_id_differs_by_source():
    id_json = make_review_id("json", "same_original_id")
    id_csv = make_review_id("csv", "same_original_id")
    assert id_json != id_csv


def test_review_to_dict_serializes_date_as_iso_string():
    review = Review(
        review_id="abc123",
        product_id="B001",
        source="json",
        text_raw="Great product",
        review_date=date(2024, 3, 12),
    )
    result = review.to_dict()
    assert result["review_date"] == "2024-03-12"


def test_review_to_dict_handles_missing_date():
    review = Review(
        review_id="abc123",
        product_id="B001",
        source="json",
        text_raw="Great product",
        review_date=None,
    )
    result = review.to_dict()
    assert result["review_date"] is None
