"""
Neo4j 医疗知识图谱批量导入脚本（在容器内运行）
====================================================
- 方式：Cypher UNWIND 批量导入（每批 5000 行），不依赖 APOC
- 数据源：/import/nodes/*.csv 与 /import/relations/*.csv（容器内挂载）
- 连接：bolt://neo4j:7687（Docker 内部服务名）
- 账号：neo4j，密码从环境变量 NEO4J_PASSWORD 读取（不硬编码）

幂等：默认若图谱已有数据则跳过；设 SKIP_IF_EXISTS=0 可强制重新导入。
"""
import os
import csv
import sys
import time

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
CSV_DIR = os.getenv("CSV_DIR", "/import")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5000"))
SKIP_IF_EXISTS = os.getenv("SKIP_IF_EXISTS", "1") == "1"

# 9 类节点（与 Neo4j schema 一致，Disease 为核心）
NODE_LABELS = [
    "Disease", "Symptom", "Check", "Drug",
    "Department", "Food", "Dishes", "Category", "Cureway",
]

# 10 类关系：关系类型 -> 终点节点 label（起点恒为 Disease）
RELATIONS = {
    "DISEASE_SYMPTOM": "Symptom",
    "DISEASE_CHECK": "Check",
    "DISEASE_CUREWAY": "Cureway",
    "DISEASE_DRUG": "Drug",
    "DISEASE_DEPARTMENT": "Department",
    "DISEASE_DO_EAT": "Food",
    "DISEASE_NOT_EAT": "Food",
    "DISEASE_DISHES": "Dishes",
    "DISEASE_ACOMPANY": "Disease",
    "DISEASE_CATEGORY": "Category",
}


def read_csv(path):
    """读 CSV，返回 list[dict]；utf-8-sig 去掉 BOM，newline 防跨行字段错读。"""
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def chunks(rows, size):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def create_constraints(session):
    """为每个 label 的 name 建唯一约束，加速 MATCH（幂等）。

    - 约束已存在：IF NOT EXISTS 会静默跳过，不报错。
    - 约束创建失败（通常是 CSV 中该 label 的 name 有重复值）：捕获异常并打印清晰提示，不中断。
    """
    for label in NODE_LABELS:
        try:
            session.run(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE"
            )
        except Exception as e:
            print(f"[WARN] 节点 {label} 唯一约束创建失败：{type(e).__name__}: {e}")
            print(f"       若因 name 字段存在重复值，请检查 {label}.csv")
    print("[OK] 唯一约束处理完成")


def import_nodes(session, label):
    path = os.path.join(CSV_DIR, "nodes", f"{label}.csv")
    if not os.path.exists(path):
        print(f"  [SKIP] {label}: 缺少 {path}")
        return
    rows = read_csv(path)
    if not rows:
        print(f"  [SKIP] {label}: 无数据")
        return
    cypher = f"UNWIND $rows AS row MERGE (n:{label} {{name: row.name}}) SET n += row"
    total = 0
    for batch in chunks(rows, BATCH_SIZE):
        session.run(cypher, rows=batch)
        total += len(batch)
    print(f"  [OK] {label}: {total} 个节点")


def import_relations(session, rel_type, end_label):
    path = os.path.join(CSV_DIR, "relations", f"{rel_type}.csv")
    if not os.path.exists(path):
        print(f"  [SKIP] {rel_type}: 缺少 {path}")
        return
    rows = read_csv(path)
    if not rows:
        print(f"  [SKIP] {rel_type}: 无数据")
        return
    cypher = (
        "UNWIND $rows AS row "
        "MATCH (a:Disease {name: row.from}) "
        f"MATCH (b:{end_label} {{name: row.to}}) "
        f"MERGE (a)-[r:{rel_type}]->(b)"
    )
    total = 0
    for batch in chunks(rows, BATCH_SIZE):
        session.run(cypher, rows=batch)
        total += len(batch)
    print(f"  [OK] {rel_type}: {total} 条关系")


def wait_for_neo4j(driver, retries=30, delay=2):
    for i in range(retries):
        try:
            driver.verify_connectivity()
            print("[OK] Neo4j 已就绪")
            return
        except Exception as e:
            print(f"[WAIT] Neo4j 未就绪 ({i + 1}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Neo4j 长时间未就绪，导入终止")


def already_imported(session):
    result = session.run("MATCH (n:Disease) RETURN count(n) AS c").single()
    return bool(result and result["c"] > 0)


def main():
    if not NEO4J_PASSWORD:
        print("[ERROR] 缺少环境变量 NEO4J_PASSWORD")
        sys.exit(1)

    print(f"[INFO] 连接 {NEO4J_URI} (user={NEO4J_USER})")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        wait_for_neo4j(driver)
        with driver.session() as session:
            if SKIP_IF_EXISTS and already_imported(session):
                print("[SKIP] 图谱已有数据，跳过导入（设 SKIP_IF_EXISTS=0 可强制重导）")
                return

            print("== 1/3 建约束 ==")
            create_constraints(session)

            print("== 2/3 导入节点 ==")
            for label in NODE_LABELS:
                import_nodes(session, label)

            print("== 3/3 导入关系 ==")
            for rel_type, end_label in RELATIONS.items():
                import_relations(session, rel_type, end_label)

        print("[DONE] 图谱数据导入完成")
    finally:
        driver.close()


if __name__ == "__main__":
    main()