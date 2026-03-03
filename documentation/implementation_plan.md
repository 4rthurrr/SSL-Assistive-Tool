# Implementation Plan - Switch to Rule-Based Engine

## Status: COMPLETED ✅
**Date Completed:** 2026-02-10

## Problem
The user input "මට තේ ඕන" (I want tea) translates to "I Tea Smile".
- **Cause:** `app.py` is currently using `learned_engine.translate()`, which is an experimental AI model. It appears to have hallucinated "Smile" instead of "Want".
- **Evidence:** `app.py` lines 56-59 show `get_ssl_sequence` (Rule-Based) is commented out, and `learned_engine` is active.

## Proposed Changes

### Backend
#### [MODIFY] [app.py](file:///c:/Users/ASUS/Desktop/csv-project/backend/app.py)
- Uncomment the Rule-Based Pipeline lines.
- Comment out or remove the Learned Model lines.
- Ensure `nlp_grammar` imports are active.

```python
# Before
# from nlp_grammar import get_ssl_sequence, get_ssl_display_sequence # Legacy Rule-based
from inference_engine import LearnedInference

# After
from nlp_grammar import get_ssl_sequence, get_ssl_display_sequence 
# from inference_engine import LearnedInference
```

## Verification Plan
### Manual Verification
1.  Restart backend (`python app.py`).
2.  Input "මට තේ ඕන".
3.  Expect output: "මම" (I), "තේ" (Tea), "ඕන" (Want).
