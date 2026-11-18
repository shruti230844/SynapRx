"""Prescription and clinical text parser backed by CASI and the custom medical KB."""

import re
from collections import Counter, defaultdict
from backend.casi_engine import CasiEngine
from backend.custom_kb import CustomMedicalKB

CLINICAL_TERMS = {
    "LDL": ("Low-density lipoprotein", "Investigation / Lipid Panel", "A cholesterol measurement used in lipid testing."),
    "OPD": ("Outpatient Department", "Follow-up / Care Setting", "Indicates outpatient clinic or follow-up care."),
    "BP": ("Blood Pressure", "Clinical Measurement", "A measurement of pressure in the arteries."),
    "HBA1C": ("Hemoglobin A1c", "Investigation / Diabetes Monitoring", "A blood test reflecting average blood glucose over roughly the prior 2 to 3 months."),
    "CBC": ("Complete Blood Count", "Investigation / Laboratory Test", "A blood test measuring red cells, white cells, and platelets."),
    "MRI": ("Magnetic Resonance Imaging", "Investigation / Imaging", "Imaging that uses magnetic fields and radio waves."),
    "CT": ("Computed Tomography", "Investigation / Imaging", "Cross-sectional X-ray imaging."),
    "CXR": ("Chest X-ray", "Investigation / Imaging", "Radiographic imaging of the chest."),
    "ECG": ("Electrocardiogram", "Investigation / Cardiology", "A recording of the heart's electrical activity."),
    "EKG": ("Electrocardiogram", "Investigation / Cardiology", "A recording of the heart's electrical activity."),
    "ECHO": ("Echocardiogram", "Investigation / Cardiology", "Ultrasound imaging of the heart."),
    "LFT": ("Liver Function Tests", "Investigation / Laboratory Test", "Blood tests that assess liver enzymes and related markers."),
    "RFT": ("Renal Function Tests", "Investigation / Laboratory Test", "Tests used to assess kidney function."),
    "TSH": ("Thyroid-Stimulating Hormone", "Investigation / Laboratory Test", "A blood test used to assess thyroid function."),
    "PNEUMONIA": ("Pneumonia", "Disease / Diagnosis", "An infection that inflames air sacs in one or both lungs."),
    "FU": ("Follow-up", "Follow-up / Care Plan", "A planned return visit or review."),
    "F/U": ("Follow-up", "Follow-up / Care Plan", "A planned return visit or review."),
    "SIG": ("Prescription Directions", "Prescription Instruction", "The directions describing how a medication should be administered."),
    "PTCA": ("Percutaneous Transluminal Coronary Angioplasty", "Cardiology / Procedure", "A procedure used to open a narrowed coronary artery, commonly using a balloon catheter."),
}

DOSAGE_UNITS = {
    "MG": ("Milligram", "Dosage Unit"),
    "MCG": ("Microgram", "Dosage Unit"),
    "G": ("Gram", "Dosage Unit"),
    "ML": ("Milliliter", "Dosage Unit"),
    "IU": ("International Unit", "Dosage Unit"),
}

NON_ABBREVIATION_WORDS = {
    "A", "AFTER", "AN", "AND", "AS", "AT", "BEFORE", "BEDTIME", "BREAKFAST", "BY", "CAP", "CAPSULE", "DATE", "MO",
    "CLINICAL", "DAILY", "DAYS", "DEPARTMENT", "DINNER", "DOCTOR", "DOSE", "DOSAGE", "EVERY", "FOOD",
    "FOR", "FROM", "FOLLOW", "GIVE", "HAVE", "HEART", "HOSPITAL", "IN", "LUNCH", "MALE", "MEAL", "MEALS",
    "MEDICATION", "MEDICATIONS", "MINS", "MOUTH", "NAME", "NORMAL", "NOTE", "NOTES", "OF", "ON", "ONCE", "OR", "ORAL",
    "OUTPATIENT", "PATIENT", "PRESCRIBED", "PRESCRIPTION", "REVIEW", "SENIOR", "SIG", "STRENGTH", "SUSP", "SYR", "SYRUP",
    "TAB", "TABLET", "TAKE", "THE", "THIS", "TIMES", "TO", "UNIT", "UP", "USE", "WITH", "YEAR", "YEARS",
    # Common hospital/clinic letterhead words and professional credentials.
    # OCR often reads these as uppercase tokens, but they are not clinical abbreviations.
    "METRO", "METABOLIC", "CARE", "CENTER", "CENTRE", "HOSPITAL", "CLINIC",
    "MEDICAL", "HEALTH", "HEALTHCARE", "INSTITUTE", "DIAGNOSTIC", "DIAGNOSTICS",
    "LAB", "LABORATORY", "DOCTORS", "DOCTOR", "DR", "PROF", "PROFESSOR",
    "MD", "MBBS", "DNB", "FACC", "FRCP", "MRCP", "FCPS",
    "CONSULTANT", "SPECIALIST", "CARDIOLOGIST", "PHYSICIAN", "SURGEON",
    "ADDRESS", "PHONE", "TEL", "EMAIL", "WWW", "COM", "REGISTRATION",
    "REPORT", "SUMMARY", "FINDINGS", "PRESENTED", "EVALUATION",
}

def format_sense(sense):
    """Format sense strings cleanly (e.g. American Society of Anesthesiologists, Multiple Sclerosis)."""
    if not sense:
        return ""
    if sense[0].isupper() and any(c.isupper() for c in sense[1:]):
        return sense
    words = sense.split()
    capitalized = []
    for i, w in enumerate(words):
        if i > 0 and w.lower() in {"of", "and", "in", "to", "for", "the", "a", "an"}:
            capitalized.append(w.lower())
        else:
            capitalized.append(w.capitalize())
    return " ".join(capitalized)

class PrescriptionInterpreter:
    def __init__(self, casi_engine=None, custom_kb=None):
        self.casi = casi_engine or CasiEngine()
        self.kb = custom_kb or CustomMedicalKB()
        self.casi.load()
        self.kb.load()

    def interpret(self, raw_text):
        """Full interpretation pipeline for prescription or clinical note text."""
        if not raw_text or not raw_text.strip():
            return {
                "success": False,
                "error": "Input text is empty. Please upload an image or enter medical text."
            }

        text = raw_text.strip()
        
        # 1. Detect Clinical Specialty (label for the whole note only;
        #    individual abbreviations are resolved from their own local context)
        specialty_info = self.kb.detect_specialty(text)

        # 2. Extract & Disambiguate Abbreviations
        abbreviations_analysis = self._extract_and_disambiguate_abbreviations(text, specialty_info)

        # 3. Parse Medications & Food Timing
        medications_list = self._parse_medications(text)

        # 4. Generate Daily Medication Schedule & Timeline
        daily_schedule = self._generate_daily_schedule(medications_list)

        # 5. Extract Conditions / Diagnoses
        diagnoses = self._extract_diagnoses(text)

        # 6. Safety & ISMP Alerts
        safety_alerts = self.kb.check_ismp_warnings(text)

        # 7. Generate Plain-English Patient Summary
        patient_summary = self._generate_patient_summary(
            medications_list, diagnoses, daily_schedule, abbreviations_analysis
        )

        return {
            "success": True,
            "specialty": specialty_info,
            "diagnoses": diagnoses,
            "abbreviations": abbreviations_analysis,
            "medications": medications_list,
            "daily_schedule": daily_schedule,
            "safety_alerts": safety_alerts,
            "patient_summary": patient_summary,
            "disclaimer": (
                "IMPORTANT MEDICAL DISCLAIMER: This application is an assistive tool for deciphering medical shorthand, "
                "prescription Latin abbreviations, and clinical terminology. It does NOT diagnose medical conditions, and "
                "does NOT independently prescribe, modify, or recommend drug dosages. Always consult your prescribing physician "
                "or licensed pharmacist before making any changes to your medication regimen."
            )
        }

    @staticmethod
    def _has_explicit_negation(token, context):
        token_pattern = re.escape(token)
        before_pattern = rf"\b(?:no\s+evidence\s+of|no\s+signs?\s+of|negative\s+for|ruled\s+out|excluded|no|not|denies|denied|without|absent)\b(?:\W+(?!and\b|but\b)\w+){{0,2}}\W+{token_pattern}\b"
        after_pattern = rf"\b{token_pattern}\b(?:\W+\w+){{0,2}}\W+(?:ruled\s+out|not\s+present|absent|negative)\b"
        return bool(re.search(before_pattern, context, re.I) or re.search(after_pattern, context, re.I))

    @staticmethod
    def _sentence_context(text, start, end=None):
        """Return the sentence containing a token, excluding decimal points and dotted abbreviations."""
        end = end if end is not None else start + 1
        boundary_pattern = r"(?:(?<!\d)[!?;\n]|(?<!\d)(?<!\.[a-z])\.(?=\s+[A-Z0-9]|\s*$|\n))"
        boundaries = [match.start() for match in re.finditer(boundary_pattern, text)]
        left = max((position + 1 for position in boundaries if position < start), default=0)
        right = min((position for position in boundaries if position >= end), default=len(text))
        sentence = text[left:right].strip()

        local_start = start - left
        local_end = end - left
        clause_pattern = r",|:|;|\b(?:but|however|although|whereas)\b"
        clause_left = max((match.end() for match in re.finditer(clause_pattern, sentence[:local_start], re.I)), default=0)
        clause_right = min((match.start() + local_end for match in re.finditer(clause_pattern, sentence[local_end:], re.I)), default=len(sentence))
        clause = sentence[clause_left:clause_right].strip()
        return sentence, clause

    @staticmethod
    def _context_window(text, start, end, words=25):
        """Return up to `words` words on each side of the token, limited to its
        own sentence and cut at contrast words (but/however/...).

        This window is used ONLY to decide what an abbreviation means. It never
        includes text from other sentences, so the rest of the document cannot
        influence the meaning of a single abbreviation. Unlike the clause, it is
        not cut at commas, so 'Tab Metformin 500 mg, OD' keeps its dose cue.
        """
        boundary_pattern = r"(?:(?<!\d)[!?;\n]|(?<!\d)(?<!\.[a-z])\.(?=\s+[A-Z0-9]|\s*$|\n))"
        boundaries = [m.start() for m in re.finditer(boundary_pattern, text)]
        left = max((p + 1 for p in boundaries if p < start), default=0)
        right = min((p for p in boundaries if p >= end), default=len(text))

        before, after = text[left:start], text[end:right]
        contrast = r"\b(?:but|however|although|whereas)\b"
        breaks = list(re.finditer(contrast, before, re.I))
        if breaks:
            before = before[breaks[-1].end():]
        m = re.search(contrast, after, re.I)
        if m:
            after = after[:m.start()]

        return " ".join(before.split()[-words:] + [text[start:end]] + after.split()[:words])

    @classmethod
    def _clinical_status(cls, token, context, sentence_context=None):
        """Classify one occurrence without borrowing a neighbouring finding."""
        sentence = (sentence_context or context or "").strip()
        clause = (context or sentence).strip()
        token_pattern = re.escape(token)

        # Prescription codes and units are instructions/metadata, not diagnoses.
        if token in DOSAGE_UNITS:
            return "Dosage Unit"
        if token in {"PO", "IV", "IM", "SC", "SL", "TOP"}:
            return "Administration Instruction"
        if token in {"OD", "BD", "BID", "TID", "QID", "QHS", "HS", "SOS", "PRN", "STAT"}:
            return "Prescription Frequency / As Needed"
        if token in {"AC", "PC"}:
            return "Food-Timing Instruction"

        # A medication-form CAP is capsule, not community-acquired pneumonia.
        if token == "CAP" and re.search(r"\bcap\.?\s+[A-Za-z][A-Za-z-]*", sentence, re.I):
            return "Dosage Form"

        # A final explicit outcome overrides an earlier suspicion.
        ruled_out_patterns = (
            rf"\b{token_pattern}\b(?:\W+\w+){{0,10}}\W+(?:was\s+)?(?:later\s+)?(?:ruled\s+out|excluded|not\s+evident)",
            rf"\b(?:no\s+evidence\s+of|no\s+signs?\s+of|ruled\s+out|excluded|negative\s+for)\b(?:\W+\w+){{0,3}}\W+{token_pattern}\b",
        )
        if any(re.search(pattern, sentence, re.I) for pattern in ruled_out_patterns):
            return "Ruled Out / Not Evident"
        if cls._has_explicit_negation(token, clause):
            return "Negative / Denied"

        # Keep monitoring instructions attached to the relevant occurrence.
        if re.search(
            rf"\b(?:monitor(?:ing)?|track|recheck|repeat|follow|check)\b(?:\W+\w+){{0,3}}\W+{token_pattern}\b|"
            rf"\b{token_pattern}\b(?:\W+\w+){{0,3}}\W+(?:monitor(?:ed|ing)?|track(?:ed|ing)?|recheck(?:ed)?|repeat(?:ed)?)\b",
            clause, re.I
        ):
            return "Monitoring Instruction"

        token_match = re.search(rf"\b{token_pattern}\b", sentence, re.I)
        if token_match:
            prefix = sentence[:token_match.start()]
            if re.search(r"\b(?:history\s+of|hx\s+of|past\s+medical\s+history|pmh)\b", prefix, re.I):
                if not re.search(r"\b(?:but|however|although|whereas)\b", prefix, re.I):
                    return "Past History"
            if re.match(r"\s*(?:history|hx|pmh|past\s+medical\s+history)\s*:", sentence, re.I):
                return "Past History"

        if re.search(rf"\b(?:possible|suspected|probable|likely|may\s+represent|cannot\s+exclude)\b(?:\W+\w+){{0,3}}\W+{token_pattern}\b", clause, re.I):
            return "Suspected / Uncertain"
        if re.search(rf"\b(?:mild|moderate|severe)\b(?:\W+\w+){{0,2}}\W+{token_pattern}\b", clause, re.I):
            return "Positive / Confirmed Finding"
        if re.search(
            rf"\b{token_pattern}\b(?:\W+\w+){{0,5}}\W*(?:elevated|high|increased|raised)\b|"
            rf"\b(?:elevated|high|increased|raised)\b(?:\W+\w+){{0,5}}\W+{token_pattern}\b",
            clause, re.I
        ):
            return "Positive Finding / Elevated"

        # Prevent a neighbouring result (e.g. normal EF) from changing LVH status.
        normal_match = re.search(r"\b(?:within\s+normal\s+limits|normal|unremarkable)\b", clause, re.I)
        if normal_match:
            before_normal = clause[:normal_match.start()]
            after_normal = clause[normal_match.end():]
            token_is_subject = bool(re.search(rf"\b{token_pattern}\b", before_normal, re.I))
            another_measurement_follows = bool(re.match(r"\s*(?:for\s+)?(?:EF|LVEF|BP|RBS|LDL|HBA1C|CBC)\b", after_normal, re.I))
            if token_is_subject and not (re.search(r"\bwith\s*$", before_normal, re.I) and another_measurement_follows):
                return "Normal Finding"
            if re.search(rf"\b{token_pattern}\b", after_normal, re.I):
                return "Normal Finding"

        if re.search(rf"\b{token_pattern}\b(?:\W+\w+){{0,5}}\W+reviewed\b|\breviewed\b(?:\W+\w+){{0,5}}\W+{token_pattern}\b", clause, re.I):
            return "Reviewed / Mentioned"
        if re.search(rf"\b(?:reports?|reported|has|shows?|demonstrates?|noted|diagnosed|confirmed|present)\b(?:\W+\w+){{0,4}}\W+{token_pattern}\b|\b{token_pattern}\b(?:\W+\w+){{0,3}}\W*(?:present|confirmed|noted)\b", clause, re.I):
            return "Positive / Confirmed Finding"
        return "Mentioned / Uncertain"

    @staticmethod
    def _contextual_status_cues(context):
        cues = [
            "no evidence of", "no signs of", "negative for", "ruled out", "not evident",
            "denies", "denied", "without", "possible", "suspected", "probable", "likely",
            "history of", "hx of", "elevated", "high", "increased", "raised", "normal",
            "unremarkable", "confirmed", "diagnosed", "shows", "demonstrates", "noted",
            "monitor", "monitoring", "track", "recheck", "repeat", "reviewed",
        ]
        return [cue for cue in cues if re.search(r"(?<!\w)" + re.escape(cue) + r"(?!\w)", context, re.I)]

    def _extract_and_disambiguate_abbreviations(self, text, specialty_info):
        """Identify known and unsupported abbreviation-like tokens in the note."""
        known_tokens = set(CLINICAL_TERMS) | set(DOSAGE_UNITS)
        known_tokens.update(self.casi.abbr_senses)
        known_tokens.update(self.kb.clinical_abbreviations)
        known_tokens.update(self.kb.multispecialty_abbrs)
        known_tokens.update(self.kb.sig_frequencies)
        known_tokens.update(self.kb.food_timings)
        known_tokens.update(d["abbreviation"].upper() for d in self.kb.diseases)
        for route in self.kb.routes.values():
            route_codes = [re.sub(r"[^A-Z]", "", item.upper()) for item in route["code"].split("/")]
            known_tokens.update(route_codes)
            if len(route_codes) > 1:
                known_tokens.add("/".join(route_codes))

        occurrences = {}
        # Preserve slash-form abbreviations only when the complete form is
        # present in the reference data (for example F/U). Otherwise split
        # combinations such as SOS/PRN into their individual abbreviations.
        known_slash_tokens = sorted(
            (token for token in known_tokens if "/" in token),
            key=len,
            reverse=True,
        )
        slash_alternation = "|".join(re.escape(token) for token in known_slash_tokens)
        token_pattern = (
            r"(?<![A-Za-z0-9])(?:"
            + (slash_alternation + r"|" if slash_alternation else "")
            + r"[A-Za-z][A-Za-z0-9]*)(?![A-Za-z0-9])"
        )
        # Learn explicit long-form definitions once, then apply them to later
        # occurrences of the same abbreviation throughout this document.
        # This is deterministic document-level context, not a frequency guess.
        document_expansions = {}
        expansion_patterns = {
            "MS": [
                (r"\bMS\s*\(\s*material\s+synopsis\s*\)|\bmaterial\s+synopsis\s*\(\s*MS\s*\)",
                 ("Material Synopsis", "A concise structured summary of the relevant records or material.", "Document / Records Term")),
                (r"\bMS\s*\(\s*multiple\s+sclerosis\s*\)|\bmultiple\s+sclerosis\s*\(\s*MS\s*\)",
                 ("Multiple Sclerosis", "A neurological condition affecting the central nervous system.", "Neurology / Disease")),
            ],
            "IT": [
                (r"\bIT\s*\(\s*information\s+technology\s*\)|\binformation\s+technology\s*\(\s*IT\s*\)",
                 ("Information Technology", "The department or field responsible for computing and information systems.", "Department / General Term")),
            ],
        }
        for abbreviation, definitions in expansion_patterns.items():
            for pattern, definition in definitions:
                if re.search(pattern, text, re.I):
                    document_expansions[abbreviation] = definition
                    break

        for match in re.finditer(token_pattern, text, re.I):
            raw_token = match.group(0)
            token = raw_token.upper()
            normalized = re.sub(r"[^A-Z0-9/]", "", token)

            # Do not mistake the ordinary pronoun “it” (including sentence-start
            # “It”) for the abbreviation IT merely because CASI contains IT.
            # Keep uppercase IT only when explicitly defined or used in a clear
            # department/technology context.
            if token == "IT" and raw_token != "IT":
                continue
            if token == "IT" and token not in document_expansions and not re.search(
                r"\b(?:information\s+technology|IT\s+department|IT\s+services|IT\s+system)\b",
                text[max(0, match.start()-80):min(len(text), match.end()+80)], re.I
            ):
                continue
            # Keep reference-backed terms regardless of length. For unknown OCR tokens,
            # only consider plausible short uppercase abbreviations; discard ordinary
            # letterhead words, credentials and single-character noise.
            is_reference_term = normalized in known_tokens
            is_plausible_unknown = (
                raw_token.isupper()
                and 2 <= len(normalized) <= 6
                and normalized not in NON_ABBREVIATION_WORDS
                and bool(re.search(r"[A-Z]", normalized))
            )
            is_numeric_code = any(char.isdigit() for char in raw_token) and len(normalized) <= 10
            if is_reference_term or is_plausible_unknown or is_numeric_code:
                occurrences.setdefault((normalized, match.start()), []).append(match)

        results = []
        token_occurrence_counts = Counter(tok for (tok, _pos) in occurrences.keys())
        token_occurrence_indices = defaultdict(int)

        for (token, _position), matches in occurrences.items():
            m0 = matches[0]
            start_pos = m0.start()
            end_pos = m0.end()
            token_occurrence_indices[token] += 1
            occ_idx = token_occurrence_indices[token]
            tot_occ = token_occurrence_counts[token]

            sentence_context, local_context = self._sentence_context(text, start_pos, end_pos)
            # Window used to decide MEANING for this specific occurrence
            sense_context = self._context_window(text, start_pos, end_pos, words=25)

            route = self.kb.lookup_route(token)
            frequency = self.kb.lookup_sig_frequency(token)
            food_timing = self.kb.lookup_food_timing(token)
            disease_entry = self.kb.lookup_disease(token)

            local_specialty = self.kb.detect_specialty(sense_context)["primary"]
            clinical_resolution = self.kb.resolve_clinical_abbreviation(
                token, sense_context, local_specialty
            )
            clinical_term = CLINICAL_TERMS.get(token)
            dosage_unit = DOSAGE_UNITS.get(token)
            custom_sense = self.kb.disambiguate_custom(token, sense_context, local_specialty)

            # Evaluate each occurrence using its own surrounding context
            is_casi_token = token in self.casi.abbr_senses
            casi_result = (
                self.casi.disambiguate(token, text, focus_snippet=sense_context, start=start_pos, end=end_pos)
                if is_casi_token else None
            )
            custom_ambiguous = bool(custom_sense and custom_sense.get("ambiguous"))
            casi_context_supported = bool(
                casi_result
                and (casi_result.get("confidence", 0) >= 70 or casi_result.get("matched_context_keywords"))
            )

            # Status stays clause-level so a neighbouring finding isn't borrowed.
            clinical_status = self._clinical_status(token, local_context, sentence_context)
            negated = clinical_status in {"Negative / Denied", "Ruled Out / Not Evident"}

            medication_cue = bool(
                re.search(r"\b(?:\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu)|tab(?:let)?|cap(?:sule)?|po|iv|im)\b", sense_context, re.I)
                or self._find_medicine_mentions(sense_context)
            )
            explicit_meal_phrase = re.search(
                r"\b(?:before|after|with)\s+(?:the\s+)?(?:breakfast|lunch|dinner|food|meal|meals)\b",
                sense_context, re.I
            )
            ophthalmology_cue = bool(re.search(
                r"\b(?:right\s+eye|ophthalm\w*|ocular|eye\s+(?:exam|examination|drop))\b",
                sense_context, re.I
            ))
            forced_alternatives = None

            if dosage_unit:
                meaning, category = dosage_unit
                definition = f"A unit used to express a medication dose ({meaning.lower()})."
                source, confidence = "Dosage Unit Reference", 98.0
                forced_alternatives = []
            elif token == "CAP" and re.search(r"\bcap\.?\s+[A-Za-z][A-Za-z-]*", sentence_context, re.I):
                meaning, definition, category = "Capsule", "A capsule dosage form used for medication administration.", "Dosage Form"
                source, confidence = "Prescription Terminology Reference", 98.0
                forced_alternatives = []
            elif token == "OD" and ophthalmology_cue:
                meaning, definition, category = "Right Eye (Oculus Dexter)", "The right eye; an ophthalmic notation.", "Ophthalmology"
                source, confidence = "Clinical Terminology Reference", 98.0
                forced_alternatives = []
            elif token == "OD" and not medication_cue:
                meaning = "Ambiguous abbreviation"
                definition = "OD may mean once daily or right eye. Add prescription or ophthalmology context to disambiguate."
                category, source, confidence = "Needs Clarification", "Prescription and Ophthalmology References", 0.0
                forced_alternatives = [
                    {"sense": "Once daily", "specialty": "Prescription Shorthand", "definition": "A medication frequency."},
                    {"sense": "Right Eye (Oculus Dexter)", "specialty": "Ophthalmology", "definition": "The right eye."},
                ]
            elif token == "OD" and frequency:
                meaning, definition, category = frequency["english"], frequency["timing_details"], "Prescription Frequency"
                source, confidence = "Custom Sig Code Reference", 99.0
                forced_alternatives = []
            elif is_casi_token and casi_context_supported:
                raw_sense = casi_result["predicted_sense"]
                meaning = format_sense(raw_sense)
                confidence = casi_result["confidence"]
                source = casi_result["data_source"]
                raw_lower = raw_sense.lower()
                if raw_lower == "multiple sclerosis":
                    category = "Neurology / Disease"
                    definition = "A neurological condition affecting the central nervous system."
                elif raw_lower == "morphine sulfate":
                    category = "Pharmacology / Analgesic"
                    definition = "A potent opioid analgesic medication used to treat severe pain."
                elif raw_lower == "mitral stenosis":
                    category = "Cardiology / Valvular Disease"
                    definition = "A narrowing of the heart's mitral valve opening that restricts blood flow."
                elif raw_lower == "intramuscular":
                    category = "Administration Route"
                    definition = "Administration route: Injected into muscle tissue (intramuscular)."
                elif raw_lower == "intramedullary":
                    category = "Orthopedics / Surgical"
                    definition = "Located within or introduced into the medullary cavity of a bone (e.g., an intramedullary nail)."
                elif raw_lower == "acetylsalicylic acid":
                    category = "Pharmacology / Antiplatelet"
                    definition = "Aspirin (acetylsalicylic acid), an analgesic, antipyretic, and antiplatelet medication."
                elif "anesthesiologist" in raw_lower:
                    category = "Anesthesiology / Risk Assessment"
                    definition = "American Society of Anesthesiologists (ASA physical status classification score)."
                elif raw_lower == "pulmonary embolism":
                    category = "Pulmonology / Disease"
                    definition = "A blockage in one of the pulmonary arteries in the lungs."
                elif raw_lower == "physical examination":
                    category = "Clinical Assessment"
                    definition = "A physical examination performed by a clinician."
                elif raw_lower == "rheumatoid arthritis":
                    category = "Rheumatology / Disease"
                    definition = "A chronic inflammatory disorder affecting joints and connective tissue."
                elif raw_lower == "right atrium":
                    category = "Cardiology / Anatomy"
                    definition = "The right upper chamber of the heart that receives deoxygenated blood."
                elif raw_lower == "physical therapy":
                    category = "Rehabilitation / Care Plan"
                    definition = "Physical therapy and rehabilitation exercises."
                elif raw_lower == "prothrombin time":
                    category = "Investigation / Laboratory Test"
                    definition = "A blood test measuring how long it takes for blood to clot."
                else:
                    category = "Clinical Abbreviation"
                    definition = f"Selected from matching clinical contexts in the CASI reference corpus: {', '.join(casi_result.get('matched_context_keywords', [])[:4])}."
                forced_alternatives = casi_result.get("alternative_senses", [])
            elif route:
                meaning, definition, category = (route.get("latin") or route["english"]), f"Administration route: {route['english']}.", "Administration Route"
                source, confidence = "Custom Sig Code Reference", 99.0
                forced_alternatives = []
            elif frequency:
                meaning, definition, category = frequency["english"], frequency["timing_details"], "Prescription Frequency"
                source, confidence = "Custom Sig Code Reference", 99.0
                forced_alternatives = []
            elif food_timing and (medication_cue or explicit_meal_phrase):
                meaning, definition, category = food_timing["english"], food_timing["instruction"], "Food Timing"
                source, confidence = "Custom Sig Code Reference", 99.0
                forced_alternatives = []
            elif disease_entry:
                meaning, definition, category = disease_entry["full_name"], disease_entry["plain_english"], "Disease / Diagnosis"
                source, confidence = f"Custom Medical KB ({disease_entry['verified_source']})", 98.0
            elif token in document_expansions and not (is_casi_token and casi_context_supported):
                meaning, definition, category = document_expansions[token]
                source, confidence = "Explicit Document Definition", 99.0
                forced_alternatives = []
            elif clinical_resolution:
                if clinical_resolution["ambiguous"]:
                    meaning = "Ambiguous abbreviation"
                    definition = "The context does not distinguish the documented meanings. Review the alternatives or clarify the source."
                    category, source, confidence = "Needs Clarification", "Clinical Terminology Reference", 0.0
                else:
                    meaning = clinical_resolution["predicted_sense"]
                    definition = clinical_resolution["definition"]
                    category = clinical_resolution["category"]
                    source, confidence = clinical_resolution["data_source"], 98.0
                forced_alternatives = clinical_resolution["alternative_senses"]
            elif custom_ambiguous and not casi_context_supported:
                meaning = "Ambiguous abbreviation"
                definition = "Available meanings have equal or insufficient contextual evidence; clarify the intended meaning."
                category, source, confidence = "Needs Clarification", custom_sense["data_source"], 0.0
                forced_alternatives = custom_sense["alternative_senses"]
            elif clinical_term:
                meaning, category, definition = clinical_term
                source, confidence = "Clinical Terminology Reference", 98.0
            elif custom_sense and custom_sense.get("matched_keywords"):
                meaning, definition, category = custom_sense["predicted_sense"], custom_sense["definition"], "Clinical Abbreviation"
                source, confidence = custom_sense["data_source"], 92.0
            elif casi_result:
                meaning = format_sense(casi_result["predicted_sense"])
                definition = "Selected from matching clinical contexts in the CASI reference corpus."
                category = "Clinical Abbreviation"
                source, confidence = casi_result["data_source"], casi_result["confidence"]
                forced_alternatives = casi_result.get("alternative_senses", [])
            elif custom_sense:
                meaning, definition, category = custom_sense["predicted_sense"], custom_sense["definition"], "Clinical Abbreviation"
                source, confidence = custom_sense["data_source"], 70.0
            else:
                meaning = "Unrecognized abbreviation"
                definition = "This abbreviation is not supported by the local references. Confirm its intended meaning with the prescriber or pharmacist."
                category, source, confidence = "Needs Clarification", "No reference match", 0.0

            # Non-clinical terminology must never inherit a clinical finding
            # status such as Positive, Ruled Out, or Mixed Clinical Status.
            # The status is attached per occurrence before deduplication.
            non_clinical_categories = {
                "Document / Records Term", "Department / General Term",
                "Medical Qualification", "Dosage Form", "Dosage Unit",
                "Administration Route", "Prescription Frequency",
                "Food Timing", "Prescription Instruction", "Administration Instruction",
                "Food-Timing Instruction", "Ophthalmology",
            }
            if category in non_clinical_categories:
                clinical_status = "Not Applicable"
                negated = False

            casi_prediction = casi_result.get("predicted_sense") if casi_result else None
            custom_prediction = custom_sense.get("predicted_sense") if custom_sense else None
            model_disagreement = bool(casi_prediction and custom_prediction and casi_prediction.casefold() != custom_prediction.casefold())
            model_status = "reference_disagreement" if model_disagreement else ("reference_agreement" if casi_prediction and custom_prediction else "single_reference" if casi_prediction or custom_prediction else "no_reference_prediction")

            alternatives = []
            alternative_sources = []
            if forced_alternatives is not None:
                alternative_sources.extend(forced_alternatives)
            else:
                if custom_sense:
                    alternative_sources.extend(custom_sense.get("alternative_senses", []))
                if casi_result and (casi_result.get("confidence", 0) < 80 or not casi_result.get("matched_context_keywords")):
                    alternative_sources.extend(casi_result.get("alternative_senses", []))
            seen_senses = {meaning.casefold()}
            for alternative in alternative_sources:
                sense = alternative.get("sense", "")
                if sense and sense.casefold() not in seen_senses:
                    alternatives.append(alternative)
                    seen_senses.add(sense.casefold())

            candidate_meanings = [meaning]
            for alt in alternatives:
                s = alt.get("sense") if isinstance(alt, dict) else str(alt)
                if s and s.casefold() not in {m.casefold() for m in candidate_meanings}:
                    candidate_meanings.append(format_sense(s))

            matched_keywords = clinical_resolution.get("matched_keywords", []) if clinical_resolution and not clinical_resolution["ambiguous"] else []
            if not matched_keywords:
                matched_keywords = custom_sense.get("matched_keywords", []) if custom_sense else []
            if not matched_keywords and casi_result:
                matched_keywords = casi_result.get("matched_context_keywords", [])
            matched_keywords = list(dict.fromkeys(matched_keywords + self._contextual_status_cues(sense_context)))
            if clinical_status == "Past History" and re.match(r"\s*(?:history|hx|pmh|past\s+medical\s+history)\s*:", sentence_context, re.I):
                matched_keywords.append("history heading")

            if matched_keywords:
                why_selected = f"Selected from nearby clinical cues: {', '.join(matched_keywords[:4])}."
            elif route:
                why_selected = f"{token} occurs as an administration route; the route reference defines it as {meaning.lower()}."
            elif frequency:
                why_selected = f"{token} occurs as a prescription frequency code; the sig reference defines it as {meaning.lower()}."
            elif food_timing and (medication_cue or explicit_meal_phrase):
                phrase = explicit_meal_phrase.group(0) if explicit_meal_phrase else token
                why_selected = f"The food-timing code {token} is supported by the nearby instruction '{phrase}'."
            elif clinical_resolution and clinical_resolution["ambiguous"]:
                why_selected = "Available meanings have no distinguishing local context; clarification is required."
            elif clinical_term or dosage_unit or disease_entry:
                why_selected = f"Matched the standardized {category.lower()} reference entry; no unrelated context was used."
            elif alternatives:
                why_selected = f"The context did not strongly separate the available senses; {source} supplied the leading candidate."
            else:
                why_selected = "No supported reference or contextual model recognized this token; clarification is required."

            results.append({
                "token": token,
                "occurrence_index": occ_idx,
                "total_occurrences": tot_occ,
                "start": start_pos,
                "end": end_pos,
                "position": [start_pos, end_pos],
                "occurrences": 1,
                "context_snippet": sentence_context,
                "category": category,
                "meaning": meaning,
                "plain_english": definition,
                "confidence": confidence,
                "source": source,
                "specialty": (
                    clinical_resolution.get("specialty") if clinical_resolution
                    else custom_sense.get("specialty") if custom_sense
                    else disease_entry.get("specialty") if disease_entry
                    else None
                ),
                "verification_status": clinical_resolution.get("verification_status") if clinical_resolution else None,
                "references": clinical_resolution["entry"].get("sources", []) if clinical_resolution else [],
                "matched_keywords": matched_keywords[:6],
                "why_selected": why_selected,
                "candidate_meanings": candidate_meanings,
                "alternative_senses": alternatives[:5],
                "clarification_required": meaning in {"Unrecognized abbreviation", "Ambiguous abbreviation"},
                "negated": negated,
                "clinical_status": clinical_status,
                "occurrence_details": [{
                    "occurrence_index": occ_idx,
                    "position": [start_pos, end_pos],
                    "meaning": meaning,
                    "clinical_status": clinical_status,
                    "context_snippet": sentence_context,
                    "matched_keywords": matched_keywords[:6],
                    "why_selected": why_selected,
                }],
                "model_comparison": {
                    "casi": {"prediction": casi_prediction, "confidence": casi_result.get("confidence") if casi_result else None},
                    "custom_kb": {"prediction": custom_prediction, "matched_keywords": custom_sense.get("matched_keywords", []) if custom_sense else []},
                    "status": model_status,
                    "disagreement": model_disagreement,
                },
                "safety_note": disease_entry.get("safety_considerations") if disease_entry else (frequency.get("ismp_status") if frequency else None),
            })

        return self._deduplicate_abbreviations(results)

    @staticmethod
    def _deduplicate_abbreviations(results):
        """Consolidate occurrences by (token, meaning) so that occurrences with
        different contextual meanings (e.g. MS as Multiple Sclerosis vs Morphine Sulfate)
        are preserved as separate, occurrence-level entries.
        Only identical occurrences with the same meaning are merged.
        """
        grouped = {}
        for result in results:
            key = (result["token"], result["meaning"])
            if key not in grouped:
                grouped[key] = dict(result)
                continue

            current = grouped[key]
            current["occurrences"] += result["occurrences"]
            current["occurrence_details"].extend(result["occurrence_details"])
            if "positions" not in current:
                current["positions"] = [current.get("position", [current.get("start"), current.get("end")])]
            current["positions"].append(result.get("position", [result.get("start"), result.get("end")]))
            statuses = list(dict.fromkeys(detail["clinical_status"] for detail in current["occurrence_details"]))
            current["clinical_status"] = statuses[0] if len(statuses) == 1 else "Mixed Clinical Status"
            current["negated"] = all(detail["clinical_status"] in {"Negative / Denied", "Ruled Out / Not Evident"} for detail in current["occurrence_details"])
            current["matched_keywords"] = list(dict.fromkeys(
                keyword for detail in current["occurrence_details"] for keyword in detail["matched_keywords"]
            ))[:6]

        return list(grouped.values())

    def _find_medicine_mentions(self, text):
        catalog = {}
        for medicine in self.kb.medicines.values():
            generic_name = medicine.get("generic_name", "")
            if not generic_name or generic_name in catalog:
                continue
            aliases = [re.sub(r"\([^)]*\)", "", generic_name).strip()]
            aliases.extend(re.findall(r"\(([^)]*)\)", generic_name))
            aliases.extend(medicine.get("brand_names", []))
            aliases.extend(part.strip() for part in re.split(r"\s+and\s+", aliases[0], flags=re.I) if part.strip())
            catalog[generic_name] = (medicine, {alias.strip() for alias in aliases if alias.strip()})

        matches = []
        for generic_name, (medicine, aliases) in catalog.items():
            for alias in aliases:
                pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
                for match in re.finditer(pattern, text, re.I):
                    is_partial_ingredient = " and " in generic_name.lower() and alias.casefold() in {
                        part.strip().casefold() for part in re.split(r"\s+and\s+", re.sub(r"\([^)]*\)", "", generic_name), flags=re.I)
                    }
                    matches.append((match.start(), match.end(), alias.title() if is_partial_ingredient else generic_name, None if is_partial_ingredient else medicine))

        selected = []
        for candidate in sorted(matches, key=lambda item: (item[0], -(item[1] - item[0]))):
            if any(candidate[0] < item[1] and candidate[1] > item[0] for item in selected):
                continue
            selected.append(candidate)
        return sorted(selected, key=lambda item: item[0])

    def _parse_catalog_medication(self, segment, generic_name, medicine):
        medicine = medicine or {}
        dose_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|puffs?))\b", segment, re.I)
        dosage = dose_match.group(1) if dose_match else "Dose not specified"

        frequency_codes = sorted(set(self.kb.sig_frequencies) | {"BID", "HS", "ON", "OM"}, key=len, reverse=True)
        frequency_pattern = r"\b(" + "|".join(re.escape(code) for code in frequency_codes) + r")\b"
        frequency_match = re.search(frequency_pattern, segment, re.I)
        frequency_code = frequency_match.group(1).upper() if frequency_match else None
        frequency_aliases = {
            "once daily": "OD", "twice daily": "BD", "three times daily": "TID",
            "four times daily": "QID", "as needed": "PRN"
        }
        if not frequency_code:
            for phrase, code in frequency_aliases.items():
                if re.search(r"\b" + re.escape(phrase) + r"\b", segment, re.I):
                    frequency_code = code
                    break
        frequency_info = self.kb.lookup_sig_frequency(frequency_code) if frequency_code else None

        route_codes = set()
        for route in self.kb.routes.values():
            route_codes.update(re.split(r"\s*[/,]\s*", route.get("code", "")))
        route_codes = sorted((code for code in route_codes if code), key=len, reverse=True)
        route_pattern = r"\b(" + "|".join(re.escape(code) for code in route_codes) + r")\b"
        route_match = re.search(route_pattern, segment, re.I) if route_codes else None
        route_code = route_match.group(1).upper() if route_match else None
        route_info = self.kb.lookup_route(route_code) if route_code else None

        meal_match = re.search(
            r"\b(before|after|with)\s+(?:the\s+)?((?:(?:breakfast|lunch|dinner)(?:\s+and\s+(?:breakfast|lunch|dinner))*)|meals?|food)\b",
            segment,
            re.I,
        )
        code_match = re.search(r"\b(AC|PC|CC)\b", segment, re.I)
        food_code = code_match.group(1).upper() if code_match else None
        if meal_match:
            food_code = {"before": "AC", "after": "PC", "with": "CC"}[meal_match.group(1).lower()]
        elif not food_code and re.search(r"\b(?:bedtime|at\s+night)\b", segment, re.I):
            food_code = "HS"

        explicit_direction = meal_match.group(1).lower() if meal_match else None
        code_conflict = bool(code_match and explicit_direction and {
            "AC": "before", "PC": "after", "CC": "with"
        }.get(code_match.group(1).upper()) != explicit_direction)
        if code_conflict:
            timing_instruction = "The written meal-timing code conflicts with the explicit meal instruction; confirm with the prescriber or pharmacist."
            timing_badge, timing_class = "Conflicting Instructions", "flex-badge"
        elif meal_match:
            meal_text = f"{meal_match.group(1).lower()} {meal_match.group(2).lower()}"
            timing_instruction = f"Take {meal_text}."
            timing_badge = meal_text.title() + (f" ({food_code})" if food_code else "")
            timing_class = {"AC": "ac-badge", "PC": "pc-badge", "CC": "cc-badge"}.get(food_code, "flex-badge")
        elif food_code == "AC":
            timing_instruction = "Take 30 to 60 minutes before food, unless the prescription specifies otherwise."
            timing_badge, timing_class = "Before Food (AC)", "ac-badge"
        elif food_code == "PC":
            timing_instruction = "Take immediately or within 30 minutes after a meal."
            timing_badge, timing_class = "After Food (PC)", "pc-badge"
        elif food_code == "CC":
            timing_instruction = "Take with food."
            timing_badge, timing_class = "With Food (CC)", "cc-badge"
        elif food_code == "HS" or (frequency_code and frequency_code in {"QHS", "HS"}):
            food_code = "HS"
            timing_instruction = "Take at bedtime."
            timing_badge, timing_class = "Bedtime (QHS)", "hs-badge"
        else:
            food_code = None
            timing_instruction = "No meal timing specified in the text."
            timing_badge, timing_class = "Not specified", "flex-badge"

        form_match = re.search(r"\b(Tab|Tablet|Cap|Capsule|Syr|Syrup|Susp|Suspension|Inhaler|Inj|Injection|Drops?)\b", segment, re.I)
        duration_match = re.search(r"\bfor\s+(\d+\s*(?:days?|weeks?|months?))\b", segment, re.I)
        indication_match = re.search(r"\b(?:PRN|SOS)\s+(?:for\s+)?([a-z][a-z /-]{1,30})", segment, re.I)
        indication = indication_match.group(1).strip(" .;,") if indication_match else medicine.get("primary_indications", "Prescribed clinical indication")
        additional_instructions = self._extract_additional_instructions(segment)

        return {
            "raw_block": segment.strip(" ,;"),
            "form": form_match.group(1).title() if form_match else ("Oral" if route_code == "PO" else "Dosage form not specified"),
            "drug_name": generic_name,
            "dosage_strength": dosage,
            "frequency_code": frequency_code or "Unspecified",
            "frequency_english": frequency_info.get("english", frequency_code) if frequency_info else "Not specified in text",
            "route_code": route_code or "Unspecified",
            "route_english": route_info.get("english", "Not specified in text") if route_info else "Not specified in text",
            "food_timing_code": food_code or "Unspecified",
            "food_timing_instruction": timing_instruction,
            "food_timing_badge": timing_badge,
            "food_timing_class": timing_class,
            "instruction_conflict": code_conflict,
            "duration": duration_match.group(1) if duration_match else "As prescribed",
            "additional_instructions": additional_instructions,
            "schedule_slots": frequency_info.get("schedule_slots", []) if frequency_info else [],
            "generic_name": medicine.get("generic_name", generic_name),
            "drug_class": medicine.get("drug_class", "Not identified in local medication reference"),
            "indication": indication,
            "patient_counseling": medicine.get("patient_counseling", "Take exactly as directed by your healthcare provider."),
            "food_rationale": medicine.get("food_rationale", ""),
        }

    @staticmethod
    def _extract_additional_instructions(segment):
        patterns = [
            r"\bdo\s+not\b[^,;.\n]*",
            r"\bavoid\b[^,;.\n]*",
            r"\bwith\s+(?:a\s+)?(?:full\s+glass\s+of\s+)?water\b[^,;.\n]*",
            r"\b(?:PRN|SOS)\s+(?:for\s+)?(?:pain|fever|headache|nausea|cough|wheezing)\b",
        ]
        instructions = []
        for pattern in patterns:
            instructions.extend(match.group(0).strip() for match in re.finditer(pattern, segment, re.I))
        return list(dict.fromkeys(instructions))

    def _parse_medications(self, text):
        """Associate dose and sig instructions with the nearest recognized medicine."""
        mentions = self._find_medicine_mentions(text)
        if not mentions:
            return self._parse_legacy_medications(text)

        medications = []
        for index, (start, end, generic_name, medicine) in enumerate(mentions):
            segment_end = mentions[index + 1][0] if index + 1 < len(mentions) else len(text)
            segment = text[start:segment_end]
            segment = re.split(r"[;\n]", segment, maxsplit=1)[0]
            segment = re.sub(r",?\s*(?:and\s*)?$", "", segment, flags=re.I)
            medications.append(self._parse_catalog_medication(segment, generic_name, medicine))

        def medication_identity(item):
            reference = self.kb.lookup_medicine(item.get("drug_name", ""))
            name = reference.get("generic_name", "") if reference else item.get("generic_name", item.get("drug_name", ""))
            return re.sub(r"[^a-z0-9]", "", name.casefold())

        known_names = {medication_identity(item) for item in medications}
        for fallback in self._parse_legacy_medications(text):
            identity = medication_identity(fallback)
            if identity not in known_names:
                medications.append(fallback)
                known_names.add(identity)
        return medications

    def _parse_legacy_medications(self, text):
        """Parse structured prescription medications across single or multi-line formats."""
        meds = []
        
        # If text has no newlines, insert newlines before numbered items or Tab/Cap
        normalized_text = re.sub(r"(?<=[^\n])(?=\b\d+[\.\)]\s*(?:Tab|Cap|Syr|Susp|Inhaler|Inj)\b)", "\n", text, flags=re.I)
        raw_lines = [l.strip() for l in normalized_text.splitlines() if l.strip()]

        med_blocks = []
        current_block = []

        in_notes_section = False
        for line in raw_lines:
            # If notes or clinical findings section begins, finish medication collection
            if any(k in line.upper() for k in ["CLINICAL FINDINGS", "INVESTIGATION SUMMARY", "CLINICAL NOTES", "IMPRESSION:", "2D ECHO", "ADVICE:", "FOLLOW-UP:"]):
                in_notes_section = True
                if current_block:
                    med_blocks.append(" ".join(current_block))
                    current_block = []
                continue

            if in_notes_section:
                continue

            if any(k in line.upper() for k in ["DOCTOR", "DATE:", "PATIENT:", "HELPLINE", "AUTHORIZED", "OPD REG"]):
                if current_block:
                    med_blocks.append(" ".join(current_block))
                    current_block = []
                continue

            is_new_med = bool(re.match(r"^\d+[\.\)]\s*(?:Tab|Cap|Syr|Susp|Inhaler|Inj)?\b", line, re.I)) or \
                         bool(re.match(r"^(Tab|Cap|Syr|Susp|Inhaler|Inj)\b", line, re.I))
            
            if is_new_med and current_block:
                med_blocks.append(" ".join(current_block))
                current_block = [line]
            elif current_block:
                if any(k in line.upper() for k in ["SIG:", "FREQUENCY:", "TIMING:", "DURATION:", "INDICATION:", "TAB", "CAP", "DOSE", "DAYS"]):
                    current_block.append(line)
                else:
                    if any(line.lower().startswith(p) for p in ["tab", "cap", "syr", "inhaler", "inj"]):
                        med_blocks.append(" ".join(current_block))
                        current_block = [line]
                    else:
                        current_block.append(line)
            elif is_new_med:
                current_block = [line]

        if current_block:
            med_blocks.append(" ".join(current_block))

        for block in med_blocks:
            has_form = any(f in block.lower() for f in ["tab", "cap", "syr", "susp", "inhaler", "inj", "drops"])
            has_dose = bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|puffs?)\b", block, re.I))
            
            if not (has_form or has_dose):
                continue

            dose_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|puffs?))\b", block, re.I)
            dosage = dose_match.group(1) if dose_match else "Standard dose"

            form_match = re.search(r"\b(Tab|Tablet|Cap|Capsule|Syr|Syrup|Susp|Suspension|Inhaler|Inj|Injection)\b", block, re.I)
            form = form_match.group(1).title() if form_match else "Oral Dosage"

            freq_match = re.search(r"\b(OD|QD|BD|BID|TID|TDS|QID|QDS|QHS|HS|Q4H|Q6H|Q8H|Q12H|PRN|SOS|STAT|QWK|ON|OM)\b", block, re.I)
            freq_code = freq_match.group(1).upper() if freq_match else None
            freq_info = self.kb.lookup_sig_frequency(freq_code) if freq_code else None

            meal_match = re.search(r"\b(before|after|with)\s+(?:the\s+)?(breakfast|lunch|dinner|meals?|food)\b", block, re.I)
            food_match = re.search(r"\b(AC|PC|CC)\b", block, re.I)
            food_code = food_match.group(1).upper() if food_match else None
            if meal_match:
                food_code = {"before": "AC", "after": "PC", "with": "CC"}[meal_match.group(1).lower()]
            elif not food_code and ("bedtime" in block.lower() or freq_code in ["QHS", "HS"]):
                food_code = "HS"

            route_codes = sorted({code.strip() for route in self.kb.routes.values() for code in re.split(r"[/,]", route.get("code", "")) if code.strip()}, key=len, reverse=True)
            route_match = re.search(r"\b(" + "|".join(re.escape(code) for code in route_codes) + r")\b", block, re.I) if route_codes else None
            route_code = route_match.group(1).upper() if route_match else None
            route_info = self.kb.lookup_route(route_code) if route_code else None

            dur_match = re.search(r"(?:Duration:\s*|\bfor\s+|\bx\s*)(\d+\s*(?:days?|weeks?|months?)|x\s*\d+\/\d+|\d+\s*d)\b", block, re.I)
            duration = dur_match.group(1) if dur_match else "As prescribed"

            name_part = block
            name_part = re.sub(r"^\d+[\.\)]\s*", "", name_part)
            name_part = re.sub(r"^(?:Tab|Tablet|Cap|Capsule|Syr|Syrup|Susp|Suspension|Inhaler|Inj|Injection)\.?\s+", "", name_part, flags=re.I)
            if dose_match:
                name_candidate = name_part[:name_part.find(dose_match.group(0))].strip()
            else:
                delim = min([name_part.find(d) for d in ["Sig:", "Frequency:", "Timing:", "-", "|", ":"] if name_part.find(d) != -1] or [len(name_part)])
                name_candidate = name_part[:delim].strip()

            drug_name = " ".join(name_candidate.split()[:4]).strip(" ,.-")
            if not drug_name or len(drug_name) < 2:
                drug_name = "Prescribed Medication"

            med_db = self.kb.lookup_medicine(drug_name)

            if meal_match:
                meal_text = f"{meal_match.group(1).lower()} {meal_match.group(2).lower()}"
                timing_instruction = f"Take {meal_text}."
                timing_badge = meal_text.title() + (f" ({food_code})" if food_code else "")
                timing_class = {"AC": "ac-badge", "PC": "pc-badge", "CC": "cc-badge"}.get(food_code, "flex-badge")
            elif food_code == "AC":
                timing_instruction, timing_badge, timing_class = "Take 30 to 60 minutes before food.", "Before Food (AC)", "ac-badge"
            elif food_code == "PC":
                timing_instruction, timing_badge, timing_class = "Take immediately or within 30 minutes after a meal.", "After Food (PC)", "pc-badge"
            elif food_code == "CC":
                timing_instruction, timing_badge, timing_class = "Take with food.", "With Food (CC)", "cc-badge"
            elif food_code == "HS" or freq_code in ["QHS", "HS"]:
                food_code = "HS"
                timing_instruction, timing_badge, timing_class = "Take at bedtime.", "Bedtime (QHS)", "hs-badge"
            else:
                food_code = None
                timing_instruction, timing_badge, timing_class = "No meal timing specified in the text.", "Not specified", "flex-badge"

            ind_match = re.search(r"\(Indication:\s*([^\)]+)\)", block, re.I)
            stated_indication = ind_match.group(1).strip() if ind_match else None

            meds.append({
                "raw_block": block,
                "form": form,
                "drug_name": drug_name.title(),
                "dosage_strength": dosage,
                "frequency_code": freq_code or "Unspecified",
                "frequency_english": freq_info.get("english", freq_code) if freq_info else "Not specified in text",
                "route_code": route_code or "Unspecified",
                "route_english": route_info.get("english", "Not specified in text") if route_info else "Not specified in text",
                "food_timing_code": food_code or "Unspecified",
                "food_timing_instruction": timing_instruction,
                "food_timing_badge": timing_badge,
                "food_timing_class": timing_class,
                "duration": duration,
                "additional_instructions": self._extract_additional_instructions(block),
                "schedule_slots": freq_info.get("schedule_slots", []) if freq_info else [],
                "generic_name": med_db["generic_name"] if med_db else drug_name.title(),
                "drug_class": med_db["drug_class"] if med_db else "Pharmacotherapy",
                "indication": stated_indication or (med_db["primary_indications"] if med_db else "Prescribed clinical indication"),
                "patient_counseling": med_db.get("patient_counseling") if med_db else "Take exactly as directed by your healthcare provider.",
                "food_rationale": med_db.get("food_rationale", "") if med_db else ""
            })

        return meds

    def _generate_daily_schedule(self, medications):
        """Build chronological daily patient schedule with food relation."""
        schedule = {
            "morning": {
                "label": "Morning (07:00 AM - 09:00 AM)",
                "icon": "sun",
                "items": []
            },
            "afternoon": {
                "label": "Afternoon (12:30 PM - 02:00 PM)",
                "icon": "sun-medium",
                "items": []
            },
            "evening": {
                "label": "Evening (07:00 PM - 08:30 PM)",
                "icon": "sunset",
                "items": []
            },
            "bedtime": {
                "label": "Bedtime (09:30 PM - 10:30 PM)",
                "icon": "moon",
                "items": []
            },
            "as_needed": {
                "label": "As Needed / PRN / SOS (In Emergency or Pain)",
                "icon": "alert-circle",
                "items": []
            }
        }

        for med in medications:
            slots = med.get("schedule_slots", ["morning"])
            timing_order = 0 if "AC" in med.get("food_timing_code", "") else (1 if "CC" in med.get("food_timing_code", "") else 2)
            
            item_entry = {
                "name": med["drug_name"],
                "dose": med["dosage_strength"],
                "instruction": med["food_timing_instruction"],
                "badge": med["food_timing_badge"],
                "badge_class": med["food_timing_class"],
                "indication": med["indication"],
                "order": timing_order
            }

            for slot in slots:
                if slot in schedule:
                    schedule[slot]["items"].append(item_entry)

        for slot in schedule:
            schedule[slot]["items"].sort(key=lambda x: x["order"])

        return schedule

    def _extract_diagnoses(self, text):
        """Identify diagnosis terms and preserve their occurrence-level clinical status."""
        diagnoses = {}

        def add_diagnosis(abbreviation, full_name, specialty, icd10, plain_english, pattern):
            matches = list(re.finditer(pattern, text, re.I))
            if not matches:
                return
            details = []
            for match in matches:
                sentence, _clause = self._sentence_context(text, match.start(), match.end())
                details.append({
                    "clinical_status": self._clinical_status(abbreviation, sentence),
                    "context_snippet": sentence,
                })
            statuses = list(dict.fromkeys(item["clinical_status"] for item in details))
            diagnoses[abbreviation.upper()] = {
                "abbreviation": abbreviation,
                "full_name": full_name,
                "specialty": specialty,
                "icd10": icd10,
                "plain_english": plain_english,
                "clinical_status": statuses[0] if len(statuses) == 1 else "Mixed Clinical Status",
                "occurrence_details": details,
            }

        for d in self.kb.diseases:
            pattern = r"\b" + re.escape(d["abbreviation"]) + r"\b"
            add_diagnosis(d["abbreviation"], d["full_name"], d["specialty"], d["icd10_hint"], d["plain_english"], pattern)

        for item in self.kb.clinical_abbreviations.values():
            if not item["category"].startswith(("Diagnosis", "Symptom")):
                continue
            pattern = r"\b" + re.escape(item["abbreviation"]) + r"\b"
            add_diagnosis(item["abbreviation"], item["full_form"], item["specialty"], None, item["explanation"], pattern)

        for term, (full_name, category, explanation) in CLINICAL_TERMS.items():
            if category != "Disease / Diagnosis":
                continue
            pattern = r"\b" + re.escape(term) + r"\b"
            add_diagnosis(full_name, full_name, category, None, explanation, pattern)

        return list(diagnoses.values())

    def _generate_patient_summary(self, medications, diagnoses, schedule, abbreviations=None):
        """Create clean, easy-to-understand bullet points for the patient."""
        summary_points = []

        clinical_findings = {}
        clinical_categories = {
            "Disease / Diagnosis", "Clinical Abbreviation", "Symptom / Respiratory",
            "Diagnosis / Cardiology", "Investigation / Cardiology Measurement",
            "Investigation / Laboratory Test", "Investigation / Lipid Panel",
            "Investigation / Diabetes Monitoring", "Clinical Measurement",
            "Investigation / Imaging", "Follow-up / Care Setting",
        }
        for item in abbreviations or []:
            if item.get("category") not in clinical_categories:
                continue
            details = item.get("occurrence_details") or [{
                "meaning": item.get("meaning"),
                "clinical_status": item.get("clinical_status", "Mentioned / Uncertain"),
            }]
            term_findings = clinical_findings.setdefault(item["token"], {})
            for detail in details:
                status = detail.get("clinical_status", "Mentioned / Uncertain")
                if detail.get("meaning") in {"Ambiguous abbreviation", "Unrecognized abbreviation"}:
                    continue
                statuses = term_findings.setdefault(detail["meaning"], [])
                if status not in statuses:
                    statuses.append(status)

        if clinical_findings:
            finding_text = []
            for token, meanings in clinical_findings.items():
                meaning_text = [
                    f"{meaning}: {', '.join(statuses)}" for meaning, statuses in meanings.items()
                ]
                finding_text.append(f"{token} ({'; '.join(meaning_text)})")
            summary_points.append(
                "**Clinical findings by source context:** " + "; ".join(finding_text) + "."
            )
        elif diagnoses:
            diag_names = ", ".join([f"{d['full_name']} ({d['abbreviation']})" for d in diagnoses])
            summary_points.append(f"**Identified Clinical Conditions:** Your record addresses {diag_names}.")

        extracted_medications = []
        for medication in medications:
            details = []
            if medication.get("dosage_strength") not in {"Dose not specified", "Standard dose", ""}:
                details.append(medication["dosage_strength"])
            if medication.get("route_code") not in {"Unspecified", ""}:
                details.append(medication["route_code"])
            if medication.get("frequency_code") not in {"Unspecified", ""}:
                details.append(medication["frequency_code"])
            if medication.get("food_timing_code") not in {"Unspecified", "Flexible", ""}:
                details.append(medication["food_timing_instruction"])
            details.extend(medication.get("additional_instructions", []))
            if details:
                extracted_medications.append(f"{medication['drug_name']}: {', '.join(dict.fromkeys(details))}")
        if extracted_medications:
            summary_points.append("**Prescription details extracted:** " + "; ".join(extracted_medications) + ".")

        # Do not leave the patient-summary panel empty when the input contains
        # only document/administrative terminology and no clinical findings.
        if not summary_points:
            document_terms = []
            for item in abbreviations or []:
                if item.get("category") in {"Document / Records Term", "Department / General Term"}:
                    meaning = item.get("meaning")
                    token = item.get("token")
                    if meaning and token and meaning not in {"Ambiguous abbreviation", "Unrecognized abbreviation"}:
                        document_terms.append(f"{token} means {meaning}")
            if document_terms:
                summary_points.append("**Document terminology identified:** " + "; ".join(dict.fromkeys(document_terms)) + ".")
            else:
                summary_points.append("No clinical findings or prescription details could be extracted from this text.")

        return summary_points