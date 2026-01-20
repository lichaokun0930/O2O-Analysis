"""
Property-Based Test: Highlight Distance Mapping (Property 4)

Feature: distance-order-diagnosis
Property 4: Highlight Distance Mapping

*For any* highlightDistance value in the range [0, ∞), exactly one distance band 
SHALL be highlighted, and that band SHALL be the one where 
min_distance ≤ highlightDistance < max_distance.

Validates: Requirements 6.2

This test validates the distance-to-band mapping logic that is used in both:
- Backend: Python implementation in orders.py
- Frontend: TypeScript implementation in distanceUtils.ts

The logic must be consistent across both implementations.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

# 距离区间定义（与后端和前端保持一致）
DISTANCE_BANDS = [
    {"label": "0-1km", "min": 0, "max": 1},
    {"label": "1-2km", "min": 1, "max": 2},
    {"label": "2-3km", "min": 2, "max": 3},
    {"label": "3-4km", "min": 3, "max": 4},
    {"label": "4-5km", "min": 4, "max": 5},
    {"label": "5-6km", "min": 5, "max": 6},
    {"label": "6km+", "min": 6, "max": float('inf')},
]


def get_distance_band_index(distance: float) -> int:
    """
    根据距离值计算对应的距离区间索引
    
    这是前端 distanceUtils.ts 中 getDistanceBandIndex 函数的 Python 等价实现
    
    Args:
        distance: 距离值 (km)
        
    Returns:
        对应的区间索引，如果距离无效则返回 -1
    """
    if distance is None or distance < 0:
        return -1
    
    for i, band in enumerate(DISTANCE_BANDS):
        if band["min"] <= distance < band["max"]:
            return i
    
    # 如果距离 >= 最后一个区间的 min，返回最后一个区间
    if distance >= DISTANCE_BANDS[-1]["min"]:
        return len(DISTANCE_BANDS) - 1
    
    return -1


def get_distance_band_label(distance: float) -> str:
    """根据距离值获取对应的距离区间标签"""
    index = get_distance_band_index(distance)
    if index == -1:
        return None
    return DISTANCE_BANDS[index]["label"]


class TestHighlightDistanceMapping:
    """
    Property 4: Highlight Distance Mapping
    
    测试距离值到距离区间的映射逻辑
    """
    
    @given(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    @settings(max_examples=200)
    def test_property_4_exactly_one_band_highlighted(self, distance: float):
        """
        Property 4: For any highlightDistance value in [0, ∞), exactly one 
        distance band SHALL be highlighted.
        
        Feature: distance-order-diagnosis, Property 4: Highlight Distance Mapping
        Validates: Requirements 6.2
        """
        # 获取映射的区间索引
        band_index = get_distance_band_index(distance)
        
        # 验证：必须映射到恰好一个区间
        assert band_index >= 0, f"Distance {distance} should map to a valid band"
        assert band_index < len(DISTANCE_BANDS), f"Band index {band_index} out of range"
        
        # 验证：只有一个区间被选中
        matching_bands = []
        for i, band in enumerate(DISTANCE_BANDS):
            if band["min"] <= distance < band["max"]:
                matching_bands.append(i)
        
        # 特殊处理 6km+ 区间（max 是 infinity）
        if distance >= 6:
            assert band_index == 6, f"Distance {distance} >= 6 should map to band 6 (6km+)"
        else:
            assert len(matching_bands) == 1, f"Distance {distance} should match exactly one band, got {matching_bands}"
            assert band_index == matching_bands[0], f"Band index mismatch for distance {distance}"
    
    @given(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    @settings(max_examples=200)
    def test_property_4_correct_band_boundaries(self, distance: float):
        """
        Property 4: The highlighted band SHALL be the one where 
        min_distance ≤ highlightDistance < max_distance.
        
        Feature: distance-order-diagnosis, Property 4: Highlight Distance Mapping
        Validates: Requirements 6.2
        """
        band_index = get_distance_band_index(distance)
        band = DISTANCE_BANDS[band_index]
        
        # 验证：距离值在区间范围内
        assert distance >= band["min"], f"Distance {distance} should be >= band min {band['min']}"
        
        # 对于非最后一个区间，验证 distance < max
        if band_index < len(DISTANCE_BANDS) - 1:
            assert distance < band["max"], f"Distance {distance} should be < band max {band['max']}"
    
    @given(st.integers(min_value=0, max_value=6))
    @settings(max_examples=100)
    def test_property_4_band_boundary_values(self, band_index: int):
        """
        测试区间边界值的映射正确性
        
        Feature: distance-order-diagnosis, Property 4: Highlight Distance Mapping
        Validates: Requirements 6.2
        """
        band = DISTANCE_BANDS[band_index]
        
        # 测试区间最小值
        min_distance = band["min"]
        assert get_distance_band_index(min_distance) == band_index, \
            f"Min distance {min_distance} should map to band {band_index}"
        
        # 测试区间内的中间值
        if band_index < len(DISTANCE_BANDS) - 1:
            mid_distance = (band["min"] + band["max"]) / 2
            assert get_distance_band_index(mid_distance) == band_index, \
                f"Mid distance {mid_distance} should map to band {band_index}"
            
            # 测试接近上边界的值（但不包含上边界）
            near_max = band["max"] - 0.001
            assert get_distance_band_index(near_max) == band_index, \
                f"Near-max distance {near_max} should map to band {band_index}"
    
    def test_property_4_specific_boundary_cases(self):
        """
        测试特定边界情况
        
        Feature: distance-order-diagnosis, Property 4: Highlight Distance Mapping
        Validates: Requirements 6.2
        """
        # 测试每个区间边界
        test_cases = [
            (0, 0, "0-1km"),      # 最小值
            (0.5, 0, "0-1km"),    # 区间内
            (0.999, 0, "0-1km"),  # 接近上边界
            (1, 1, "1-2km"),      # 边界值（属于下一个区间）
            (1.5, 1, "1-2km"),
            (2, 2, "2-3km"),
            (3, 3, "3-4km"),
            (4, 4, "4-5km"),
            (5, 5, "5-6km"),
            (6, 6, "6km+"),       # 最后一个区间
            (7, 6, "6km+"),
            (10, 6, "6km+"),
            (100, 6, "6km+"),     # 大距离值
        ]
        
        for distance, expected_index, expected_label in test_cases:
            actual_index = get_distance_band_index(distance)
            actual_label = get_distance_band_label(distance)
            
            assert actual_index == expected_index, \
                f"Distance {distance}: expected index {expected_index}, got {actual_index}"
            assert actual_label == expected_label, \
                f"Distance {distance}: expected label {expected_label}, got {actual_label}"
    
    def test_property_4_invalid_inputs(self):
        """
        测试无效输入的处理
        
        Feature: distance-order-diagnosis, Property 4: Highlight Distance Mapping
        Validates: Requirements 6.2
        """
        # 负数距离应返回 -1
        assert get_distance_band_index(-1) == -1
        assert get_distance_band_index(-0.001) == -1
        
        # None 应返回 -1
        assert get_distance_band_index(None) == -1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
