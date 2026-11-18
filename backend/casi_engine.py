"""
CASI (Clinical Abbreviation Sense Inventory) Context Disambiguation Engine.
Indexes the official CASI dataset (37,500 clinical note contexts across 75 abbreviations).
Provides context-aware sense classification with confidence scoring, evidence extraction,
and section alignment.
"""

import os
import re
import math
from collections import defaultdict, Counter

class CasiEngine:
    def __init__(self, data_path=None):
        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "casi_reference", "AnonymizedClinicalAbbreviationsAndAcronymsDataSet.txt")
        self.data_path = data_path
        self.is_loaded = False
        
        # Abbreviation data structures
        self.abbr_senses = defaultdict(Counter)  # abbr -> sense -> count
        self.sense_word_counts = defaultdict(lambda: defaultdict(Counter)) # abbr -> sense -> word -> count
        self.sense_total_words = defaultdict(lambda: defaultdict(int)) # abbr -> sense -> total_words
        self.sense_doc_freq = defaultdict(Counter) # abbr -> word -> num_senses_containing_word
        self.sense_sections = defaultdict(lambda: defaultdict(Counter)) # abbr -> sense -> section -> count
        self.sense_examples = defaultdict(lambda: defaultdict(list)) # abbr -> sense -> list of sample sentences
        
        # Ignored / stop words and CASI de-identification tags
        self.stop_words = set([
            "the", "and", "a", "an", "of", "to", "in", "is", "was", "for", "with", "on", "as", "at", "by", "this",
            "that", "from", "she", "he", "it", "her", "his", "patient", "pt", "there", "are", "were", "be", "has",
            "had", "have", "been", "or", "not", "no", "who", "which", "will", "would", "can", "could", "also",
            "name", "year", "old", "presented", "complaining", "admitted", "history", "hospital",
            "_%#name#%_", "_%#1999#%_", "_%#mm2006#%_", "_%#mmdd#%_", "_%#mm#%_", "_%#city#%_", "_%#date#%_",
            "_%#year#%_", "_%#month#%_", "_%#state#%_", "_%#hospital#%_", "_%#clinic#%_"
        ])

    def load(self):
        """Parse and index CASI dataset into memory."""
        if self.is_loaded:
            return True
        if not os.path.exists(self.data_path):
            print(f"Warning: CASI file not found at {self.data_path}")
            return False

        with open(self.data_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 7:
                    abbr = parts[0].strip().upper()
                    sense = parts[1].strip()
                    section = parts[5].strip().upper() if parts[5].strip() else "GENERAL"
                    context = parts[6].strip()

                    self.abbr_senses[abbr][sense] += 1
                    self.sense_sections[abbr][sense][section] += 1
                    
                    if len(self.sense_examples[abbr][sense]) < 4:
                        self.sense_examples[abbr][sense].append({
                            "context": context,
                            "section": section
                        })

                    # Extract words
                    words = set(re.findall(r"\b[a-zA-Z]{3,}\b", context.lower()))
                    filtered_words = [w for w in words if w not in self.stop_words and w != abbr.lower()]
                    
                    for w in filtered_words:
                        self.sense_word_counts[abbr][sense][w] += 1
                        self.sense_total_words[abbr][sense] += 1

        # Calculate document frequency across senses
        for abbr, senses in self.sense_word_counts.items():
            for sense, word_counts in senses.items():
                for w in word_counts:
                    self.sense_doc_freq[abbr][w] += 1

        self.is_loaded = True
        return True

    def get_statistics(self):
        """Return dataset statistics."""
        if not self.is_loaded:
            self.load()
        total_rows = sum(sum(s.values()) for s in self.abbr_senses.values())
        return {
            "dataset_name": "Clinical Abbreviation Sense Inventory (CASI)",
            "total_records": total_rows,
            "unique_abbreviations": len(self.abbr_senses),
            "reference": "Moon et al. (University of Minnesota) / NLM / PhysioNet",
            "abbreviations_list": sorted(list(self.abbr_senses.keys()))
        }

    def get_abbreviation_detail(self, abbr):
        """Return details and sense distributions for an abbreviation."""
        if not self.is_loaded:
            self.load()
        abbr = abbr.upper()
        if abbr not in self.abbr_senses:
            return None
        
        senses = self.abbr_senses[abbr]
        total = sum(senses.values())
        
        senses_summary = []
        for sense, count in sorted(senses.items(), key=lambda x: x[1], reverse=True):
            pct = round((count / total) * 100, 1)
            # Top representative words
            word_counts = self.sense_word_counts[abbr][sense]
            top_words = [w for w, _ in word_counts.most_common(8)]
            examples = self.sense_examples[abbr][sense]
            senses_summary.append({
                "sense": sense,
                "count": count,
                "percentage": pct,
                "top_context_words": top_words,
                "examples": examples
            })

        return {
            "abbreviation": abbr,
            "total_occurrences": total,
            "unique_senses_count": len(senses),
            "senses": senses_summary
        }

    def disambiguate(self, abbr, text, focus_snippet=None, start=None, end=None, window_chars=250):
        """
        Context-aware disambiguation for an abbreviation given surrounding medical text.
        Uses TF-IDF weighted cosine / Bayesian evidence scoring.
        If start and end character positions are provided (or focus_snippet), evaluates
        the abbreviation using the specific occurrence's surrounding context rather
        than combining all contexts across the document.
        """
        if not self.is_loaded:
            self.load()
            
        abbr = abbr.upper()
        if abbr not in self.abbr_senses:
            return None

        senses_dict = self.abbr_senses[abbr]
        total_abbr_instances = sum(senses_dict.values())
        valid_senses = [s for s in senses_dict if s not in ["UNSURED SENSE", "NAME", "GENERAL ENGLISH"]]
        
        if not valid_senses:
            valid_senses = list(senses_dict.keys())

        # Determine evaluation context for this specific occurrence
        if focus_snippet:
            eval_text = focus_snippet.lower()
        elif start is not None and end is not None and text:
            # Extract local window around this specific occurrence
            left = max(0, start - window_chars)
            right = min(len(text), end + window_chars)
            boundaries = [m.start() for m in re.finditer(r"(?<!\d)[.!?;\n](?!\d)", text)]
            sent_left = max((p + 1 for p in boundaries if p < start), default=left)
            sent_right = min((p for p in boundaries if p >= end), default=right)
            eval_left = max(left, sent_left)
            eval_right = min(right, sent_right)
            eval_text = text[eval_left:eval_right].lower()
        else:
            eval_text = (text or "").lower()

        query_words = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", eval_text) if w not in self.stop_words and w != abbr.lower()]
        
        scores = {}
        evidence_by_sense = {}
        num_senses = len(valid_senses)

        for sense in valid_senses:
            # Baseline prior probability
            prior = (senses_dict[sense] + 1) / (total_abbr_instances + num_senses)
            
            # Context score
            sense_words = self.sense_word_counts[abbr][sense]
            tot_words = self.sense_total_words[abbr][sense] or 1
            
            match_score = 0.0
            matched_terms = []
            
            for w in query_words:
                if w in sense_words:
                    freq = sense_words[w]
                    # TF-IDF style weighting
                    tf = freq / tot_words
                    df = self.sense_doc_freq[abbr].get(w, 1)
                    idf = math.log((num_senses + 1) / (df + 0.5)) + 1.0
                    weight = tf * idf * 1000.0
                    match_score += weight
                    matched_terms.append((w, round(weight, 2)))

            # Combined score: weighted blend of prior + matched context evidence
            # Evidence has strong weight when matches are present
            if matched_terms:
                combined_score = (match_score * 0.85) + (prior * 15.0)
            else:
                combined_score = prior * 10.0

            scores[sense] = combined_score
            matched_terms.sort(key=lambda x: x[1], reverse=True)
            evidence_by_sense[sense] = [w for w, _ in matched_terms[:6]]

        # Softmax normalization for calibrated confidence
        max_score = max(scores.values()) if scores else 1.0
        scale = 1.0 if max_score < 50 else (50.0 / max_score)
        
        exp_vals = {s: math.exp(min(sc * scale, 30)) for s, sc in scores.items()}
        sum_exp = sum(exp_vals.values()) or 1.0
        probs = {s: exp_vals[s] / sum_exp for s in scores}
        
        sorted_senses = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        top_sense, top_prob = sorted_senses[0]

        alternatives = []
        for s, p in sorted_senses[1:5]:
            alternatives.append({
                "sense": s,
                "probability": round(p * 100, 1),
                "casi_count": senses_dict[s],
                "matched_context_keywords": evidence_by_sense.get(s, [])
            })

        return {
            "abbreviation": abbr,
            "predicted_sense": top_sense,
            "confidence": round(top_prob * 100, 1),
            "matched_context_keywords": evidence_by_sense.get(top_sense, []),
            "casi_total_references": senses_dict[top_sense],
            "casi_prior_frequency": round((senses_dict[top_sense] / total_abbr_instances) * 100, 1),
            "sample_casi_context": self.sense_examples[abbr][top_sense][0]["context"] if self.sense_examples[abbr][top_sense] else "",
            "sample_section": self.sense_examples[abbr][top_sense][0]["section"] if self.sense_examples[abbr][top_sense] else "GENERAL",
            "alternative_senses": alternatives,
            "data_source": "CASI Reference Dataset (Moon et al., 37,500 clinical note inventory)"
        }

    def disambiguate_occurrence(self, abbr, text, start, end, window_chars=250):
        """
        Disambiguate a specific occurrence of an abbreviation at character span (start, end)
        using its surrounding local clinical context in text.
        """
        return self.disambiguate(abbr, text, start=start, end=end, window_chars=window_chars)
