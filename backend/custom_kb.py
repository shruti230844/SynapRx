"""
Expanded Custom Medical Knowledge Base Engine.
Loads verified medical datasets:
- Disease abbreviations & multi-specialty meanings
- Prescription sig codes & food timing (AC, PC, CC, etc.)
- Medicine terminology & counseling pearls
- ISMP error-prone abbreviations and safety alerts
"""

import os
import json
import re

class CustomMedicalKB:
    def __init__(self, data_dir=None):
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data", "custom_dataset")
        self.data_dir = data_dir
        self.diseases = []
        self.clinical_abbreviations = {}
        self.multispecialty_abbrs = {}
        self.sig_frequencies = {}
        self.food_timings = {}
        self.routes = {}
        self.medicines = {}
        self.ismp_warnings = []
        self.is_loaded = False

    def load(self):
        if self.is_loaded:
            return True
        
        # 1. Disease Abbreviations
        d_path = os.path.join(self.data_dir, "disease_abbreviations.json")
        if os.path.exists(d_path):
            with open(d_path, "r", encoding="utf-8") as f:
                self.diseases = json.load(f)

        clinical_path = os.path.join(self.data_dir, "clinical_abbreviations.json")
        if os.path.exists(clinical_path):
            with open(clinical_path, "r", encoding="utf-8") as f:
                self.clinical_abbreviations = {
                    item["abbreviation"].upper(): item for item in json.load(f)
                }
        
        # 2. Multi-specialty Abbreviations
        m_path = os.path.join(self.data_dir, "abbreviation_senses_multispecialty.json")
        if os.path.exists(m_path):
            with open(m_path, "r", encoding="utf-8") as f:
                items = json.load(f)
                for item in items:
                    self.multispecialty_abbrs[item["abbreviation"].upper()] = item

        # 3. Prescription Sig Codes
        s_path = os.path.join(self.data_dir, "prescription_sig_codes.json")
        if os.path.exists(s_path):
            with open(s_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for freq in data.get("frequencies", []):
                    self.sig_frequencies[freq["code"].upper()] = freq
                for ft in data.get("food_timings", []):
                    self.food_timings[ft["code"].upper()] = ft
                for r in data.get("routes", []):
                    self.routes[r["code"].upper()] = r

        # 4. Medicine Terminology
        med_path = os.path.join(self.data_dir, "medicine_terminology.json")
        if os.path.exists(med_path):
            with open(med_path, "r", encoding="utf-8") as f:
                med_list = json.load(f)
                for med in med_list:
                    # Index by generic name and brand names
                    self.medicines[med["generic_name"].lower()] = med
                    for b in med.get("brand_names", []):
                        self.medicines[b.lower()] = med

        # 5. ISMP Error-Prone list
        ismp_path = os.path.join(self.data_dir, "ismp_error_prone_abbreviations.json")
        if os.path.exists(ismp_path):
            with open(ismp_path, "r", encoding="utf-8") as f:
                self.ismp_warnings = json.load(f)

        self.is_loaded = True
        return True

    def detect_specialty(self, text):
        """Detect the most likely clinical specialty from the context."""
        text_lower = text.lower()
        specialty_scores = {
            "Cardiology": 0,
            "Endocrinology / Diabetology": 0,
            "Pulmonology": 0,
            "Neurology": 0,
            "Gastroenterology": 0,
            "Nephrology": 0,
            "Rheumatology": 0,
            "Infectious Disease": 0,
            "General Medicine": 1 # baseline
        }
        
        keywords = {
            "Cardiology": ["heart", "cardio", "ecg", "echo", "cad", "htn", "stent", "angina", "mi", "valve", "bp", "hypertension", "atorvastatin", "amlodipine", "aspirin", "chf"],
            "Endocrinology / Diabetology": ["diabetes", "t2dm", "t1dm", "glucose", "insulin", "hba1c", "metformin", "thyroid", "levothyroxine", "sugar", "fasting", "ppbg"],
            "Pulmonology": ["lung", "cough", "sputum", "dyspnea", "asthma", "copd", "inhaler", "wheezing", "chest", "pe", "cxr", "salbutamol", "fev1", "pulmonary"],
            "Neurology": ["brain", "neuro", "stroke", "cva", "tia", "seizure", "mri", "ms", "multiple sclerosis", "neuropathy", "headache", "pregabalin", "tremor"],
            "Gastroenterology": ["gerd", "acid", "reflux", "ulcer", "stomach", "liver", "bowel", "diarrhea", "pantoprazole", "omeprazole", "endoscopy", "pud"],
            "Nephrology": ["kidney", "renal", "creatinine", "bun", "dialysis", "ckd", "gfr", "proteinuria", "edema"],
            "Rheumatology": ["joint", "arthritis", "ra", "lupus", "sle", "synovitis", "rf", "anti-ccp", "methotrexate", "morning stiffness"],
            "Infectious Disease": ["infection", "fever", "antibiotic", "culture", "augmentin", "amoxicillin", "uti", "bacterial", "viral"]
        }
        
        for spec, words in keywords.items():
            for w in words:
                matches = len(re.findall(r"\b" + re.escape(w) + r"\b", text_lower))
                specialty_scores[spec] += matches * 2

        sorted_specs = sorted(specialty_scores.items(), key=lambda x: x[1], reverse=True)
        top_spec, top_score = sorted_specs[0]
        secondary_spec, sec_score = sorted_specs[1]
        
        return {
            "primary": top_spec,
            "secondary": secondary_spec if sec_score > 2 else None,
            "confidence": "High" if top_score > 6 else ("Moderate" if top_score > 2 else "General")
        }

    def lookup_disease(self, term):
        """Lookup disease by abbreviation or name."""
        if not self.is_loaded:
            self.load()
        term_clean = term.strip().upper()
        for d in self.diseases:
            if d["abbreviation"].upper() == term_clean:
                return d
        # Only check full name if term is longer than 3 characters to prevent spurious 2-letter substring matches
        if len(term_clean) > 3:
            for d in self.diseases:
                if term_clean == d["full_name"].upper() or term_clean in d["full_name"].upper().split():
                    return d
        return None

    def lookup_clinical_abbreviation(self, term):
        """Return a structured clinical abbreviation reference, if present."""
        if not self.is_loaded:
            self.load()
        return self.clinical_abbreviations.get(term.strip().upper())

    def resolve_clinical_abbreviation(self, term, context_text, specialty_hint=None):
        """Score a clinical abbreviation's documented meanings against local context."""
        entry = self.lookup_clinical_abbreviation(term)
        if not entry:
            return None

        candidates = [{
            "sense": entry["full_form"],
            "category": entry["category"],
            "definition": entry["explanation"],
            "specialty": entry["specialty"],
            "context_keywords": entry.get("context_keywords", []),
            "source": entry.get("sources", []),
        }]
        candidates.extend({
            "sense": alternative["full_form"],
            "category": alternative["category"],
            "definition": alternative["explanation"],
            "specialty": alternative["specialty"],
            "context_keywords": alternative.get("context_keywords", []),
            "source": entry.get("sources", []),
        } for alternative in entry.get("alternative_meanings", []))

        context_lower = context_text.lower()
        for candidate in candidates:
            matched = []
            score = 0.0
            for keyword in candidate["context_keywords"]:
                pattern = r"(?<!\w)" + re.escape(keyword.lower()) + r"(?!\w)"
                if re.search(pattern, context_lower):
                    score += 1.0 + min(len(keyword.split()), 3) * 0.25
                    matched.append(keyword)
            if specialty_hint and specialty_hint.casefold() in candidate["specialty"].casefold():
                score += 0.5
            candidate["matched_keywords"] = matched
            candidate["score"] = score

        ranked = sorted(candidates, key=lambda item: item["score"], reverse=True)
        has_alternatives = len(ranked) > 1
        tied = has_alternatives and ranked[0]["score"] == ranked[1]["score"]
        no_context_evidence = ranked[0]["score"] == 0
        ambiguous = has_alternatives and (tied or no_context_evidence)
        selected = None if ambiguous else ranked[0]
        alternatives = [candidate for candidate in ranked if candidate is not selected and candidate["score"] > 0]
        if ambiguous:
            alternatives = ranked

        return {
            "abbreviation": entry["abbreviation"],
            "entry": entry,
            "selected": selected,
            "predicted_sense": selected["sense"] if selected else "Ambiguous abbreviation",
            "specialty": selected["specialty"] if selected else entry["specialty"],
            "definition": selected["definition"] if selected else "The context does not distinguish the documented meanings.",
            "category": selected["category"] if selected else entry["category"],
            "matched_keywords": selected["matched_keywords"] if selected else [],
            "ambiguous": ambiguous,
            "alternative_senses": [
                {
                    "sense": candidate["sense"],
                    "specialty": candidate["specialty"],
                    "definition": candidate["definition"],
                    "matched_keywords": candidate["matched_keywords"],
                }
                for candidate in alternatives
            ],
            "data_source": "; ".join(source["name"] + " — " + source["title"] for source in entry.get("sources", [])),
            "verification_status": entry.get("verification_status", "Unverified"),
        }

    def lookup_sig_frequency(self, code):
        """Lookup prescription frequency sig code."""
        if not self.is_loaded:
            self.load()
        code_clean = code.strip().upper()
        # Direct match or alias
        if code_clean in self.sig_frequencies:
            return self.sig_frequencies[code_clean]
        # Check standard mappings
        aliases = {"TDS": "TID", "QDS": "QID", "ON": "QHS", "OM": "OD"}
        if code_clean in aliases:
            return self.sig_frequencies.get(aliases[code_clean])
        return None

    def lookup_food_timing(self, code):
        """Lookup food timing abbreviation (AC, PC, CC, etc.)."""
        if not self.is_loaded:
            self.load()
        code_clean = code.strip().upper()
        return self.food_timings.get(code_clean)

    def lookup_route(self, code):
        """Lookup an administration route abbreviation."""
        if not self.is_loaded:
            self.load()
        aliases = {"SUBQ": "SC", "SUBCUTANEOUS": "SC", "ORAL": "PO", "INHALATION": "INH"}
        requested_codes = {
            aliases.get(re.sub(r"[^A-Z]", "", item.upper()), re.sub(r"[^A-Z]", "", item.upper()))
            for item in re.split(r"[/,]", code)
        }
        for route in self.routes.values():
            route_codes = {
                aliases.get(re.sub(r"[^A-Z]", "", item.upper()), re.sub(r"[^A-Z]", "", item.upper()))
                for item in re.split(r"[/,]", route.get("code", ""))
            }
            if requested_codes & route_codes:
                return route
        return None

    def lookup_medicine(self, drug_name):
        """Lookup medicine by generic or brand name."""
        if not self.is_loaded:
            self.load()
        name_clean = drug_name.strip().lower()
        # Try direct lookup
        if name_clean in self.medicines:
            return self.medicines[name_clean]
        # Try partial word match
        for key, med in self.medicines.items():
            if key in name_clean or name_clean in key:
                return med
        return None

    def check_ismp_warnings(self, text):
        """Scan text for known ISMP error-prone abbreviations and risky notation."""
        if not self.is_loaded:
            self.load()
        warnings_found = []
        text_lower = text.lower()
        
        # Check unit vs U
        if re.search(r"\b\d+\s*u\b", text_lower):
            warnings_found.append({
                "flagged_token": "U (for Unit)",
                "risk": "ISMP High Risk: 'U' can be mistaken for '0' (10-fold overdose) or '4'.",
                "recommendation": "Always write 'units' fully."
            })
        
        # Check trailing zero e.g. 5.0 mg
        trailing_zero = re.findall(r"\b(\d+\.0)\s*(?:mg|mcg|g|ml)\b", text_lower)
        if trailing_zero:
            warnings_found.append({
                "flagged_token": f"Trailing zero ({trailing_zero[0]})",
                "risk": "ISMP High Risk: Trailing zero (X.0) can lead to a 10-fold overdose if the decimal is missed.",
                "recommendation": "Never use trailing zeros (write '5 mg' instead of '5.0 mg')."
            })

        # Check lack of leading zero e.g. .5 mg
        lack_leading_zero = re.findall(r"(?:^|\s)(\.\d+)\s*(?:mg|mcg|g|ml)\b", text_lower)
        if lack_leading_zero:
            warnings_found.append({
                "flagged_token": f"Missing leading zero ({lack_leading_zero[0]})",
                "risk": "ISMP High Risk: Missing leading zero (.X) can be misread as a 10-fold overdose.",
                "recommendation": "Always write leading zero (e.g. '0.5 mg')."
            })

        # Check QD or QOD
        if re.search(r"\b(q\.?d\.?|q\.?o\.?d\.?)\b", text_lower):
            warnings_found.append({
                "flagged_token": "QD / QOD",
                "risk": "ISMP High Risk: QD and QOD are frequently misread for each other or for QID.",
                "recommendation": "Write 'daily' or 'every other day'."
            })

        # Check MS / MSO4 / MgSO4
        if re.search(r"\b(mso4|mgso4)\b", text_lower):
            warnings_found.append({
                "flagged_token": "MSO4 / MgSO4",
                "risk": "Critical ISMP Alert: Morphine sulfate and Magnesium sulfate confused with lethal consequences.",
                "recommendation": "Spell out 'morphine sulfate' or 'magnesium sulfate'."
            })

        return warnings_found

    def disambiguate_custom(self, abbr, context_text, specialty_hint=None):
        """Cross-reference multi-specialty sense inventory."""
        if not self.is_loaded:
            self.load()
        abbr_clean = abbr.strip().upper()
        if abbr_clean not in self.multispecialty_abbrs:
            return None
        
        entry = self.multispecialty_abbrs[abbr_clean]
        senses = entry.get("senses", [])
        
        ctx_lower = context_text.lower()
        scored_senses = []
        
        for s in senses:
            score = 0
            # Specialty match bonus
            if specialty_hint and specialty_hint.lower() in s.get("specialty", "").lower():
                score += 1
            # Keyword matches
            matched_kw = []
            for kw in s.get("context_keywords", []):
                pattern = r"(?<!\w)" + re.escape(kw.lower()) + r"(?!\w)"
                if re.search(pattern, ctx_lower):
                    score += 3 + min(len(kw.split()), 3) * 0.5
                    matched_kw.append(kw)
            scored_senses.append({
                "sense": s["sense"],
                "specialty": s["specialty"],
                "definition": s["definition"],
                "matched_keywords": matched_kw,
                "score": score,
                "typical_prescriptions": s.get("typical_prescriptions", []),
                "verified_source": s.get("verified_source", "")
            })
            
        scored_senses.sort(key=lambda x: x["score"], reverse=True)
        top = scored_senses[0]
        ambiguous = len(scored_senses) > 1 and (
            top["score"] == 0 or top["score"] == scored_senses[1]["score"]
        )
        
        return {
            "abbreviation": abbr_clean,
            "predicted_sense": top["sense"],
            "specialty": top["specialty"],
            "definition": top["definition"],
            "matched_keywords": top["matched_keywords"],
            "ambiguous": ambiguous,
            "ismp_warning": entry.get("ismp_warning"),
            "alternative_senses": [
                {
                    "sense": alt["sense"],
                    "specialty": alt["specialty"],
                    "definition": alt["definition"],
                    "matched_keywords": alt["matched_keywords"],
                }
                for alt in scored_senses[1:]
                if ambiguous or alt["score"] > 0
            ],
            "data_source": f"Custom Medical Knowledge Base ({top.get('verified_source', 'Clinical Reference')})"
        }
