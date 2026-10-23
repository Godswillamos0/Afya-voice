import os
import re
import sqlite3
from typing import List, Dict, Any

DB_PATH = os.path.join(os.getcwd(), "storage", "maternal_rag.db")
GUIDELINES_DIR = os.path.join(os.getcwd(), "storage", "guidelines_md")

class MaternalRAGIndexer:
    """
    Indexes WHO and Nigerian maternal healthcare guidelines into SQLite FTS5 for sub-millisecond retrieval.
    """
    def __init__(self, db_path: str = DB_PATH, guidelines_dir: str = GUIDELINES_DIR):
        self.db_path = db_path
        self.guidelines_dir = guidelines_dir
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initializes relational and FTS5 tables in SQLite."""
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        # Main storage table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS maternal_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_name TEXT NOT NULL,
                doc_title TEXT NOT NULL,
                section_title TEXT NOT NULL,
                content TEXT NOT NULL,
                urgency_indicator TEXT,
                trimester_focus TEXT
            )
        """)

        # Drop and recreate FTS5 virtual table for indexing
        cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS maternal_fts USING fts5(doc_name, doc_title, section_title, content);")
        con.commit()
        con.close()

    def parse_markdown_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Splits a markdown document by section headers (##) into semantic clinical chunks."""
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        file_name = os.path.basename(file_path)
        lines = text.split("\n")
        
        doc_title = "WHO & Nigeria Maternal Healthcare Guidelines"
        for l in lines:
            if l.startswith("# "):
                doc_title = l.replace("# ", "").strip()
                break

        # Split on section headings (## )
        sections = re.split(r'\n(?=##\s+)', text)
        chunks = []

        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue

            sec_lines = sec.split("\n")
            header_line = sec_lines[0].replace("#", "").strip() if sec_lines[0].startswith("#") else "General Guidance"
            content = "\n".join(sec_lines[1:]).strip() if sec_lines[0].startswith("#") else sec

            if len(content) < 40:
                continue

            # Determine urgency indicator
            urgency = "ROUTINE"
            content_lower = content.lower()
            if any(w in content_lower for w in ["emergency", "severe pre-eclampsia", "eclampsia", "haemorrhage", "bleeding", "cord prolapse", "convulsion", "abruption"]):
                urgency = "EMERGENCY"
            elif any(w in content_lower for w in ["urgent", "hyperemesis", "pyelonephritis", "dysuria", "reduced fetal", "fever"]):
                urgency = "URGENT"

            # Determine trimester focus
            trimester = "ALL_STAGES"
            if "first trimester" in content_lower or "contact 1" in content_lower or "booking" in content_lower:
                trimester = "FIRST_TRIMESTER"
            elif "second trimester" in content_lower or "iptp" in content_lower or "20 weeks" in content_lower:
                trimester = "SECOND_TRIMESTER"
            elif "third trimester" in content_lower or "36 weeks" in content_lower or "labor" in content_lower or "abruption" in content_lower:
                trimester = "THIRD_TRIMESTER"
            elif "postnatal" in content_lower or "postpartum" in content_lower or "breastfeeding" in content_lower or "newborn" in content_lower:
                trimester = "POSTNATAL"

            chunks.append({
                "doc_name": file_name,
                "doc_title": doc_title,
                "section_title": header_line,
                "content": content,
                "urgency": urgency,
                "trimester": trimester
            })

        return chunks

    def build_index(self) -> int:
        """Indexes all markdown files in the guidelines directory."""
        if not os.path.exists(self.guidelines_dir):
            print(f"[RAG Indexer] Guidelines directory not found: {self.guidelines_dir}")
            return 0

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()

        # Clear existing entries
        cur.execute("DELETE FROM maternal_chunks")
        cur.execute("DELETE FROM maternal_fts")

        total_indexed = 0
        for f in os.listdir(self.guidelines_dir):
            if f.endswith(".md"):
                file_path = os.path.join(self.guidelines_dir, f)
                chunks = self.parse_markdown_file(file_path)
                
                for c in chunks:
                    cur.execute("""
                        INSERT INTO maternal_chunks (doc_name, doc_title, section_title, content, urgency_indicator, trimester_focus)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (c["doc_name"], c["doc_title"], c["section_title"], c["content"], c["urgency"], c["trimester"]))
                    
                    # Insert into FTS5
                    cur.execute("""
                        INSERT INTO maternal_fts (doc_name, doc_title, section_title, content)
                        VALUES (?, ?, ?, ?)
                    """, (c["doc_name"], c["doc_title"], c["section_title"], c["content"]))
                    
                    total_indexed += 1

        con.commit()
        con.close()
        print(f"[RAG Indexer] Successfully indexed {total_indexed} clinical maternal guidelines into {self.db_path}")
        return total_indexed

if __name__ == "__main__":
    indexer = MaternalRAGIndexer()
    indexer.build_index()
