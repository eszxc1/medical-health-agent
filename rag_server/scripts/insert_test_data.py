"""
联调测试数据插入脚本
===================
用途：为指定用户插入逼真的健康数据，验证 Agent 的记忆能力和药物冲突检测。
执行方式：cd rag_server && python scripts/insert_test_data.py
"""

import sys
import os

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.MySQLUtil import execute_query, execute_insert, execute_update
from common.UserUtil import resolve_user_id


def insert_test_data(email: str):
    """
    为指定用户插入完整的测试健康数据。
    场景设定：55 岁男性，高血压 + 2 型糖尿病，青霉素过敏，正在服用硝苯地平和二甲双胍。
    """
    print(f"\n{'='*60}")
    print(f"为 {email} 插入测试健康数据")
    print(f"{'='*60}")

    # 1. 解析 user_id
    try:
        user_id = resolve_user_id(email)
        print(f"[OK] 用户存在: user_id={user_id}")
    except ValueError:
        print(f"[ERROR] 用户 {email} 不存在，请先在登录页面注册该用户")
        return

    # 2. 插入健康画像
    print("\n[1/4] 插入健康画像...")
    existing = execute_query("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    if existing:
        print(f"  [SKIP] 画像已存在，跳过")
    else:
        execute_insert("""
            INSERT INTO user_profiles
                (user_id, age, gender, height_cm, weight_kg, blood_type,
                 smoking_status, alcohol_consumption, exercise_frequency)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, 55, 'male', 172.0, 78.0, 'A', 'former', 'occasional', '每周2次'))
        print(f"  [OK] 画像已插入: 55岁男性, 172cm/78kg, A型血, 戒烟, 偶尔饮酒, 每周运动2次")

    # 3. 插入过敏史
    print("\n[2/4] 插入过敏史...")
    allergies = [
        ("青霉素", "severe"),
        ("磺胺类药物", "moderate"),
        ("花粉", "mild"),
    ]
    for name, severity in allergies:
        result = execute_insert(
            "INSERT IGNORE INTO user_allergies (user_id, allergy_name, severity) VALUES (%s, %s, %s)",
            (user_id, name, severity)
        )
        status = "[OK]" if result else "[SKIP] 已存在"
        print(f"  {status} {name} (严重程度: {severity})")

    # 4. 插入慢性病
    print("\n[3/4] 插入慢性病...")
    diseases = [
        ("高血压", "2020-03-15", "2级高血压，血压控制尚可，需每日监测"),
        ("2型糖尿病", "2021-06-20", "空腹血糖控制在7.0mmol/L左右，糖化血红蛋白6.5%"),
        ("高脂血症", "2022-01-10", "轻度，通过饮食控制"),
    ]
    for name, date, notes in diseases:
        result = execute_insert(
            "INSERT IGNORE INTO user_chronic_diseases (user_id, disease_name, diagnosed_date, notes) VALUES (%s, %s, %s, %s)",
            (user_id, name, date, notes)
        )
        status = "[OK]" if result else "[SKIP] 已存在"
        print(f"  {status} {name} (确诊: {date})")

    # 5. 插入当前用药
    print("\n[4/4] 插入当前用药...")
    medications = [
        ("硝苯地平", "30mg", "每日一次", "2020-04-01"),
        ("二甲双胍", "500mg", "每日两次", "2021-07-01"),
        ("阿托伐他汀", "20mg", "每日一次", "2022-02-01"),
    ]
    for name, dosage, freq, date in medications:
        result = execute_insert(
            """INSERT INTO user_medications (user_id, medication_name, dosage, frequency, started_date)
               VALUES (%s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE dosage=VALUES(dosage), frequency=VALUES(frequency), is_active=1""",
            (user_id, name, dosage, freq, date)
        )
        status = "[OK]" if result else "[SKIP] 已存在"
        print(f"  {status} {name} {dosage} {freq} (开始: {date})")

    print(f"\n{'='*60}")
    print("测试数据插入完成！")
    print(f"用户 {email} 的健康画像:")
    print(f"  - 过敏史: 青霉素(重度), 磺胺类药物(中度), 花粉(轻度)")
    print(f"  - 慢性病: 高血压, 2型糖尿病, 高脂血症")
    print(f"  - 当前用药: 硝苯地平, 二甲双胍, 阿托伐他汀")
    print(f"{'='*60}")
    print("现在可以在前端问 Agent: '记得我的过敏史吗？' 或 '我现在在吃什么药？'")


if __name__ == '__main__':
    # 默认使用当前登录用户的邮箱，也可以从命令行参数传入
    email = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    insert_test_data(email)