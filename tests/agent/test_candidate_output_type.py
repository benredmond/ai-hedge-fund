import pytest

from pydantic_ai import PromptedOutput

from src.agent.models import CandidateList, SingleStrategy
from src.agent.stages import candidate_generator as cg


def test_candidate_output_type_for_gemini_single_strategy():
    output = cg._candidate_output_type_for_model(
        "gemini:gemini-3-pro-preview", SingleStrategy
    )
    assert isinstance(output, PromptedOutput)
    assert output.outputs is SingleStrategy


def test_candidate_output_type_for_gemini_candidate_list():
    output = cg._candidate_output_type_for_model(
        "gemini:gemini-3-pro-preview", CandidateList
    )
    assert isinstance(output, PromptedOutput)
    assert output.outputs is CandidateList


def test_candidate_output_type_for_non_gemini():
    output = cg._candidate_output_type_for_model("openai:gpt-4o", SingleStrategy)
    assert output is SingleStrategy
