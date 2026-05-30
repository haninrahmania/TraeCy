"""
Unit tests for alignment_mcp server.
Tests the _score function and related utilities.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alignment_server import _text_of, _score, _sim_matrix


class TestTextOf:
    """Test the _text_of utility function."""

    def test_deliverable_with_title_and_description(self):
        item = {"title": "Login System", "description": "User authentication"}
        result = _text_of(item)
        assert result == "Login System. User authentication"

    def test_deliverable_with_title_only(self):
        item = {"title": "Dashboard"}
        result = _text_of(item)
        assert result == "Dashboard"

    def test_deliverable_with_description_only(self):
        item = {"description": "Analytics feature"}
        result = _text_of(item)
        assert result == "Analytics feature"

    def test_empty_item(self):
        item = {}
        result = _text_of(item)
        assert result == ""

    def test_goal_format(self):
        item = {"goal_text": "Improve user retention", "goal_id": "g1"}
        result = _text_of(item)
        assert result == "Improve user retention"

    def test_strips_leading_periods(self):
        item = {"title": "Test", "description": "Description"}
        result = _text_of(item)
        assert not result.startswith(".")
        assert not result.endswith(".")


class TestSimMatrix:
    """Test the similarity matrix calculation."""

    def test_empty_inputs(self):
        result = _sim_matrix([], [])
        assert result == []

    def test_empty_goals(self):
        deliv_texts = ["Deliverable 1", "Deliverable 2"]
        result = _sim_matrix([], deliv_texts)
        assert result == []

    def test_empty_deliverables(self):
        goal_texts = ["Goal 1", "Goal 2"]
        result = _sim_matrix(goal_texts, [])
        assert result == [[], []]

    def test_single_goal_single_deliverable(self):
        goals = ["Improve performance"]
        delivs = ["Performance optimization"]
        result = _sim_matrix(goals, delivs)
        assert len(result) == 1
        assert len(result[0]) == 1
        assert 0 <= result[0][0] <= 1

    def test_multiple_goals_and_deliverables(self):
        goals = ["Goal 1", "Goal 2", "Goal 3"]
        delivs = ["Deliverable A", "Deliverable B"]
        result = _sim_matrix(goals, delivs)
        assert len(result) == 3
        assert all(len(row) == 2 for row in result)


class TestScoreFunction:
    """Test the core _score function."""

    def test_basic_scoring(self):
        deliverables = [
            {"id": "d1", "title": "Auth System", "description": "Login feature"},
            {"id": "d2", "title": "Dashboard", "description": "Analytics UI"},
        ]
        goals = [
            {"goal_id": "g1", "goal_text": "Improve user authentication"},
            {"goal_id": "g2", "goal_text": "Better data visualization"},
        ]

        result = _score(deliverables, goals, threshold=0.3)

        assert result["backend"] in ["embeddings", "tfidf"]
        assert result["threshold"] == 0.3
        assert len(result["results"]) == 2

        assert result["results"][0]["goal_id"] == "g1"
        assert result["results"][1]["goal_id"] == "g2"

        assert "match_score" in result["results"][0]
        assert "supporting_deliverables" in result["results"][0]
        assert "per_deliverable" in result["results"][0]

    def test_threshold_filtering(self):
        deliverables = [{"id": "d1", "title": "Test"}]
        goals = [{"goal_id": "g1", "goal_text": "Goal"}]

        high_threshold_result = _score(deliverables, goals, threshold=0.99)
        low_threshold_result = _score(deliverables, goals, threshold=0.1)

        assert (
            len(high_threshold_result["results"][0]["supporting_deliverables"])
            <= len(low_threshold_result["results"][0]["supporting_deliverables"])
        )

    def test_per_deliverable_sorted_by_score(self):
        deliverables = [
            {"id": "d1", "title": "Related work"},
            {"id": "d2", "title": "Unrelated content"},
            {"id": "d3", "title": "Also related"},
        ]
        goals = [{"goal_id": "g1", "goal_text": "Work on features"}]

        result = _score(deliverables, goals, threshold=0.0)
        per_deliv = result["results"][0]["per_deliverable"]

        scores = [item["score"] for item in per_deliv]
        assert scores == sorted(scores, reverse=True)

    def test_empty_deliverables(self):
        goals = [{"goal_id": "g1", "goal_text": "Test goal"}]
        result = _score([], goals, threshold=0.4)

        assert len(result["results"]) == 1
        assert result["results"][0]["match_score"] == 0.0
        assert result["results"][0]["supporting_deliverables"] == []

    def test_empty_goals(self):
        deliverables = [{"id": "d1", "title": "Test deliverable"}]
        result = _score(deliverables, [], threshold=0.4)

        assert result["results"] == []

    def test_all_deliverables_supporting(self):
        deliverables = [
            {"id": "d1", "title": "Very related"},
            {"id": "d2", "title": "Also very related"},
        ]
        goals = [{"goal_id": "g1", "goal_text": "Similar content"}]

        result = _score(deliverables, goals, threshold=0.0)

        assert len(result["results"][0]["supporting_deliverables"]) == 2
        assert set(result["results"][0]["supporting_deliverables"]) == {"d1", "d2"}

    def test_no_supporting_deliverables(self):
        deliverables = [
            {"id": "d1", "title": "Cooking recipes"},
            {"id": "d2", "title": "Car maintenance"},
        ]
        goals = [{"goal_id": "g1", "goal_text": "Improve code quality"}]

        result = _score(deliverables, goals, threshold=0.4)

        assert result["results"][0]["supporting_deliverables"] == []

    def test_match_score_is_max(self):
        deliverables = [
            {"id": "d1", "title": "Partially related"},
            {"id": "d2", "title": "Highly related"},
        ]
        goals = [{"goal_id": "g1", "goal_text": "Related topic"}]

        result = _score(deliverables, goals, threshold=0.0)
        match_score = result["results"][0]["match_score"]
        per_deliv = result["results"][0]["per_deliverable"]
        max_score = max(item["score"] for item in per_deliv)

        assert match_score == max_score

    def test_deliverable_ids_preserved(self):
        deliverables = [
            {"id": "unique-id-123", "title": "Title 1"},
            {"id": "another-id-456", "title": "Title 2"},
        ]
        goals = [{"goal_id": "g1", "goal_text": "Goal"}]

        result = _score(deliverables, goals, threshold=0.0)

        for item in result["results"][0]["per_deliverable"]:
            assert "id" in item
            assert item["id"] in ["unique-id-123", "another-id-456"]

    def test_goal_text_preserved(self):
        goal_text = "This is an important goal"
        goals = [{"goal_id": "g1", "goal_text": goal_text}]
        deliverables = [{"id": "d1", "title": "Deliverable"}]

        result = _score(deliverables, goals, threshold=0.0)

        assert result["results"][0]["goal_text"] == goal_text


class TestIntegration:
    """Integration tests for typical use cases."""

    def test_software_team_example(self):
        """Test with realistic software team deliverables and goals."""
        deliverables = [
            {
                "id": "auth-module",
                "title": "OAuth2 Implementation",
                "description": "Implemented secure authentication with OAuth2 and JWT tokens",
            },
            {
                "id": "perf-dashboard",
                "title": "Performance Monitoring",
                "description": "Built real-time dashboard for API response times and error rates",
            },
            {
                "id": "docs-site",
                "title": "Documentation Site",
                "description": "Created comprehensive developer documentation with examples",
            },
        ]

        goals = [
            {
                "goal_id": "security",
                "goal_text": "Improve application security and compliance",
            },
            {
                "goal_id": "reliability",
                "goal_text": "Increase system uptime and reduce errors",
            },
            {
                "goal_id": "developer-experience",
                "goal_text": "Make it easier for developers to onboard and build",
            },
        ]

        result = _score(deliverables, goals, threshold=0.3)

        assert result["backend"] in ["embeddings", "tfidf"]
        assert len(result["results"]) == 3

        assert result["results"][0]["goal_id"] == "security"
        assert result["results"][1]["goal_id"] == "reliability"
        assert result["results"][2]["goal_id"] == "developer-experience"

        assert "auth-module" in result["results"][0]["supporting_deliverables"]
        assert "perf-dashboard" in result["results"][1]["supporting_deliverables"]
        assert "docs-site" in result["results"][2]["supporting_deliverables"]

    def test_marketing_team_example(self):
        """Test with realistic marketing team deliverables and goals."""
        deliverables = [
            {
                "id": "blog-post-1",
                "title": "Product Launch Blog",
                "description": "Announced new features to customers via blog post",
            },
            {
                "id": "social-campaign",
                "title": "Social Media Push",
                "description": "Coordinated Twitter and LinkedIn campaign for product launch",
            },
            {
                "id": "newsletter",
                "title": "Email Newsletter",
                "description": "Sent monthly newsletter to subscriber list",
            },
        ]

        goals = [
            {
                "goal_id": "brand-awareness",
                "goal_text": "Increase brand visibility and recognition",
            },
            {
                "goal_id": "lead-generation",
                "goal_text": "Generate qualified leads for sales team",
            },
        ]

        result = _score(deliverables, goals, threshold=0.25)

        assert len(result["results"]) == 2

        assert result["results"][0]["goal_id"] == "brand-awareness"
        assert result["results"][1]["goal_id"] == "lead-generation"

        assert "blog-post-1" in result["results"][0]["supporting_deliverables"]
        assert "social-campaign" in result["results"][0]["supporting_deliverables"]
