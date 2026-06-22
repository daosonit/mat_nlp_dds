import os
import json
import pytest
from detection import TeencodeDetector


@pytest.fixture
def mock_dictionary(tmp_path):
    """Tạo file dictionary giả lập để test."""
    dict_file = tmp_path / "mock_teencode.json"
    mock_data = {
        "dc": "được",
        "ko": "không",
        "j": "gì",  # Từ 1 ký tự, sẽ bị lọc bỏ
        "r": "rồi",  # Từ 1 ký tự, sẽ bị lọc bỏ
        "lun": "luôn",
        "hok": "không",
    }
    with open(dict_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)
    return str(dict_file)


def test_detector_filters_single_chars(mock_dictionary):
    detector = TeencodeDetector(mock_dictionary)
    # j, r sẽ bị lọc, chỉ còn dc, ko, lun, hok
    assert len(detector._strong_set) == 4
    assert "j" not in detector._strong_set
    assert "r" not in detector._strong_set
    assert "dc" in detector._strong_set


def test_detector_detects_teencode(mock_dictionary):
    detector = TeencodeDetector(mock_dictionary, min_matches=1)

    # Text bình thường
    assert detector.detect("hôm nay tôi đi học") is False
    # Text có từ 1 ký tự nằm trong blacklist nhưng bị filter out
    assert detector.detect("anh j r") is False

    # Text chứa teencode
    assert detector.detect("hôm nay ko đi học") is True
    assert detector.detect("đẹp lun") is True


def test_detector_ratio_threshold(mock_dictionary):
    detector = TeencodeDetector(mock_dictionary, min_matches=99, ratio_threshold=0.3)

    # Câu có 4 từ, 1 từ teencode (tỷ lệ 0.25) -> False (0.25 < 0.3)
    assert detector.detect("hôm nay ko đi") is False

    # Câu có 3 từ, 1 từ teencode (tỷ lệ 0.33) -> True (0.33 > 0.3)
    assert detector.detect("ko đi học") is True
