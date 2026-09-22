"""
日期标准化工具
==============
用途：将用户描述的相对时间（如"昨天"、"3个月前"、"半年前"、"大半年"）转换为绝对日期 YYYY-MM-DD。

为什么放在 Python 工具层而非交给 LLM 计算？
—— LLM 做日期算术（如推算"3个月前是几号"）容易出错，且涉及月末/闰年等边界。
   由 Python 的 datetime 库计算，保证入库数据的绝对准确性。

使用方式：
    from common.DateUtil import parse_relative_date, get_current_date
"""

import re
from datetime import date, timedelta


def _days_in_month(year, month):
    """返回指定年月的天数"""
    if month == 12:
        return (date(year + 1, 1, 1) - date(year, month, 1)).days
    return (date(year, month + 1, 1) - date(year, month, 1)).days


def _subtract_months(d, months):
    """
    从日期 d 减去 months 个月，返回新日期。
    处理月末溢出：如 3月31日 减 1个月 → 2月28/29日。
    """
    month_index = d.month - 1 - months  # 0-indexed 月
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, _days_in_month(year, month))
    return date(year, month, day)


def _subtract_years_same_day(d, years):
    """
    从日期 d 减去 years 年，保持月日不变。
    处理闰年边界：如 2024年2月29日 减 1年 → 2023年2月28日（非闰年）。
    """
    try:
        return date(d.year - years, d.month, d.day)
    except ValueError:
        # 2月29日 减到非闰年 → 回退到 2月28日
        return date(d.year - years, d.month, 28)


def get_current_date():
    """返回当前日期对象"""
    return date.today()


def get_weekday_cn(d=None):
    """返回中文星期几（如"周六"）"""
    if d is None:
        d = date.today()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return weekdays[d.weekday()]


def parse_relative_date(description, reference_date=None):
    """
    将时间描述（相对或绝对）转换为绝对日期字符串 YYYY-MM-DD。

    支持的格式：
    - 绝对日期: 2026-08-14 / 2026/08/14 / 2026年8月14日
    - 相对时间: 今天 / 昨天 / 前天 / 大半年 / 半年 / 半个月 /
               X天前 / X周前 / X个月前 / X年前 / 去年 / 前年 / 上周 / 上个月 /
               年初 / 年中 / 年底 / 去年这个时候

    返回:
        解析成功 → "YYYY-MM-DD" 字符串
        无法解析 → None（调用方需自行处理，优雅降级）
    """
    if reference_date is None:
        reference_date = date.today()

    if not description:
        return None

    text = str(description).strip()

    # ===== 1. 绝对日期格式 =====
    # YYYY-MM-DD
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    # YYYY/MM/DD
    m = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', text)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    # YYYY年M月D日
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日?', text)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()

    # ===== 2. 相对时间 =====
    # 今天 / 昨天 / 前天
    if "今天" in text or "今日" in text:
        return reference_date.isoformat()
    if "昨天" in text or "昨日" in text:
        return (reference_date - timedelta(days=1)).isoformat()
    if "前天" in text:
        return (reference_date - timedelta(days=2)).isoformat()

    # 大半年（约8个月）—— 必须在"半年"之前匹配，因为"大半年"包含"半年"子串
    if "大半年" in text:
        return _subtract_months(reference_date, 8).isoformat()
    # 半年前 / 半年
    if "半年前" in text or "半年" in text:
        return _subtract_months(reference_date, 6).isoformat()
    # 半个月前
    if "半个月前" in text or "半个月" in text:
        return (reference_date - timedelta(days=15)).isoformat()

    # 去年这个时候 / 去年的今天（去年同月同日）
    if "去年这个时候" in text or "去年的今天" in text:
        return _subtract_years_same_day(reference_date, 1).isoformat()
    # 前年（两年前）
    if "前年" in text:
        return _subtract_years_same_day(reference_date, 2).isoformat()
    # 去年
    if "去年" in text:
        return _subtract_months(reference_date, 12).isoformat()

    # 年初 / 年中 / 年底
    if "年初" in text:
        return date(reference_date.year, 1, 1).isoformat()
    if "年底" in text or "年末" in text:
        return date(reference_date.year, 12, 31).isoformat()
    if "年中" in text:
        return date(reference_date.year, 6, 30).isoformat()

    # X天前
    m = re.search(r'(\d+)\s*天前', text)
    if m:
        return (reference_date - timedelta(days=int(m.group(1)))).isoformat()

    # X周前 / X个星期前
    m = re.search(r'(\d+)\s*(?:个)?(?:周|星期)前', text)
    if m:
        return (reference_date - timedelta(weeks=int(m.group(1)))).isoformat()

    # X个月前（注意：必须在"X年前"之前匹配，避免歧义）
    m = re.search(r'(\d+)\s*个?月前', text)
    if m:
        return _subtract_months(reference_date, int(m.group(1))).isoformat()

    # X年前
    m = re.search(r'(\d+)\s*年?前', text)
    if m:
        return _subtract_months(reference_date, int(m.group(1)) * 12).isoformat()

    # 上周
    if "上周" in text:
        return (reference_date - timedelta(days=7)).isoformat()

    # 上个月
    if "上个月" in text or "上月" in text:
        return _subtract_months(reference_date, 1).isoformat()

    # 无法解析
    return None


if __name__ == '__main__':
    # 简单自测
    today = date.today()
    print(f"今天: {today}")
    print(f"昨天: {parse_relative_date('昨天')}")
    print(f"前天: {parse_relative_date('前天')}")
    print(f"3天前: {parse_relative_date('3天前')}")
    print(f"3个月前: {parse_relative_date('3个月前')}")
    print(f"半年前: {parse_relative_date('半年前')}")
    print(f"大半年: {parse_relative_date('大半年')}")
    print(f"1年前: {parse_relative_date('1年前')}")
    print(f"去年: {parse_relative_date('去年')}")
    print(f"前年: {parse_relative_date('前年')}")
    print(f"去年这个时候: {parse_relative_date('去年这个时候')}")
    print(f"年初: {parse_relative_date('年初')}")
    print(f"绝对日期: {parse_relative_date('2024-01-15')}")
    print(f"中文日期: {parse_relative_date('2024年1月15日')}")
    print(f"无法解析: {parse_relative_date('很久以前')}")
