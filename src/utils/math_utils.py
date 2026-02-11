"""
数学工具函数

提供价格精度自适应等通用数学工具。
"""

import math


def smart_round(val: float, min_decimals: int = 2) -> float:
    """
    根据数值大小自动选择合适的小数位数

    大于等于1的数值使用 min_decimals 位小数；
    小于1的数值根据前导零数量自动扩展精度，确保小价格代币不被截断为0。

    Args:
        val: 待四舍五入的数值
        min_decimals: 最少保留的有效小数位数（默认2）

    Returns:
        四舍五入后的浮点数
    """
    if val == 0 or not math.isfinite(val):
        return 0.0
    abs_val = abs(val)
    if abs_val >= 1:
        return round(val, min_decimals)
    # 0.00000789 → -log10(0.00000789) ≈ 5.1 → 5个前导零 → 需要 5+2=7 位小数
    leading_zeros = int(math.floor(-math.log10(abs_val)))
    decimals = min(leading_zeros + min_decimals, 12)
    return round(val, decimals)
