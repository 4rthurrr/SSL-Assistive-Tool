"""
Sinhala Sentence Parser — Semantic NLP Pipeline
================================================
Implements full sentence-level parsing for Sinhala Text-to-SSL:

  Stage 0 : Sentence Segmentation
  Stage 1 : Per-clause tokenisation
  Stage 2 : Tense Detection (verb-suffix rules)
  Stage 3 : SVO / semantic role labelling
  Stage 4 : Semantic JSON representation
  Stage 5 : Gloss sequence generation (respecting SSL SOV word-order)
  Stage 6 : Animation-block output (one block per sentence)

All parsing is rule-based so no external model download is needed.
An optional spaCy/transformer hook is provided for future upgrade.
"""

from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from typing import Optional

# ── Concept database (single source of truth for all Sinhala vocabulary) ────────
try:
    from concepts import CONCEPT_DEFINITIONS
except ImportError:
    import sys, os as _os
    sys.path.append(_os.path.dirname(_os.path.abspath(__file__)))
    from concepts import CONCEPT_DEFINITIONS

# ─────────────────────────────────────────────────────────────────────────────
# LINGUISTIC CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# Sinhala clause boundary markers (these end or separate clauses)
CLAUSE_BOUNDARY_TOKENS: set[str] = {
    ",", ".", "?", "!", ";", ":", "නමුත්", "හෝ", "එමෙන්ම",
    "නිසා", "නිසාම", "ද", "ත්", "ලෙස", "ඇත", "ඇති",
}

# Conjunctions that join clauses (absorbed / dropped in SSL gloss)
COORD_CONJUNCTIONS: set[str] = {"සහ", "හා", "ද", "ත්", "ඒ", "නිසා", "ඇයි"}

# ── Person / pronoun concept IDs (grammar constants — IDs only, no Sinhala words) ──
# Sinhala surface forms are loaded automatically from CONCEPT_DEFINITIONS below.
# To support a new person concept, add it to concepts.py and list its ID here.
_PERSON_CONCEPT_IDS: frozenset = frozenset({
    "CONCEPT_I", "CONCEPT_WE", "CONCEPT_US", "CONCEPT_YOU", "CONCEPT_YOU_ALL",
    "CONCEPT_HE", "CONCEPT_SHE", "CONCEPT_THEY", "CONCEPT_MY",
    "CONCEPT_MOTHER", "CONCEPT_FATHER",
    "CONCEPT_ELDER_BRO", "CONCEPT_ELDER_SISTER",
    "CONCEPT_YOUNGER_BRO", "CONCEPT_YOUNGER_SISTER",
    "CONCEPT_SISTER", "CONCEPT_BROTHER", "CONCEPT_BRO",
    "CONCEPT_CHILD", "CONCEPT_BABY", "CONCEPT_BOY", "CONCEPT_GIRL",
    "CONCEPT_MAN", "CONCEPT_LADY", "CONCEPT_HUSBAND", "CONCEPT_WIFE",
    "CONCEPT_SON", "CONCEPT_DAUGHTER",
    "CONCEPT_GRAND_FATHER", "CONCEPT_GRAND_MOTHER", "CONCEPT_GRAND_SON",
    "CONCEPT_UNCLE", "CONCEPT_AUNT",
    "CONCEPT_TEACHER", "CONCEPT_DOCTOR", "CONCEPT_STUDENT",
})

# ── Negation / Question concept IDs (handled explicitly in Stage 5) ──
_NEGATION_CONCEPT_IDS: frozenset = frozenset({
    "CONCEPT_NO", "CONCEPT_NOT", "CONCEPT_DONT", "CONCEPT_CANT", "CONCEPT_NONE", 
    "CONCEPT_NOT_GOOD", "CONCEPT_NOT_LIKE", "CONCEPT_NOT_LIKE_(DISLIKE)"
})

_QUESTION_CONCEPT_IDS: frozenset = frozenset({
    "CONCEPT_WHAT", "CONCEPT_WHERE", "CONCEPT_WHO", "CONCEPT_WHY", "CONCEPT_WHEN", 
    "CONCEPT_HOW_MANY", "CONCEPT_HOW_MUCH", "CONCEPT_WHICH", "CONCEPT_WHOSE", "CONCEPT_WHOM"
})


# CUSTOM OPTIMIZATION
# Self-synchronizing concept maps built from CONCEPT_DEFINITIONS at import time
# Adding vocabulary to concepts.py auto-updates parser — no manual sync needed
# Replaced earlier hardcoded Sinhala word lists that caused silent mismatches
def _build_subject_map() -> "dict[str, str]":
    """
    Build synonym → concept_id map for every person/subject concept
    directly from CONCEPT_DEFINITIONS.  No Sinhala words are hardcoded here;
    all entries come from the concepts DB.
    """
    result: dict = {}
    for cid in _PERSON_CONCEPT_IDS:
        data = CONCEPT_DEFINITIONS.get(cid, {})
        for syn in data.get("synonyms", []):
            syn_nc = unicodedata.normalize("NFC", syn.strip())
            if syn_nc:
                result[syn_nc] = cid
    return result


# Built once at import time from the concept DB — automatically stays in sync.
SUBJECT_MAP: dict = _build_subject_map()

# Lazy vocab cache shared by _strip_case_suffix (populated on first call).
_PARSER_VOCAB: "set | None" = None

# ── Object / Noun clues ──────────────────────────────────────────────────────
OBJECT_PARTICLES: tuple[str, ...] = (
    "ව", "ව​", "ට", "ගෙ", "ගේ", "ගෙන්", "ගෙන", "ෙන්", "ේ",
)

# ── Tense detection — verb suffix rules ─────────────────────────────────────
#   Each entry: (suffix_pattern,  tense_label, base_verb_strip_chars)
#
#   Sinhala tense suffixes (unicode-normalized, NFC):
#     Past   : -ෑවා  -ාවා  -ුවා  -ිෙ  -ාල  past compound → ආවා, ගියා, කෑවා, …
#     Present: -නවා  -නෙ   -ෙනවා
#     Future : -ාවි  -ෙවි   -නවා (with future adverb context)
#
# RESEARCH CONTRIBUTION
# Manual Sinhala tense detection: 20+ verb suffix regex patterns (PAST/PRESENT/FUTURE)
# Dual evidence: tense adverbs (high confidence 0.95) + verb suffixes (0.80)
# Right-to-left scan respects SOV structure where verb appears last
TENSE_RULES: list[tuple[str, str]] = [
    # ── PAST ──────────────────────────────────────────────────────────────
    # Match dependent-vowel-sign ා (U+0DCF) or independent ආ (U+0D86) before වා
    (r"[ා\u0D86]වා$", "PAST"),   # covers ගෙනාවා, ආවා, උසාවා …
    (r"ෑවා$",          "PAST"),   # කෑවා, බෑවා
    (r"ෙවා$",          "PAST"),   # ගෙනෙවා
    (r"ිෙ$",           "PAST"),
    (r"ාල$",           "PAST"),   # ගිහිල්, ඇවිල්
    (r"ල්ල$",          "PAST"),   # ගෙනාල්ල
    (r"ාවො$",          "PAST"),
    (r"ිෙහේ$",         "PAST"),
    (r"ාවේ$",          "PAST"),
    # explicit common irregular past forms
    (r"(ගියා|බෑවා|කෑවා|ගත්තා|දුන්නා|ගෙනාවා|නෑවා|ඇවිල්ල)$", "PAST"),
    # ── PRESENT ───────────────────────────────────────────────────────────
    (r"නවා$",          "PRESENT"),
    (r"නෙ$",           "PRESENT"),
    (r"ෙනවා$",         "PRESENT"),
    (r"ෙනෙ$",          "PRESENT"),
    # ── FUTURE ────────────────────────────────────────────────────────────
    (r"ාවි$",          "FUTURE"),
    (r"ෙවි$",          "FUTURE"),
    (r"ෙනවිය$",        "FUTURE"),
    (r"ානෙ$",          "FUTURE"),
]

# ── Tense concept IDs → tense label (grammar constants — IDs only) ───────────
# Sinhala surface forms are loaded from CONCEPT_DEFINITIONS at import time.
# To add a new tense-signalling word, add its synonym to the relevant concept
# in concepts.py — no change needed here.
_TENSE_CONCEPT_TO_TENSE: dict = {
    "CONCEPT_YESTERDAY":          "PAST",
    "CONCEPT_PAST":               "PAST",
    "CONCEPT_NOW":                "PRESENT",
    "CONCEPT_TODAY":              "PRESENT",
    "CONCEPT_MORNING":            "PRESENT",
    "CONCEPT_TOMORROW":           "FUTURE",
    "CONCEPT_FUTURE":             "FUTURE",
    "CONCEPT_DAY_AFTER_TOMORROW": "FUTURE",
}


def _build_tense_adverb_map() -> dict:
    """
    Build synonym → tense-label map from the concept DB.
    Every synonym of CONCEPT_YESTERDAY / TODAY / TOMORROW / etc.
    automatically becomes a tense trigger — no manual word list required.
    """
    result: dict = {}
    for cid, tense in _TENSE_CONCEPT_TO_TENSE.items():
        data = CONCEPT_DEFINITIONS.get(cid, {})
        for syn in data.get("synonyms", []):
            syn_nc = unicodedata.normalize("NFC", syn.strip())
            if syn_nc:
                result[syn_nc] = tense
    return result


# Built once at import time — automatically stays in sync with concepts.py
TENSE_ADVERB_MAP: dict = _build_tense_adverb_map()


# ── Verb concept IDs (grammar constants — IDs only, no Sinhala words) ────────
# All Sinhala surface forms (present, past, imperative …) are loaded from the
# concept DB via _build_verb_concept_map().  To add a verb's inflected form,
# add it to the relevant concept's synonyms list in concepts.py.
_VERB_CONCEPT_IDS: frozenset = frozenset({
    "CONCEPT_GO", "CONCEPT_COME", "CONCEPT_EAT", "CONCEPT_DRINK",
    "CONCEPT_SLEEP", "CONCEPT_RUN", "CONCEPT_WALK", "CONCEPT_JUMP",
    "CONCEPT_SIT", "CONCEPT_DANCE", "CONCEPT_PLAY", "CONCEPT_WASH",
    "CONCEPT_COOK", "CONCEPT_CUT", "CONCEPT_DRAW", "CONCEPT_WRITE",
    "CONCEPT_READ", "CONCEPT_WATCH", "CONCEPT_SEE", "CONCEPT_LISTEN",
    "CONCEPT_TALK", "CONCEPT_TELL", "CONCEPT_GIVE", "CONCEPT_TAKE",
    "CONCEPT_BRING", "CONCEPT_BUY", "CONCEPT_SELL", "CONCEPT_HELP",
    "CONCEPT_LOVE", "CONCEPT_LIKE", "CONCEPT_WANT", "CONCEPT_STOP",
    "CONCEPT_OPEN", "CONCEPT_CLOSE", "CONCEPT_MAKE", "CONCEPT_USE",
    "CONCEPT_WORK", "CONCEPT_STUDY", "CONCEPT_TEACH", "CONCEPT_THINK",
    "CONCEPT_UNDERSTAND", "CONCEPT_FEEL", "CONCEPT_LAUGH", "CONCEPT_CRY",
    "CONCEPT_SMILE", "CONCEPT_ENTER", "CONCEPT_GET_UP", "CONCEPT_MEET",
    "CONCEPT_SHOW", "CONCEPT_SELECT", "CONCEPT_SEARCH", "CONCEPT_PUT",
    "CONCEPT_CARRY", "CONCEPT_PULL", "CONCEPT_HANG", "CONCEPT_BOIL",
    "CONCEPT_BATHE", "CONCEPT_SCRATCH", "CONCEPT_BREAK", "CONCEPT_CHANGE",
    "CONCEPT_SWEEP", "CONCEPT_SWIM", "CONCEPT_KNOCK", "CONCEPT_ERASE",
    "CONCEPT_CLICK", "CONCEPT_ORDER", "CONCEPT_FOLLOW", "CONCEPT_TRUST",
    "CONCEPT_SHARE", "CONCEPT_EXCHANGE", "CONCEPT_CONNECT", "CONCEPT_FIGHT",
    "CONCEPT_COPY", "CONCEPT_HIT", "CONCEPT_COUNT", "CONCEPT_COVER",
    "CONCEPT_PEEING", "CONCEPT_LEAD", "CONCEPT_THROW",
})


def _build_verb_concept_map() -> dict:
    """
    Build synonym → concept_id map for every verb concept from the DB.
    Present-tense, past-tense, imperative, and all other synonym forms
    stored in concepts.py are automatically included.  Adding a new inflected
    form only requires updating concepts.py — not this file.
    """
    result: dict = {}
    for cid in _VERB_CONCEPT_IDS:
        data = CONCEPT_DEFINITIONS.get(cid, {})
        for syn in data.get("synonyms", []):
            syn_nc = unicodedata.normalize("NFC", syn.strip())
            if syn_nc:
                result[syn_nc] = cid
    return result


# Built once at import time — automatically stays in sync with concepts.py
VERB_CONCEPT_MAP: dict = _build_verb_concept_map()

# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TenseInfo:
    tense: str           # PAST | PRESENT | FUTURE | UNKNOWN
    evidence: str        # suffix or adverb that triggered the detection
    confidence: float    # 0.0 – 1.0


@dataclass
class SemanticClause:
    """One independent clause extracted from the input sentence."""
    raw_text: str
    subject: Optional[str]         # Sinhala surface form
    subject_concept: Optional[str] # CONCEPT_* id
    verb_surface: Optional[str]    # Sinhala surface form
    verb_concept: Optional[str]    # CONCEPT_* id
    objects: list[str]             # Sinhala surface forms
    object_concepts: list[str]     # CONCEPT_* ids
    tense: TenseInfo
    modifiers: list[str]           # adverbs, time expressions, etc.
    modifier_concepts: list[str]
    negated: bool = False
    interrogative: bool = False


@dataclass
class SemanticSentence:
    """Full sentence = list of clauses + metadata."""
    original_text: str
    clauses: list[SemanticClause] = field(default_factory=list)


@dataclass
class GlossBlock:
    """Ready-to-animate block for one clause."""
    clause_index: int
    tense: str
    gloss_sequence: list[str]      # ordered CONCEPT_* ids for SSL
    display_sinhala: list[str]     # human-readable Sinhala for UI
    raw_clause: str


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 0 — SENTENCE SEGMENTATION
# ─────────────────────────────────────────────────────────────────────────────

# RESEARCH CONTRIBUTION
# Full 6-stage Sinhala-to-SSL semantic NLP pipeline (rule-based, no external model)
# Stage 0–6: Segmentation → Tokenization → Tense → SVO → Gloss → AnimationBlock
# Designed for low-resource Sinhala SSL — no pre-trained Sinhala NLP model available

# Words and punctuation marks in a separated sentence are identified separately.

def segment_sentences(text: str) -> list[str]:
    """
    Split text into individual sentences on Sinhala & ASCII sentence-ending
    punctuation.  Commas that separate clauses (not lists) are also treated
    as clause breaks.
    Returns a list of non-empty stripped sentence strings.
    """
    text = unicodedata.normalize("NFC", text.strip())

    # Protect decimals (1.5 → no split)
    text = re.sub(r"(\d)\.(\d)", r"\1__DOT__\2", text)

    # Split on: . ? ! ; and comma-space
    parts = re.split(r"[.?!;]\s*|,\s*", text)

    # Restore decimals
    parts = [p.replace("__DOT__", ".") for p in parts]

    # Filter blanks and very short noise fragments
    sentences = [p.strip() for p in parts if len(p.strip()) > 1]
    return sentences


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — TOKENISATION
# ─────────────────────────────────────────────────────────────────────────────
# Words and punctuation marks in a separated sentence are identified separately.


def tokenize_sinhala(sentence: str) -> list[str]:
    """
    Lightweight tokeniser for Sinhala Unicode text.
    Splits on whitespace and removes punctuation tokens.
    """
    sentence = unicodedata.normalize("NFC", sentence)
    # Insert space around punctuation so they become separate tokens
    sentence = re.sub(r"([,.?!;:\"'()।])", r" \1 ", sentence)
    tokens = sentence.split()
    # Strip stray punctuation tokens
    tokens = [t for t in tokens if re.search(r"[\u0D80-\u0DFF\w]", t)]
    return tokens


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — TENSE DETECTION
# ─────────────────────────────────────────────────────────────────────────────
# It identifies whether the sentence is in the past, present, or future tense. Two methods are used here:


def detect_tense(tokens: list[str]) -> TenseInfo:
    """
    Detect tense from:
      1. Tense adverbs in the token stream (high confidence).
      2. Verb suffix patterns on the last content token(s) (medium confidence).
    Returns TenseInfo with the best match.
    """
    # Priority 1 – explicit tense adverb
    for tok in tokens:
        tok_nc = unicodedata.normalize("NFC", tok)
        if tok_nc in TENSE_ADVERB_MAP:
            return TenseInfo(
                tense=TENSE_ADVERB_MAP[tok_nc],
                evidence=f"adverb:{tok_nc}",
                confidence=0.95,
            )

    # Priority 2 – verb suffix on any token (scan right-to-left for the verb)
    for tok in reversed(tokens):
        tok_nc = unicodedata.normalize("NFC", tok)
        for pattern, tense_label in TENSE_RULES:
            if re.search(pattern, tok_nc):
                return TenseInfo(
                    tense=tense_label,
                    evidence=f"suffix:{tok_nc}",
                    confidence=0.80,
                )

    return TenseInfo(tense="UNKNOWN", evidence="none", confidence=0.0)


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3 — SEMANTIC ROLE LABELLING (SVO extraction)
# ─────────────────────────────────────────────────────────────────────────────
# In a sentence, who is doing the action (Subject), what is being done (Verb), and to whom it is being done (Object) are distinguished.

def _lookup_concept(token: str) -> Optional[str]:
    """Return a CONCEPT_* id for a Sinhala token via concepts.py if available."""
    try:
        from concepts import get_concept_by_sinhala, normalize_concept
        cid = get_concept_by_sinhala(token)
        if cid:
            return normalize_concept(cid)
        return None
    except Exception:
        return None


# RESEARCH CONTRIBUTION
# Vocabulary-aware progressive suffix stripping for Sinhala case morphology
# Strips ablative (-ින්), copula (-යි), tag-question (-නේ), emphatic (-ම) etc.
# Validates each candidate stem against the full CONCEPT_DEFINITIONS vocabulary
def _strip_case_suffix(token: str) -> str:
    """
    Vocabulary-aware stem finder for case-marked / predicate-marked tokens.

    Instead of a hardcoded suffix list, the function progressively trims
    1–6 characters from the right and checks each candidate against every
    synonym in CONCEPT_DEFINITIONS.  The first candidate that exists in
    the vocabulary is returned.

    E.g.
        "ගෙදරින්" → "ගෙදර"   (ablative -ින්)
        "නරකයි"   → "නරක"    (predicate copula -යි)
        "හොඳනේ"   → "හොඳ"    (tag question -නේ)
        "නරකද"    → "නරක"    (yes/no question -ද)
        "නරකම"    → "නරක"    (emphatic -ම)

    Falls back to the original token when no vocabulary match is found so
    that the call is always safe.
    """
    global _PARSER_VOCAB
    if _PARSER_VOCAB is None:
        _PARSER_VOCAB = set()
        for _d in CONCEPT_DEFINITIONS.values():
            for _s in _d.get("synonyms", []):
                _sc = _s.strip()
                if _sc:
                    _PARSER_VOCAB.add(unicodedata.normalize("NFC", _sc))

    token_nc = unicodedata.normalize("NFC", token)
    if token_nc in _PARSER_VOCAB:
        return token_nc

    for strip_len in range(1, min(len(token_nc) - 1, 7)):
        candidate = token_nc[:-strip_len]
        if len(candidate) >= 2 and candidate in _PARSER_VOCAB:
            return candidate

    return token


def extract_svo(tokens: list[str]) -> tuple[
    Optional[str], Optional[str],
    Optional[str], Optional[str],
    list[str], list[str]
]:
    """
    Returns (subject, subj_concept, verb, verb_concept, objects, obj_concepts).
    Strategy:
      • Subject  — first token that matches SUBJECT_MAP (or has a concept that
                   is a person/entity).
      • Verb     — token that matches VERB_CONCEPT_MAP (or whose suffix yields
                   a VERB concept via _lookup_concept).
      • Objects  — all remaining meaningful tokens not classified above.
    """
    subject = subject_concept = None
    verb = verb_concept = None
    objects: list[str] = []
    obj_concepts: list[str] = []

    remaining: list[str] = []

    # ── Pass 1: find subject ───────────────────────────────────────────────
    for tok in tokens:
        tok_nc = unicodedata.normalize("NFC", tok)
        if subject is None and tok_nc in SUBJECT_MAP:
            subject = tok_nc
            subject_concept = SUBJECT_MAP[tok_nc]
        else:
            remaining.append(tok)

    tokens_for_vo = remaining
    remaining = []

    # ── Pass 2: find verb ──────────────────────────────────────────────────
    # Try last token first (SOV language — verb usually at end)
    for tok in reversed(tokens_for_vo):
        tok_nc = unicodedata.normalize("NFC", tok)
        if tok_nc in VERB_CONCEPT_MAP:
            verb = tok_nc
            verb_concept = VERB_CONCEPT_MAP[tok_nc]
            break
        # Try suffix-based lookup
        cid = _lookup_concept(tok_nc)
        if cid and cid.startswith("CONCEPT_") and _is_verb_concept(cid):
            verb = tok_nc
            verb_concept = cid
            break

    # Build object list from what's left
    for tok in tokens_for_vo:
        tok_nc = unicodedata.normalize("NFC", tok)
        if tok_nc == verb:
            continue
        if tok_nc in COORD_CONJUNCTIONS or tok_nc in SUBJECT_MAP:
            continue
        # Skip tense adverbs — they belong in the modifier slot, not objects
        if tok_nc in TENSE_ADVERB_MAP:
            continue
        # Strip case suffix then look up concept
        bare = _strip_case_suffix(tok_nc)
        cid = _lookup_concept(bare) or _lookup_concept(tok_nc)
        if cid:
            # Skip negation/question concepts — they are added explicitly in Stage 5
            if cid in _NEGATION_CONCEPT_IDS or cid in _QUESTION_CONCEPT_IDS:
                continue
            objects.append(tok_nc)
            obj_concepts.append(cid)
        else:
            # Keep the surface token even without a concept (for display)
            objects.append(tok_nc)
            obj_concepts.append(f"RAW:{tok_nc}")

    return subject, subject_concept, verb, verb_concept, objects, obj_concepts


def _is_verb_concept(cid: str) -> bool:
    from nlp_grammar import VERB_CONCEPTS  # lazy import to avoid circular
    return cid in VERB_CONCEPTS


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — BUILD SEMANTIC JSON REPRESENTATION
# ─────────────────────────────────────────────────────────────────────────────

def build_semantic_clause(raw_clause: str) -> SemanticClause:
    """
    Full pipeline for a single clause:
      tokenise → tense → SVO → SemanticClause
    """
    tokens = tokenize_sinhala(raw_clause)

    tense_info = detect_tense(tokens)

    # Check negation
    negated = any(
        unicodedata.normalize("NFC", t) in {"නෑ", "නැහැ", "නොහේ", "එපා", "නොකළ"}
        for t in tokens
    )

    # Check interrogative
    interrogative = any(
        unicodedata.normalize("NFC", t) in {"ද", "කෝ", "මොකද", "ඇයි", "කවදා", "කොහෙ"}
        for t in tokens
    ) or raw_clause.strip().endswith("?")

    (subject, subj_concept,
     verb, verb_concept,
     objects, obj_concepts) = extract_svo(tokens)

    # Modifiers = time adverbs + left-over tokens not in SVO
    svo_tokens = {subject, verb} | set(objects)
    modifiers = []
    for t in tokens:
        t_nc = unicodedata.normalize("NFC", t)
        if t_nc in svo_tokens or t_nc in COORD_CONJUNCTIONS:
            continue
        # Skip negation/question tokens - handled explicitly at the end
        cid = _lookup_concept(t_nc)
        if cid in _NEGATION_CONCEPT_IDS or cid in _QUESTION_CONCEPT_IDS:
            continue
        modifiers.append(t_nc)
    mod_concepts = [_lookup_concept(m) or f"RAW:{m}" for m in modifiers]

    return SemanticClause(
        raw_text=raw_clause,
        subject=subject,
        subject_concept=subj_concept,
        verb_surface=verb,
        verb_concept=verb_concept,
        objects=objects,
        object_concepts=obj_concepts,
        tense=tense_info,
        modifiers=modifiers,
        modifier_concepts=mod_concepts,
        negated=negated,
        interrogative=interrogative,
    )


def build_semantic_sentence(text: str) -> SemanticSentence:
    """
    Full segmentation + per-clause semantic parsing.
    """
    clauses_raw = segment_sentences(text)
    result = SemanticSentence(original_text=text)
    for raw in clauses_raw:
        clause = build_semantic_clause(raw)
        result.clauses.append(clause)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 5 — GLOSS GENERATION  (concept-sequence per clause, SSL SOV order)
# ─────────────────────────────────────────────────────────────────────────────

# Tense sign concepts used in SSL to explicitly mark tense
# NOTE: Only EXPLICIT time adverb words (ĕඪĕඡ, ĕ්ĕඳ, etc.) produce sign chips.
#       Tense detected purely from verb suffixes is metadata only — we do NOT
#       inject an abstract \u201cpast\u201d / \u201cfuture\u201d concept chip, because
#       (a) there is no standard isolated SSL sign for these in the video set, and
#       (b) the verb form + facial expression already conveys tense in SSL.
TENSE_SIGN_MAP: dict[str, Optional[str]] = {
    "PAST":    None,
    "PRESENT": None,
    "FUTURE":  None,
    "UNKNOWN": None,
}

NEGATION_SIGN = "CONCEPT_NO"
QUESTION_SIGN = "CONCEPT_WHAT"   # fronted in yes/no questions


# RESEARCH CONTRIBUTION
# Full 6-stage Sinhala-to-SSL semantic NLP pipeline (rule-based, no external model)
# Order: [TIME] → [SUBJECT] → [OBJECTS] → [VERB] → [NEGATION] → [QUESTION]
# Tense injected only from explicit time adverb concepts — not from verb suffix metadata
def generate_gloss(clause: SemanticClause) -> list[str]:
    """
    SSL gloss order (Sri Lankan Sign Language):
      [TIME/TENSE-MARKER]  [SUBJECT]  [OBJECT(s)]  [VERB]  [NEGATION?]
    Objects are kept before verb; subject before objects; time first.

    When tense can't be inferred from a time adverb already in the token
    stream, an explicit TENSE SIGN is prepended.
    """
    gloss: list[str] = []

    # ── 1. Time adverb / tense marker ──────────────────────────────────────
    # Put time modifier concepts first (e.g. CONCEPT_YESTERDAY, CONCEPT_FUTURE)
    from nlp_grammar import TIME_CONCEPTS  # lazy import
    for mod_c in clause.modifier_concepts:
        if mod_c and not mod_c.startswith("RAW:") and mod_c in TIME_CONCEPTS:
            if mod_c not in gloss:
                gloss.append(mod_c)

    # Explicit past/future sign — only when not already covered by a modifier
    tense_sign = TENSE_SIGN_MAP.get(clause.tense.tense)
    if tense_sign and tense_sign not in gloss:
        if clause.tense.tense in ("PAST", "FUTURE"):
            gloss.append(tense_sign)

    # ── 2. Subject ──────────────────────────────────────────────────────────
    if clause.subject_concept:
        gloss.append(clause.subject_concept)

    # ── 3. Objects (before verb — SOV) ─────────────────────────────────────
    for obj_c in clause.object_concepts:
        if obj_c and not obj_c.startswith("RAW:"):
            gloss.append(obj_c)

    # ── 4. Remaining modifiers (descriptors, adjectives) ───────────────────
    for mod_c in clause.modifier_concepts:
        if mod_c and not mod_c.startswith("RAW:") and mod_c not in gloss:
            from nlp_grammar import TIME_CONCEPTS
            if mod_c not in TIME_CONCEPTS:
                gloss.append(mod_c)

    # ── 5. Verb ─────────────────────────────────────────────────────────────
    if clause.verb_concept:
        gloss.append(clause.verb_concept)

    # ── 6. Negation marker (always at end in SSL) ──────────────────────────
    if clause.negated:
        gloss.append(NEGATION_SIGN)

    # ── 7. Question marker ──────────────────────────────────────────────────
    if clause.interrogative:
        gloss.append(QUESTION_SIGN)

    return gloss


def generate_display_labels(gloss: list[str]) -> list[str]:
    """
    Convert CONCEPT_* ids → canonical Sinhala display words for the UI.
    Falls back to the concept id string on missing entries.
    """
    try:
        from concepts import get_sinhala_display
        return [get_sinhala_display(cid) or cid for cid in gloss]
    except Exception:
        return gloss


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 6 — ANIMATION BLOCK OUTPUT
# ─────────────────────────────────────────────────────────────────────────────

def build_animation_blocks(text: str) -> tuple[list[GlossBlock], SemanticSentence]:
    """
    Full pipeline entry point.

    Returns:
      blocks   — one GlossBlock per clause, ready for the animation engine.
      semantic — full SemanticSentence for logging / debugging.
    """
    semantic = build_semantic_sentence(text)
    blocks: list[GlossBlock] = []

    for i, clause in enumerate(semantic.clauses):
        gloss = generate_gloss(clause)
        display = generate_display_labels(gloss)
        block = GlossBlock(
            clause_index=i,
            tense=clause.tense.tense,
            gloss_sequence=gloss,
            display_sinhala=display,
            raw_clause=clause.raw_text,
        )
        blocks.append(block)

    return blocks, semantic


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API — integration bridge for app_translator.py / nlp_grammar.py
# ─────────────────────────────────────────────────────────────────────────────

def parse_text_to_glosses(text: str) -> dict:
    """
    Main integration function.

    Returns a dict::

        {
          "blocks": [
            {
              "clause_index": 0,
              "tense": "PRESENT",
              "gloss_sequence": ["CONCEPT_MOTHER", "CONCEPT_WATER", "CONCEPT_DRINK"],
              "display_sinhala": ["අම්මා", "වතුර", "බොනවා"],
              "raw_clause": "අම්මා වතුර බොනවා"
            },
            {
              "clause_index": 1,
              "tense": "PAST",
              "gloss_sequence": ["CONCEPT_PAST", "CONCEPT_I", "CONCEPT_HOME", "CONCEPT_COME"],
              "display_sinhala": ["ඉකිම", "මම", "ගෙදර", "ආවා"],
              "raw_clause": "මං ගෙදරින් ආවා"
            }
          ],
          "flat_sequence": ["CONCEPT_MOTHER", "CONCEPT_WATER", "CONCEPT_DRINK",
                             "CONCEPT_PAST", "CONCEPT_I", "CONCEPT_HOME", "CONCEPT_COME"],
          "flat_display": ["අම්මා", "වතුර", "බොනවා", "ඉකිම", "මම", "ගෙදර", "ආවා"],
          "semantic_json": { ... }   # full SemanticSentence as dict
        }
    """
    blocks, semantic = build_animation_blocks(text)

    flat_sequence: list[str] = []
    flat_display: list[str] = []
    for b in blocks:
        flat_sequence.extend(b.gloss_sequence)
        flat_display.extend(b.display_sinhala)

    return {
        "blocks": [asdict(b) for b in blocks],
        "flat_sequence": flat_sequence,
        "flat_display": flat_display,
        "semantic_json": _semantic_to_dict(semantic),
    }


def _semantic_to_dict(s: SemanticSentence) -> dict:
    result = {"original_text": s.original_text, "clauses": []}
    for c in s.clauses:
        result["clauses"].append({
            "raw_text": c.raw_text,
            "subject": c.subject,
            "subject_concept": c.subject_concept,
            "verb_surface": c.verb_surface,
            "verb_concept": c.verb_concept,
            "objects": c.objects,
            "object_concepts": c.object_concepts,
            "tense": asdict(c.tense),
            "modifiers": c.modifiers,
            "negated": c.negated,
            "interrogative": c.interrogative,
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# QUICK SMOKE-TEST  (python sinhala_sentence_parser.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    tests = [
        "අම්මා වතුර බොනවා, මං ගෙදරින් ආවා.",
        "ඔහු ගෙදරට ගියා.",
        "මම හෙට පාසලට යනවා.",
        "ළමයා කෑම කෑවා, ඔහු නිදාගත්තා.",
        "ඔයාලා ගෙදර ද?",
    ]

    for text in tests:
        print("\n" + "=" * 60)
        print(f"INPUT : {text}")
        result = parse_text_to_glosses(text)
        print(f"BLOCKS:")
        for b in result["blocks"]:
            print(f"  [{b['tense']}] {b['raw_clause']}")
            print(f"       gloss   : {b['gloss_sequence']}")
            print(f"       display : {b['display_sinhala']}")
        print(f"FLAT  : {result['flat_display']}")
