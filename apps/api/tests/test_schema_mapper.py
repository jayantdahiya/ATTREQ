"""Tests for `services/ai/schema_mapper.py` (RI-2)."""

from __future__ import annotations

from attreq_api.services.ai.schema_mapper import (
    build_wardrobe_update_payload,
    map_classifier_result_to_wardrobe_schema,
)


def _full_v2_raw(**overrides) -> dict:
    base = {
        "category": "shirt",
        "color_primary": "blue",
        "color_secondary": None,
        "pattern": "solid",
        "season": ["summer"],
        "occasion": ["casual"],
        "texture": "smooth",
        "silhouette": "regular",
        "neckline": "crew",
        "sleeve_length": "short",
        "statement_level": "basic",
        "formality_score": 2,
        "is_fullbody": False,
        "detection_confidence": 0.9,
        "attribute_confidence": {
            "category": 0.95,
            "color_primary": 0.8,
            "pattern": 0.9,
            "season": 0.7,
            "occasion": 0.7,
            "texture": 0.85,
            "silhouette": 0.6,
            "neckline": 0.9,
            "sleeve_length": 0.95,
        },
        "processing_status": "completed",
    }
    base.update(overrides)
    return base


class TestMapClassifierResult:
    def test_full_v2_json_maps_every_field(self):
        result = map_classifier_result_to_wardrobe_schema(_full_v2_raw())

        assert result["category"] == "shirt"
        assert result["color_primary"] == "blue"
        assert result["pattern"] == "solid"
        assert result["season"] == ["summer"]
        assert result["occasion"] == ["casual"]
        assert result["texture"] == "smooth"
        assert result["silhouette"] == "regular"
        assert result["neckline"] == "crew"
        assert result["sleeve_length"] == "short"
        assert result["statement_level"] == "basic"
        assert result["llm_formality"] == 2
        assert result["is_fullbody"] is False
        assert result["attribute_confidence"]["category"] == 0.95
        assert result["schema_version"] == 2

    def test_out_of_vocabulary_texture_coerces_to_other_and_warns(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING):
            result = map_classifier_result_to_wardrobe_schema(_full_v2_raw(texture="fur"))
        assert result["texture"] == "other"
        assert any("fur" in record.message for record in caplog.records)

    def test_missing_attribute_confidence_defaults_to_detection_confidence(self):
        raw = _full_v2_raw(detection_confidence=0.42)
        del raw["attribute_confidence"]
        result = map_classifier_result_to_wardrobe_schema(raw)
        for key in (
            "category",
            "color_primary",
            "pattern",
            "season",
            "occasion",
            "texture",
            "silhouette",
            "neckline",
            "sleeve_length",
        ):
            assert result["attribute_confidence"][key] == 0.42

    def test_partial_attribute_confidence_falls_back_per_key(self):
        raw = _full_v2_raw(detection_confidence=0.5)
        raw["attribute_confidence"] = {"category": 0.99}  # only one key present
        result = map_classifier_result_to_wardrobe_schema(raw)
        assert result["attribute_confidence"]["category"] == 0.99
        assert result["attribute_confidence"]["texture"] == 0.5

    def test_formality_score_out_of_range_becomes_none(self):
        assert map_classifier_result_to_wardrobe_schema(_full_v2_raw(formality_score=7))[
            "llm_formality"
        ] is None
        assert map_classifier_result_to_wardrobe_schema(_full_v2_raw(formality_score=0))[
            "llm_formality"
        ] is None
        assert map_classifier_result_to_wardrobe_schema(_full_v2_raw(formality_score="high"))[
            "llm_formality"
        ] is None

    def test_formality_score_in_range_passes_through(self):
        for score in (1, 2, 3, 4):
            assert (
                map_classifier_result_to_wardrobe_schema(_full_v2_raw(formality_score=score))[
                    "llm_formality"
                ]
                == score
            )

    def test_is_fullbody_derived_from_category_even_when_llm_omits_it(self):
        raw = _full_v2_raw(category="dress")
        del raw["is_fullbody"]
        assert map_classifier_result_to_wardrobe_schema(raw)["is_fullbody"] is True

    def test_is_fullbody_derived_from_category_even_when_llm_contradicts_it(self):
        # LLM says False, but category is a recognized full-body category — the
        # derived value must win.
        raw = _full_v2_raw(category="jumpsuit", is_fullbody=False)
        assert map_classifier_result_to_wardrobe_schema(raw)["is_fullbody"] is True

        # And the inverse: LLM says True, but category is NOT full-body.
        raw2 = _full_v2_raw(category="shirt", is_fullbody=True)
        assert map_classifier_result_to_wardrobe_schema(raw2)["is_fullbody"] is False

    def test_is_fullbody_falls_back_to_llm_bool_when_category_missing(self):
        raw = _full_v2_raw(category=None, is_fullbody=True)
        assert map_classifier_result_to_wardrobe_schema(raw)["is_fullbody"] is True

    def test_is_fullbody_handles_stringy_llm_booleans(self):
        raw = _full_v2_raw(category=None, is_fullbody="true")
        assert map_classifier_result_to_wardrobe_schema(raw)["is_fullbody"] is True
        raw2 = _full_v2_raw(category=None, is_fullbody="false")
        assert map_classifier_result_to_wardrobe_schema(raw2)["is_fullbody"] is False

    def test_v1_fields_pass_through_unchanged(self):
        raw = {
            "category": "jeans",
            "color_primary": "blue",
            "color_secondary": "black",
            "pattern": "solid",
            "season": ["all"],
            "occasion": ["casual"],
            "detection_confidence": 0.75,
            "processing_status": "completed",
        }
        result = map_classifier_result_to_wardrobe_schema(raw)
        assert result["category"] == "jeans"
        assert result["color_secondary"] == "black"
        assert result["detection_confidence"] == 0.75
        assert result["schema_version"] == 2  # always 2 through this function


class TestBuildWardrobeUpdatePayload:
    def test_v1_shaped_detection_result_omits_v2_fields(self):
        v1_result = {
            "category": None,
            "color_primary": None,
            "color_secondary": None,
            "pattern": None,
            "season": [],
            "occasion": [],
            "detection_confidence": 0.0,
            "processing_status": "failed",
        }
        payload = build_wardrobe_update_payload(
            detection_result=v1_result,
            palette=None,
            color_extraction_source="llm_fallback",
            processed_image_url="/uploads/processed/x.png",
            thumbnail_url="/uploads/thumbnails/x.png",
        )
        assert "texture" not in payload
        assert payload["color_palette"] is None
        assert payload["color_extraction_source"] == "llm_fallback"

    def test_v2_shaped_detection_result_includes_v2_fields(self):
        v2_result = map_classifier_result_to_wardrobe_schema(_full_v2_raw())
        payload = build_wardrobe_update_payload(
            detection_result=v2_result,
            palette=None,
            color_extraction_source="llm_fallback",
            processed_image_url="/uploads/processed/x.png",
            thumbnail_url=None,
        )
        assert payload["texture"] == "smooth"
        assert payload["schema_version"] == 2

    def test_palette_serializes_to_plain_dicts(self):
        from attreq_api.services.ai.color_extraction import ColorPalette, PaletteColor

        palette = ColorPalette(
            colors=[
                PaletteColor(lab=(50.0, 1.0, 2.0), hex="#808080", share=0.9, is_neutral=True, name="gray")
            ],
            source="pixel",
        )
        payload = build_wardrobe_update_payload(
            detection_result=map_classifier_result_to_wardrobe_schema(_full_v2_raw()),
            palette=palette,
            color_extraction_source="pixel",
            processed_image_url="/uploads/processed/x.png",
            thumbnail_url="/uploads/thumbnails/x.png",
        )
        assert payload["color_palette"] == [
            {"lab": [50.0, 1.0, 2.0], "hex": "#808080", "share": 0.9, "is_neutral": True, "name": "gray"}
        ]
