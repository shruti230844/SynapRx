import re
from collections import defaultdict, Counter
import math

class CasiEngine:
    def __init__(self, casi_path=r"data/casi_reference/AnonymizedClinicalAbbreviationsAndAcronymsDataSet.txt"):
        self.casi_path = casi_path
        self.abbr_data = defaultdict(lambda: {
            "senses": defaultdict(int),
            "sense_words": defaultdict(Counter),
            "sense_sections": defaultdict(Counter),
            "sense_examples": defaultdict(list)
        })
        self.stop_words = set([
            "the", "and", "a", "an", "of", "to", "in", "is", "was", "for", "with", "on", "as", "at", "by", "this",
            "that", "from", "she", "he", "it", "her", "his", "patient", "pt", "there", "are", "were", "be", "has",
            "had", "have", "been", "or", "not", "no", "who", "which", "will", "would", "can", "could", "also",
            "name", "_%#name#%_", "_%#1999#%_", "_%#mm2006#%_", "_%#mmdd#%_", "_%#mm#%_", "_%#city#%_"
        ])
        self.is_loaded = False

    def load(self):
        if self.is_loaded:
            return
        with open(self.casi_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 7:
                    abbr = parts[0].strip().upper()
                    sense = parts[1].strip()
                    section = parts[5].strip().upper() if parts[5].strip() else "GENERAL"
                    context = parts[6].strip()
                    
                    self.abbr_data[abbr]["senses"][sense] += 1
                    self.abbr_data[abbr]["sense_sections"][sense][section] += 1
                    if len(self.abbr_data[abbr]["sense_examples"][sense]) < 3:
                        self.abbr_data[abbr]["sense_examples"][sense].append(context)
                    
                    # Tokenize context
                    words = re.findall(r"\b[a-zA-Z]{2,}\b", context.lower())
                    for w in words:
                        if w not in self.stop_words and w != abbr.lower():
                            self.abbr_data[abbr]["sense_words"][sense][w] += 1
        self.is_loaded = True
        print(f"CasiEngine loaded {len(self.abbr_data)} unique abbreviations.")

    def disambiguate(self, abbr, full_text, focus_sentence=None):
        if not self.is_loaded:
            self.load()
        abbr = abbr.upper()
        if abbr not in self.abbr_data:
            return None
        
        info = self.abbr_data[abbr]
        senses = info["senses"]
        total_instances = sum(senses.values())

        # Extract words from the input context
        context_text = (focus_sentence or full_text).lower()
        context_words = [w for w in re.findall(r"\b[a-zA-Z]{2,}\b", context_text) if w not in self.stop_words and w != abbr.lower()]
        
        scores = {}
        matched_evidence = {}

        for sense, sense_count in senses.items():
            if sense in ["UNSURED SENSE", "GENERAL ENGLISH", "NAME"]:
                continue
            # Prior probability
            prior = (sense_count + 1) / (total_instances + len(senses))
            log_prob = math.log(prior)
            
            words_freq = info["sense_words"][sense]
            total_words_in_sense = sum(words_freq.values()) + 1000
            
            evidence_words = []
            for w in context_words:
                c = words_freq.get(w, 0)
                if c > 0:
                    word_score = (c + 0.1) / total_words_in_sense
                    log_prob += math.log(word_score) * 1.5
                    evidence_words.append((w, c))
            
            scores[sense] = log_prob
            evidence_words.sort(key=lambda x: x[1], reverse=True)
            matched_evidence[sense] = [w for w, _ in evidence_words[:5]]

        if not scores:
            return None

        # Convert log scores to normalized softmax probabilities
        max_score = max(scores.values())
        exp_scores = {s: math.exp(v - max_score) for s, v in scores.items()}
        sum_exp = sum(exp_scores.values())
        probs = {s: v / sum_exp for s, v in exp_scores.items()}
        
        sorted_senses = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        top_sense, top_prob = sorted_senses[0]

        return {
            "abbreviation": abbr,
            "predicted_sense": top_sense,
            "confidence": round(top_prob * 100, 1),
            "matched_keywords": matched_evidence.get(top_sense, []),
            "alternative_senses": [
                {"sense": s, "probability": round(p * 100, 1), "sample_keywords": matched_evidence.get(s, [])}
                for s, p in sorted_senses[1:5] if p > 0.01
            ],
            "total_casi_references": senses[top_sense],
            "sample_casi_context": info["sense_examples"][top_sense][0] if info["sense_examples"][top_sense] else ""
        }

if __name__ == "__main__":
    engine = CasiEngine()
    engine.load()
    
    # Test 1: MS in cardiac context
    res1 = engine.disambiguate("MS", "Echocardiogram was performed for suspected mitral valve disease. Findings show moderate MS with thickened leaflets and elevated gradient.")
    print("Test 1 (Cardiac MS):", res1["predicted_sense"], f"({res1['confidence']}%)", "Keywords:", res1["matched_keywords"])

    # Test 2: MS in neurology context
    res2 = engine.disambiguate("MS", "Patient with relapsing-remitting MS presented with sensory numbness in bilateral lower extremities. MRI brain revealed new periventricular demyelinating lesions.")
    print("Test 2 (Neurology MS):", res2["predicted_sense"], f"({res2['confidence']}%)", "Keywords:", res2["matched_keywords"])

    # Test 3: MS in analgesic/pharmacology context
    res3 = engine.disambiguate("MS", "Postoperative analgesia protocol: MS 4 mg IV Q3H PRN severe breakthrough pain. Monitor respiratory rate.")
    print("Test 3 (Pharmacology MS):", res3["predicted_sense"], f"({res3['confidence']}%)", "Keywords:", res3["matched_keywords"])

    # Test 4: PE in emergency respiratory context
    res4 = engine.disambiguate("PE", "Patient presents with acute onset dyspnea and tachycardia. CTA of the chest ruled out acute PE.")
    print("Test 4 (Respiratory PE):", res4["predicted_sense"], f"({res4['confidence']}%)", "Keywords:", res4["matched_keywords"])

    # Test 5: PE in routine physical exam context
    res5 = engine.disambiguate("PE", "PE: Vitals stable. HEENT normal. Chest clear to auscultation. Abdomen soft, non-tender. Extremities without edema.")
    print("Test 5 (Exam PE):", res5["predicted_sense"], f"({res5['confidence']}%)", "Keywords:", res5["matched_keywords"])
