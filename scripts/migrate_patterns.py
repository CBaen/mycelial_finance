# BIG ROCK 48: Migrate existing patterns to include moat categorization
import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)

# Step 1: Add moat columns to existing database
conn = sqlite3.connect('mycelial_patterns.db')
cursor = conn.cursor()

try:
    # Add new columns
    cursor.execute("ALTER TABLE patterns ADD COLUMN moat TEXT DEFAULT 'Finance'")
    cursor.execute("ALTER TABLE patterns ADD COLUMN product TEXT DEFAULT 'Unknown'")
    cursor.execute("ALTER TABLE patterns ADD COLUMN signal_type TEXT DEFAULT 'market-data'")
    logging.info("Added moat, product, signal_type columns to patterns table")
except Exception as e:
    logging.warning(f"Columns may already exist: {e}")

# Step 2: Categorize existing patterns by agent_id
# Agent IDs 1-18 are DataEngineers (Finance moat)
# Agent IDs 19 is RepoScraper (Code moat)
# Agent ID 20 is LogisticsMiner (Logistics moat)
# Agent ID 21 is GovtDataMiner (Government moat)
# Agent ID 22 is CorpDataMiner (Corporations moat)
# Agent IDs 23+ are SwarmBrains (mixed)

cursor.execute("UPDATE patterns SET moat = 'Finance', product = 'Crypto Markets', signal_type = 'market-data' WHERE agent_id BETWEEN 1 AND 18")
cursor.execute("UPDATE patterns SET moat = 'Code Innovation', product = 'Code', signal_type = 'repo-data' WHERE agent_id = 19")
cursor.execute("UPDATE patterns SET moat = 'Logistics', product = 'Logistics', signal_type = 'logistics-data' WHERE agent_id = 20")
cursor.execute("UPDATE patterns SET moat = 'Government', product = 'Government', signal_type = 'govt-data' WHERE agent_id = 21")
cursor.execute("UPDATE patterns SET moat = 'US Corporations', product = 'Corporations', signal_type = 'corp-data' WHERE agent_id = 22")

# SwarmBrains are distributed across all moats - categorize by modulo
cursor.execute("""
    UPDATE patterns
    SET moat = CASE
        WHEN (agent_id % 5) = 0 THEN 'Finance'
        WHEN (agent_id % 5) = 1 THEN 'Code Innovation'
        WHEN (agent_id % 5) = 2 THEN 'Logistics'
        WHEN (agent_id % 5) = 3 THEN 'Government'
        ELSE 'US Corporations'
    END,
    product = CASE
        WHEN (agent_id % 5) = 0 THEN 'Crypto Markets'
        WHEN (agent_id % 5) = 1 THEN 'Code'
        WHEN (agent_id % 5) = 2 THEN 'Logistics'
        WHEN (agent_id % 5) = 3 THEN 'Government'
        ELSE 'Corporations'
    END
    WHERE agent_id >= 23
""")

conn.commit()

# Step 3: Verify migration
cursor.execute("SELECT moat, COUNT(*) FROM patterns GROUP BY moat")
moat_counts = cursor.fetchall()

logging.info("\n=== MIGRATION COMPLETE ===")
logging.info("Pattern distribution by moat:")
for moat, count in moat_counts:
    logging.info(f"  {moat}: {count} patterns")

cursor.execute("SELECT COUNT(*) FROM patterns")
total = cursor.fetchone()[0]
logging.info(f"\nTotal patterns: {total}")

conn.close()
logging.info("\nDatabase migration successful!")
