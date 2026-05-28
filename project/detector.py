import html
import re
from typing import Dict, List

from ml_model import predict_malicious_probability


BLACKLIST = [
    "ignore previous instructions",
    "act as dan",
    "developer mode",
    "bypass safety",
    "reveal system prompt",
    "jailbreak",
    "unrestricted ai",
]


REGEX_PATTERNS = [
    re.compile(r"ign[0o]re\s+(?:the\s+)?(?:previous\s+)?instruc[ti1]ons", re.IGNORECASE),
    re.compile(r"act\s+as\s+dan", re.IGNORECASE),
    re.compile(r"developer\s+mode", re.IGNORECASE),
    re.compile(r"bypass\s+(?:all\s+)?rules?", re.IGNORECASE),
    re.compile(r"bypass\s+safety", re.IGNORECASE),
    re.compile(r"reveal\s+(?:the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"unrestricted\s+ai", re.IGNORECASE),
    re.compile(r"pretend\s+to\s+be", re.IGNORECASE),
]


LEET_MAP = str.maketrans({
    "0": "o",
    "1": "i",
    "2": "z",
    "3": "e",
    "4": "a",
    "5": "s",
    "6": "g",
    "7": "t",
    "8": "b",
    "@": "a",
    "$": "s",
})


def sanitize_prompt(prompt):
    text = html.unescape(prompt or "")
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_text(prompt):
    return sanitize_prompt(prompt).lower().translate(LEET_MAP)


def detect_keywords(prompt) -> List[str]:
    normalized = normalize_text(prompt)
    hits = [phrase for phrase in BLACKLIST if phrase in normalized]
    return hits


def detect_regex(prompt) -> List[str]:
    normalized = normalize_text(prompt)
    hits = []
    for pattern in REGEX_PATTERNS:
        if pattern.search(normalized):
            hits.append(pattern.pattern)
    return hits


def determine_risk_level(score):
    if score >= 70:
        return "High Risk"
    if score >= 35:
        return "Medium Risk"
    return "Safe"


def analyze_prompt(prompt, model=None):
    safe_prompt = sanitize_prompt(prompt)
    keyword_hits = detect_keywords(safe_prompt)
    regex_hits = detect_regex(safe_prompt)
    malicious_probability = predict_malicious_probability(model, safe_prompt)

    score = 0
    if keyword_hits:
        score += 40 + (len(keyword_hits) - 1) * 4
    if regex_hits:
        score += 30 + (len(regex_hits) - 1) * 3
    score += int(malicious_probability * 40)

    suspicious_terms = [
        "system prompt",
        "ignore",
        "override",
        "rules",
        "instructions",
        "developer",
        "safety",
    ]
    normalized = normalize_text(safe_prompt)
    if any(term in normalized for term in suspicious_terms):
        score += 5

    score = max(0, min(100, score))
    risk_level = determine_risk_level(score)

    if risk_level == "High Risk":
        decision = "Blocked"
    elif risk_level == "Medium Risk":
        decision = "Review"
    else:
        decision = "Allowed"

    reasons = []
    if keyword_hits:
        reasons.append(f"Keyword match: {', '.join(keyword_hits)}")
    if regex_hits:
        reasons.append("Regex pattern matched")
    if malicious_probability >= 0.5:
        reasons.append("Machine learning flagged the prompt")
    if not reasons:
        reasons.append("No strong attack indicators detected")

    return {
        "prompt": safe_prompt,
        "keyword_hits": keyword_hits,
        "regex_hits": regex_hits,
        "malicious_probability": round(malicious_probability, 3),
        "risk_score": score,
        "risk_level": risk_level,
        "decision": decision,
        "blocked": decision == "Blocked",
        "reasons": reasons,
    }
