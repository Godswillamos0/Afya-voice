import os
import re
import sqlite3
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.getcwd(), "storage", "maternal_rag.db")

INDIGENOUS_CLINICAL_MAP = {
    # Yoruba terms
    "eje": ["vaginal bleeding", "haemorrhage", "antepartum", "miscarriage", "abruption"],
    "ori fifo": ["severe headache", "pre-eclampsia", "eclampsia", "hypertension", "magnesium sulfate"],
    "oju dudu": ["blurred vision", "scotomata", "pre-eclampsia"],
    "ara gbona": ["fever", "malaria in pregnancy", "IPTp-SP", "sepsis", "chorioamnionitis"],
    "inu rirun": ["abdominal pain", "placental abruption", "ectopic", "uterine contractions"],
    "eebi": ["vomiting", "morning sickness", "hyperemesis gravidarum", "ginger"],
    "omo o gbon": ["reduced fetal movements", "fetal kick count", "fetal distress"],
    "aare": ["maternal fatigue", "anaemia", "iron supplementation"],
    
    # Nigerian Pidgin terms
    "dey bleed": ["vaginal bleeding", "haemorrhage", "antepartum", "miscarriage"],
    "head dey pain": ["severe headache", "pre-eclampsia", "hypertension"],
    "eye dey turn": ["blurred vision", "dizziness", "pre-eclampsia"],
    "belle pain": ["abdominal pain", "labor contractions", "placental abruption"],
    "hot body": ["fever", "malaria in pregnancy", "infection", "sepsis"],
    "pikin no dey kick": ["reduced fetal movement", "fetal distress", "kick count"],
    "throw up": ["vomiting", "morning sickness", "hyperemesis gravidarum"],
    
    # Hausa terms
    "zubar jini": ["vaginal bleeding", "haemorrhage", "miscarriage"],
    "ciwon kai": ["severe headache", "pre-eclampsia", "hypertension"],
    "zazzabi": ["fever", "malaria in pregnancy", "infection"],
    "ciwon ciki": ["abdominal pain", "labor contractions"],
    "amai": ["vomiting", "nausea", "morning sickness"],
    
    # Igbo terms
    "obara": ["bleeding", "haemorrhage", "miscarriage"],
    "isi owuwa": ["severe headache", "pre-eclampsia"],
    "ahu oku": ["fever", "malaria in pregnancy"],
    "afo ogbugba": ["abdominal pain", "cramping"],
    "onunu": ["vomiting", "morning sickness"]
}

class MaternalRAGRetriever:
    """
    Retrieves evidence-based maternal care recommendations from indexed WHO & Nigerian Health Guidelines.
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def expand_query(self, query: str) -> List[str]:
        """Expands indigenous and colloquial phrases into clinical medical search keywords."""
        q_lower = query.lower()
        expanded_terms = []

        # Check for indigenous keywords
        for phrase, clinical_synonyms in INDIGENOUS_CLINICAL_MAP.items():
            if phrase in q_lower:
                expanded_terms.extend(clinical_synonyms)

        # Standard English pregnancy mappings
        if "bleed" in q_lower or "blood" in q_lower or "spotting" in q_lower:
            expanded_terms.extend(["vaginal bleeding", "antepartum haemorrhage", "placenta praevia", "abruption", "miscarriage"])
        if "headache" in q_lower or "head" in q_lower or "vision" in q_lower or "blurry" in q_lower:
            expanded_terms.extend(["severe pre-eclampsia", "eclampsia", "magnesium sulfate", "hypertension", "blurred vision"])
        if "fever" in q_lower or "chills" in q_lower:
            expanded_terms.extend(["malaria in pregnancy", "IPTp-SP", "chorioamnionitis", "puerperal sepsis", "fever"])
        if "vomit" in q_lower or "nausea" in q_lower or "morning sickness" in q_lower:
            expanded_terms.extend(["nausea vomiting", "hyperemesis gravidarum", "ginger", "hydration"])
        if "cramp" in q_lower or "stomach" in q_lower or "belly" in q_lower or "labor" in q_lower or "contraction" in q_lower:
            expanded_terms.extend(["abdominal pain", "true labor", "Braxton Hicks", "placental abruption"])
        if "movement" in q_lower or "kick" in q_lower:
            expanded_terms.extend(["fetal movements", "fetal kick counts", "fetal distress"])
        if "supplement" in q_lower or "blood tablet" in q_lower or "iron" in q_lower or "folic" in q_lower or "food" in q_lower:
            expanded_terms.extend(["iron and folic acid", "anaemia", "nutrition", "calcium"])

        return list(set(expanded_terms))

    def retrieve(self, query: str, top_k: int = 3, gestational_stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """Performs hybrid retrieval using SQLite FTS5 BM25 search across maternal guidelines."""
        if not os.path.exists(self.db_path):
            print(f"[RAG Retriever] Warning: Database {self.db_path} does not exist yet.")
            return []

        expanded_keywords = self.expand_query(query)
        
        # Clean user query for FTS5 (remove punctuation)
        clean_words = re.findall(r'\b[A-Za-z0-9_-]{3,}\b', query)
        all_terms = list(set(clean_words + expanded_keywords))

        if not all_terms:
            all_terms = ["antenatal", "maternal", "care"]

        # Build FTS5 query with OR terms for broad high-recall matching
        fts_match_query = " OR ".join([f'"{term}"' for term in all_terms[:12]])

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()

        results = []
        try:
            # Query FTS5 matching on maternal_chunks
            cur.execute("""
                SELECT c.id, c.doc_name, c.doc_title, c.section_title, c.content, c.urgency_indicator, c.trimester_focus, bm25(maternal_fts) as rank
                FROM maternal_chunks c
                JOIN maternal_fts f ON c.id = f.rowid
                WHERE maternal_fts MATCH ?
                ORDER BY rank ASC
                LIMIT ?
            """, (fts_match_query, top_k * 2))

            rows = cur.fetchall()

            for r in rows:
                chunk_id, doc_name, doc_title, sec_title, content, urgency, trimester, rank = r
                
                # Check for trimester prioritization
                score_boost = 0
                if gestational_stage and trimester != "ALL_STAGES":
                    if gestational_stage.upper() in trimester:
                        score_boost = -1.0 # Negative BM25 is better rank

                results.append({
                    "id": chunk_id,
                    "doc_name": doc_name,
                    "doc_title": doc_title,
                    "section_title": sec_title,
                    "content": content,
                    "urgency": urgency,
                    "trimester": trimester,
                    "rank_score": rank + score_boost
                })
        except Exception as e:
            print(f"[RAG Retriever] FTS query error ({str(e)}), falling back to keyword search.")
            # Simple fallback
            cur.execute("SELECT id, doc_name, doc_title, section_title, content, urgency_indicator, trimester_focus FROM maternal_chunks LIMIT ?", (top_k,))
            for r in cur.fetchall():
                results.append({
                    "id": r[0],
                    "doc_name": r[1],
                    "doc_title": r[2],
                    "section_title": r[3],
                    "content": r[4],
                    "urgency": r[5],
                    "trimester": r[6],
                    "rank_score": 0.0
                })
        finally:
            con.close()

        # Sort by rank score and slice to top_k
        results.sort(key=lambda x: x["rank_score"])
        return results[:top_k]

    def format_guideline_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Formats retrieved clinical chunks into an authoritative medical context block for the LLM."""
        if not retrieved_chunks:
            return "No specific guideline chunks retrieved. Apply general WHO Antenatal Care safety protocols."

        context_blocks = []
        for i, c in enumerate(retrieved_chunks, 1):
            source_tag = f"[{c['doc_title']} - {c['section_title']}]"
            context_blocks.append(
                f"### Evidence #{i}: {source_tag}\n"
                f"Urgency Standard: {c['urgency']}\n"
                f"Guideline Text:\n{c['content']}\n"
            )

        return "\n".join(context_blocks)

if __name__ == "__main__":
    retriever = MaternalRAGRetriever()
    test_q = "I am 7 months pregnant with severe headache and blurry vision"
    chunks = retriever.retrieve(test_q)
    print(f"Retrieved {len(chunks)} chunks for query: '{test_q}'")
    for ch in chunks:
        print(f"- [{ch['urgency']}] {ch['doc_title']} -> {ch['section_title']}")
