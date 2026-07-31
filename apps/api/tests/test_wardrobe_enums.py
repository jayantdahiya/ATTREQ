"""Tests for `schemas/wardrobe_enums.py` — coercion + prompt/enum parity (RI-2)."""

from __future__ import annotations

import logging

from attreq_api.schemas.wardrobe_enums import (
    NECKLINE_VALUES,
    SILHOUETTE_VALUES,
    SLEEVE_LENGTH_VALUES,
    STATEMENT_LEVEL_VALUES,
    TEXTURE_VALUES,
    Neckline,
    SleeveLength,
    Texture,
    coerce_enum,
)
from attreq_api.services.ai import (
    claude_classifier,
    gemini_classifier,
    groq_classifier,
    openai_classifier,
)
from attreq_api.services.ai.prompt_text import CLASSIFICATION_PROMPT


class TestCoerceEnum:
    def test_passthrough_exact_match(self):
        assert coerce_enum("knit", Texture, Texture.OTHER) is Texture.KNIT

    def test_case_insensitive_and_trimmed(self):
        assert coerce_enum("  KNIT ", Texture, Texture.OTHER) is Texture.KNIT

    def test_unknown_value_falls_back_and_warns(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = coerce_enum("fur", Texture, Texture.OTHER)
        assert result is Texture.OTHER
        assert any("fur" in record.message for record in caplog.records)

    def test_none_falls_back(self):
        assert coerce_enum(None, SleeveLength, SleeveLength.N_A) is SleeveLength.N_A

    def test_non_string_falls_back(self):
        assert coerce_enum(3.14, Neckline, Neckline.N_A) is Neckline.N_A


class TestPromptParity:
    def test_prompt_contains_every_texture_value(self):
        for value in TEXTURE_VALUES:
            assert value in CLASSIFICATION_PROMPT

    def test_prompt_contains_every_silhouette_value(self):
        for value in SILHOUETTE_VALUES:
            assert value in CLASSIFICATION_PROMPT

    def test_prompt_contains_every_neckline_value(self):
        for value in NECKLINE_VALUES:
            assert value in CLASSIFICATION_PROMPT

    def test_prompt_contains_every_sleeve_length_value(self):
        for value in SLEEVE_LENGTH_VALUES:
            assert value in CLASSIFICATION_PROMPT

    def test_prompt_contains_every_statement_level_value(self):
        for value in STATEMENT_LEVEL_VALUES:
            assert value in CLASSIFICATION_PROMPT

    def test_all_four_classifiers_share_the_same_prompt_object(self):
        assert groq_classifier.CLASSIFICATION_PROMPT is CLASSIFICATION_PROMPT
        assert claude_classifier.CLASSIFICATION_PROMPT is CLASSIFICATION_PROMPT
        assert openai_classifier.CLASSIFICATION_PROMPT is CLASSIFICATION_PROMPT
        assert gemini_classifier.CLASSIFICATION_PROMPT is CLASSIFICATION_PROMPT
