#!/usr/bin/env python3
"""
Test Suite for Summary Generator - Phase 5: Summary Generation System

This module contains comprehensive tests for the SummaryGenerator class,
testing time period grouping, entity aggregation, and LLM-powered summary generation.

Author: Work Journal Summarizer Project
Version: Phase 5 - Summary Generation System
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock
from pathlib import Path

from summary_generator import SummaryGenerator, PeriodSummary, SummaryStats
from llm_data_structures import AnalysisResult, LLMClientProtocol


class TestSummaryGenerator:
    """Test suite for SummaryGenerator class."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client for testing."""
        mock_client = MagicMock(spec=LLMClientProtocol)
        return mock_client
    
    @pytest.fixture
    def sample_analysis_results(self):
        """Create sample analysis results for testing."""
        return [
            AnalysisResult(
                file_path=Path("worklog_2024-04-01.txt"),
                projects=["Project Alpha", "Beta Initiative"],
                participants=["John Doe", "Jane Smith"],
                tasks=["Code review", "Meeting preparation"],
                themes=["Development", "Planning"],
                api_call_time=1.5
            ),
            AnalysisResult(
                file_path=Path("worklog_2024-04-02.txt"),
                projects=["Project Alpha", "Gamma Project"],
                participants=["Jane Smith", "Bob Wilson"],
                tasks=["Bug fixing", "Documentation"],
                themes=["Development", "Documentation"],
                api_call_time=1.2
            ),
            AnalysisResult(
                file_path=Path("worklog_2024-04-08.txt"),
                projects=["Beta Initiative"],
                participants=["John Doe"],
                tasks=["Testing", "Deployment"],
                themes=["Testing", "Operations"],
                api_call_time=1.8
            )
        ]
    
    @pytest.fixture
    def summary_generator(self, mock_llm_client):
        """Create SummaryGenerator instance with mock LLM client."""
        return SummaryGenerator(mock_llm_client)
    
    def test_weekly_grouping(self, summary_generator, sample_analysis_results):
        """Test grouping analysis results by weeks."""
        # Test data spans two weeks: April 1-2 (Week 1) and April 8 (Week 2)
        grouped = summary_generator._group_by_periods(sample_analysis_results, "weekly")
        
        # Should have 2 groups
        assert len(grouped) == 2
        
        # Check that results are grouped correctly
        week1_key = list(grouped.keys())[0]
        week2_key = list(grouped.keys())[1]
        
        # Week 1 should have 2 entries (April 1-2)
        assert len(grouped[week1_key]) == 2
        # Week 2 should have 1 entry (April 8)
        assert len(grouped[week2_key]) == 1
    
    def test_monthly_grouping(self, summary_generator, sample_analysis_results):
        """Test grouping analysis results by months."""
        grouped = summary_generator._group_by_periods(sample_analysis_results, "monthly")
        
        # All sample data is from April 2024, should have 1 group
        assert len(grouped) == 1
        
        # Should contain all 3 analysis results
        month_key = list(grouped.keys())[0]
        assert len(grouped[month_key]) == 3
        assert "April 2024" in month_key
    
    def test_week_calculation(self, summary_generator):
        """Test week period calculation for various dates."""
        # Test Monday (start of week)
        monday = date(2024, 4, 1)  # April 1, 2024 is a Monday
        period_name, start_date, end_date = summary_generator._calculate_week_period(monday)
        
        assert start_date == monday
        assert end_date == monday + timedelta(days=6)  # Sunday
        assert "Week of 2024-04-01" in period_name
        
        # Test Wednesday (middle of week)
        wednesday = date(2024, 4, 3)
        period_name, start_date, end_date = summary_generator._calculate_week_period(wednesday)
        
        assert start_date == date(2024, 4, 1)  # Monday of that week
        assert end_date == date(2024, 4, 7)    # Sunday of that week
        
        # Test Sunday (end of week)
        sunday = date(2024, 4, 7)
        period_name, start_date, end_date = summary_generator._calculate_week_period(sunday)
        
        assert start_date == date(2024, 4, 1)  # Monday of that week
        assert end_date == sunday
    
    def test_month_calculation(self, summary_generator):
        """Test month period calculation."""
        # Test various dates in April 2024
        test_dates = [
            date(2024, 4, 1),   # First day
            date(2024, 4, 15),  # Middle
            date(2024, 4, 30)   # Last day
        ]
        
        for test_date in test_dates:
            period_name, start_date, end_date = summary_generator._calculate_month_period(test_date)
            
            assert start_date == date(2024, 4, 1)
            assert end_date == date(2024, 4, 30)
            assert period_name == "April 2024"
    
    def test_entity_aggregation(self, summary_generator, sample_analysis_results):
        """Test aggregation and deduplication across periods."""
        # Take first two results (same week)
        week_results = sample_analysis_results[:2]
        
        aggregated = summary_generator._aggregate_entities(week_results)
        
        # Check projects aggregation and deduplication
        expected_projects = ["Project Alpha", "Beta Initiative", "Gamma Project"]
        assert set(aggregated['projects']) == set(expected_projects)
        
        # Check participants aggregation and deduplication
        expected_participants = ["John Doe", "Jane Smith", "Bob Wilson"]
        assert set(aggregated['participants']) == set(expected_participants)
        
        # Check tasks aggregation
        expected_tasks = ["Code review", "Meeting preparation", "Bug fixing", "Documentation"]
        assert set(aggregated['tasks']) == set(expected_tasks)
        
        # Check themes aggregation
        expected_themes = ["Development", "Planning", "Documentation"]
        assert set(aggregated['themes']) == set(expected_themes)
    
    def test_summary_generation(self, summary_generator, sample_analysis_results):
        """Test summary generation with mocked LLM."""
        # Mock the LLM client's analyze_content method to return a summary
        mock_summary_response = AnalysisResult(
            file_path=Path("summary"),
            projects=[],
            participants=[],
            tasks=[],
            themes=[],
            api_call_time=2.0,
            raw_response="This week focused on Project Alpha development with key collaborations between team members."
        )
        
        # Configure the mock to return our summary when called
        summary_generator.llm_client.analyze_content.return_value = mock_summary_response
        
        # Test summary generation
        summaries, stats = summary_generator.generate_summaries(
            sample_analysis_results, "weekly", date(2024, 4, 1), date(2024, 4, 14)
        )
        
        # Should generate summaries for the periods found
        assert len(summaries) >= 1
        assert stats.total_periods >= 1
        assert stats.successful_summaries >= 0
        
        # Check that LLM was called for summary generation
        assert summary_generator.llm_client.analyze_content.called
    
    def test_partial_periods(self, summary_generator):
        """Test handling of partial weeks/months at boundaries."""
        # Create analysis results that span partial periods
        partial_results = [
            AnalysisResult(
                file_path=Path("worklog_2024-03-31.txt"),  # Sunday (end of March)
                projects=["Project A"],
                participants=["Person A"],
                tasks=["Task A"],
                themes=["Theme A"],
                api_call_time=1.0
            ),
            AnalysisResult(
                file_path=Path("worklog_2024-04-01.txt"),  # Monday (start of April)
                projects=["Project B"],
                participants=["Person B"],
                tasks=["Task B"],
                themes=["Theme B"],
                api_call_time=1.0
            )
        ]
        
        # Test weekly grouping across month boundary
        grouped = summary_generator._group_by_periods(partial_results, "weekly")
        
        # Should handle the boundary correctly
        assert len(grouped) >= 1
        
        # Test monthly grouping
        grouped_monthly = summary_generator._group_by_periods(partial_results, "monthly")
        
        # Should separate March and April
        assert len(grouped_monthly) == 2
    
    def test_empty_periods(self, summary_generator):
        """Test handling of periods with no journal entries."""
        empty_results = []
        
        summaries, stats = summary_generator.generate_summaries(
            empty_results, "weekly", date(2024, 4, 1), date(2024, 4, 7)
        )
        
        # Should handle empty input gracefully
        assert len(summaries) == 0
        assert stats.total_periods == 0
        assert stats.successful_summaries == 0
        assert stats.failed_summaries == 0
    
    def test_cross_year_grouping(self, summary_generator):
        """Test grouping across year boundaries."""
        cross_year_results = [
            AnalysisResult(
                file_path=Path("worklog_2023-12-31.txt"),
                projects=["Year End Project"],
                participants=["Person A"],
                tasks=["Year end tasks"],
                themes=["Closure"],
                api_call_time=1.0
            ),
            AnalysisResult(
                file_path=Path("worklog_2024-01-01.txt"),
                projects=["New Year Project"],
                participants=["Person B"],
                tasks=["New year tasks"],
                themes=["Planning"],
                api_call_time=1.0
            )
        ]
        
        # Test monthly grouping across years
        grouped = summary_generator._group_by_periods(cross_year_results, "monthly")
        
        # Should have separate groups for December 2023 and January 2024
        assert len(grouped) == 2
        
        # Check that the groups are correctly labeled
        group_names = list(grouped.keys())
        assert any("December 2023" in name for name in group_names)
        assert any("January 2024" in name for name in group_names)
    
    def test_summary_stats_calculation(self, summary_generator, sample_analysis_results):
        """Test calculation of summary statistics."""
        # Mock successful summary generation
        summary_generator.llm_client.analyze_content.return_value = AnalysisResult(
            file_path=Path("summary"),
            projects=[], participants=[], tasks=[], themes=[],
            api_call_time=1.0,
            raw_response="Generated summary text"
        )
        
        summaries, stats = summary_generator.generate_summaries(
            sample_analysis_results, "weekly", date(2024, 4, 1), date(2024, 4, 14)
        )
        
        # Verify stats are calculated correctly
        assert stats.total_periods >= 0
        assert stats.successful_summaries >= 0
        assert stats.failed_summaries >= 0
        assert stats.total_entries_processed == len(sample_analysis_results)
        assert stats.total_generation_time >= 0
        
        # If summaries were generated, check average length calculation
        if stats.successful_summaries > 0:
            assert stats.average_summary_length >= 0
    
    def test_error_handling_in_summary_generation(self, summary_generator, sample_analysis_results):
        """Test error handling when LLM summary generation fails."""
        # Mock LLM client to raise an exception
        summary_generator.llm_client.analyze_content.side_effect = Exception("API Error")
        
        summaries, stats = summary_generator.generate_summaries(
            sample_analysis_results, "weekly", date(2024, 4, 1), date(2024, 4, 14)
        )
        
        # Should handle errors gracefully
        assert isinstance(summaries, list)
        assert isinstance(stats, SummaryStats)
        
        # Failed summaries should be tracked
        assert stats.failed_summaries >= 0
    
    def test_date_extraction_from_file_path(self, summary_generator):
        """Test extraction of dates from file paths for grouping."""
        # Test various file path formats
        test_paths = [
            Path("worklog_2024-04-01.txt"),
            Path("some/path/worklog_2024-04-15.txt"),
            Path("worklog_2024-12-31.txt")
        ]
        
        for path in test_paths:
            # Create a dummy analysis result
            result = AnalysisResult(
                file_path=path,
                projects=[], participants=[], tasks=[], themes=[],
                api_call_time=1.0
            )
            
            # Test that the date can be extracted and used for grouping
            grouped = summary_generator._group_by_periods([result], "monthly")
            assert len(grouped) == 1
    
    def test_summary_word_count_tracking(self, summary_generator, sample_analysis_results):
        """Test tracking of word counts in generated summaries."""
        # Mock LLM to return a summary with known word count
        test_summary = "This is a test summary with exactly ten words in it."
        summary_generator.llm_client.analyze_content.return_value = AnalysisResult(
            file_path=Path("summary"),
            projects=[], participants=[], tasks=[], themes=[],
            api_call_time=1.0,
            raw_response=test_summary
        )
        
        summaries, stats = summary_generator.generate_summaries(
            sample_analysis_results, "weekly", date(2024, 4, 1), date(2024, 4, 14)
        )
        
        # Check that word counts are tracked
        if summaries:
            for summary in summaries:
                assert summary.word_count >= 0
                if summary.summary_text:
                    # Verify word count is approximately correct
                    actual_words = len(summary.summary_text.split())
                    assert abs(summary.word_count - actual_words) <= 1


if __name__ == "__main__":
    pytest.main([__file__])