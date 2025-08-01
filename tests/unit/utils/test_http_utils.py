from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from askui.utils.http_utils import parse_retry_after_header


class TestParseRetryAfterHeader:
    """Test cases for the `parse_retry_after_header` function."""

    def test_parse_numeric_seconds(self) -> None:
        """Test parsing numeric retry-after values."""
        assert parse_retry_after_header("30") == 30.0
        assert parse_retry_after_header("60.5") == 60.5
        assert parse_retry_after_header("0") == 0.0
        assert parse_retry_after_header("120") == 120.0

    def test_parse_rfc2822_date_format(self) -> None:
        """Test parsing RFC 2822 date format retry-after values."""
        # Test with a future date
        future_date = "Mon, 15 Jan 2024 12:00:00 GMT"
        with patch("askui.utils.http_utils.datetime") as mock_datetime:
            # Mock current time to be before the retry-after date
            mock_datetime.now.return_value = datetime(
                2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc
            )
            mock_datetime.strptime = datetime.strptime

            result = parse_retry_after_header(future_date)
            assert result > 0  # Should be positive seconds

    def test_parse_rfc2822_date_format_past_date(self) -> None:
        """Test parsing RFC 2822 date format with past date."""
        past_date = "Mon, 15 Jan 2024 10:00:00 GMT"
        with patch("askui.utils.http_utils.datetime") as mock_datetime:
            # Mock current time to be after the retry-after date
            mock_datetime.now.return_value = datetime(
                2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc
            )
            mock_datetime.strptime = datetime.strptime

            result = parse_retry_after_header(past_date)
            assert result < 0  # Should be negative seconds (past date)

    def test_parse_rfc2822_date_format_exact_time(self) -> None:
        """Test parsing RFC 2822 date format with exact current time."""
        exact_date = "Mon, 15 Jan 2024 11:00:00 GMT"
        with patch("askui.utils.http_utils.datetime") as mock_datetime:
            # Mock current time to be exactly the retry-after date
            mock_datetime.now.return_value = datetime(
                2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc
            )
            mock_datetime.strptime = datetime.strptime

            result = parse_retry_after_header(exact_date)
            assert result == 0.0  # Should be zero seconds

    def test_parse_invalid_numeric_input(self) -> None:
        """Test parsing invalid numeric inputs."""
        with pytest.raises(
            ValueError, match="Could not parse Retry-After header: invalid"
        ):
            parse_retry_after_header("invalid")

    def test_parse_invalid_date_format(self) -> None:
        """Test parsing invalid date format inputs."""
        with pytest.raises(
            ValueError, match="Could not parse Retry-After header: invalid_date"
        ):
            parse_retry_after_header("invalid_date")

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string input."""
        with pytest.raises(ValueError, match="Could not parse Retry-After header: "):
            parse_retry_after_header("")

    def test_parse_whitespace_string(self) -> None:
        """Test parsing whitespace-only string input."""
        with pytest.raises(ValueError, match="Could not parse Retry-After header:    "):
            parse_retry_after_header("   ")

    def test_parse_none_input(self) -> None:
        """Test parsing None input."""
        with pytest.raises(
            ValueError, match="Could not parse Retry-After header: None"
        ):
            parse_retry_after_header(None)  # type: ignore

    def test_parse_malformed_date(self) -> None:
        """Test parsing malformed date string."""
        malformed_date = "Mon, 15 Jan 2024 25:00:00 GMT"  # Invalid hour
        with pytest.raises(
            ValueError,
            match="Could not parse Retry-After header: Mon, 15 Jan 2024 25:00:00 GMT",
        ):
            parse_retry_after_header(malformed_date)

    def test_parse_date_without_gmt(self) -> None:
        """Test parsing date without GMT timezone."""
        date_without_gmt = "Mon, 15 Jan 2024 12:00:00"
        with pytest.raises(
            ValueError,
            match="Could not parse Retry-After header: Mon, 15 Jan 2024 12:00:00",
        ):
            parse_retry_after_header(date_without_gmt)

    def test_parse_negative_numeric(self) -> None:
        """Test parsing negative numeric values."""
        assert parse_retry_after_header("-30") == -30.0
        assert parse_retry_after_header("-60.5") == -60.5

    def test_parse_large_numeric(self) -> None:
        """Test parsing large numeric values."""
        assert parse_retry_after_header("86400") == 86400.0  # 24 hours
        assert parse_retry_after_header("31536000") == 31536000.0  # 1 year

    def test_parse_scientific_notation(self) -> None:
        """Test parsing scientific notation."""
        assert parse_retry_after_header("1e3") == 1000.0
        assert parse_retry_after_header("1.5e2") == 150.0

    def test_parse_edge_case_dates(self) -> None:
        """Test parsing edge case date formats."""
        # Test leap year date
        leap_year_date = "Mon, 29 Feb 2024 12:00:00 GMT"
        with patch("askui.utils.http_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(
                2024, 2, 29, 11, 0, 0, tzinfo=timezone.utc
            )
            mock_datetime.strptime = datetime.strptime

            result = parse_retry_after_header(leap_year_date)
            assert result > 0

        # Test end of year date
        end_year_date = "Mon, 31 Dec 2024 23:59:59 GMT"
        with patch("askui.utils.http_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(
                2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc
            )
            mock_datetime.strptime = datetime.strptime

            result = parse_retry_after_header(end_year_date)
            assert result > 0
