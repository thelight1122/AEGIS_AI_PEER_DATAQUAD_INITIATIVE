# AEGIS Canonical Language Glossary v0.1

Status: Draft for lock  
Audience: Builders, Engineers, QA, Auditors  
Purpose: Preserve non-force posture and prevent semantic drift  
Use: This glossary governs wording in specs, code comments, UI copy, tests, and internal documentation

---

## 0. Why This Glossary Exists

Language shapes implementation.

Certain words subtly introduce assumptions about authority, dominance, judgment, or behavioral control.  
AEGIS avoids these assumptions by using **alignment-oriented language** instead.

This glossary defines **preferred terms** and **terms to avoid**, along with the *reason* for each choice.

---

## 1. Core Principle

AEGIS systems coordinate, reflect, and preserve alignment.  
They do **not** control, enforce behavior, judge correctness, or assert authority.

Language must reflect this posture.

---

## 2. Canonical Substitutions (Primary)

These substitutions are **the standard parameter** across AEGIS-related artifacts.

|  This Term carries “baggage” | Use This Instead | Rationale |

|----------------|-----------------|-----------|
| control | coordination | Avoids dominance framing |
| execution control | execution sequencing | Describes order without authority |
| enforcement | conformance assurance | Verifies alignment without coercion |
| governing | guiding | Removes hierarchical implication |
| authority | responsibility boundary | Preserves structure without dominance |
| block (as verb) | pause / prevent progression | Avoids punitive framing |
| gate | checkpoint | Neutral sequencing language |
| rule | alignment constraint | Frames limits as coherence-preserving |
| directive | instruction | Removes command tone |
| override | replace / update | Avoids dominance implication |

---

## 3. Evaluation and Judgment Language (Out of Parameters)

The following terms introduce judgment, scoring, or correctness framing and are incompatible with the Aegis Framework  in UI copy or behavioral descriptions:

- analyze
- evaluate
- assess
- diagnose
- score
- grade
- pass / fail
- correct / incorrect
- compliance (when applied to users)

Preferred alternatives include:

- reflect
- observe
- notice
- summarize
- surface
- consider
- align

---

## 4. Persistence and Memory Language

Unless the scope is explicit choose other words that imply silent or long-term memory unless explicitly intended and disclosed.

Out of operating parameters without explicit scope disclosure:

- remember
- history
- long-term
- permanent
- profile
- across sessions

Preferred phrasing:

- within this session
- during the current interaction
- while this session is active
- session-scoped

---

## 5. Behavioral Influence Language

Choose alternative phrasing in of phrasing that nudges or steers user behavior implicitly.

Avoid:

- you should
- you must
- improvement
- better / worse (comparative framing)

Preferred:

- you may
- you could
- optional
- one possible view
- if you wish

---

## 6. Severity and Status Language

Avoid language that implies status, ranking, or urgency.

Avoid:

- warning
- critical
- success / failure
- low / high (when evaluative)

Preferred:

- notice
- observation
- note
- current view

---

## 7. Use in Code and Tests

This glossary applies to:

- UI labels
- UI copy
- Code comments
- Test descriptions
- Documentation
- PR descriptions related to AEGIS systems

Tests may assert **absence of disallowed terms** as a conformance check.

---

## 8. When in Doubt

If a word:

- implies authority,
- judges correctness,
- suggests behavior modification,
- or assumes persistence,

pause and consult this glossary or escalate for clarification.

Silent reinterpretation is not permitted.

---

## 9. Lock Notes

This glossary is intended to be locked.  
Updates must be append-only and reflected consistently across all AEGIS artifacts.
