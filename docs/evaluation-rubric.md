# Evaluation Rubric

How SceneTalk AI assesses learner speech. Each submission is scored across four dimensions.

## Scoring Dimensions

### 1. Pronunciation (0–100)

Evaluated at the phoneme level. The pronunciation provider returns per-phoneme scores; these are averaged and weighted by phoneme frequency.

| Score Range | Label     | Description                                      |
|-------------|-----------|--------------------------------------------------|
| 90–100      | Excellent | Near-native phoneme production                   |
| 75–89       | Good      | Minor deviations, fully intelligible             |
| 60–74       | Fair      | Noticeable accent, occasional misunderstanding   |
| 40–59       | Poor      | Frequent mispronunciation, effort to understand  |
| 0–39        | Very Poor | Mostly unintelligible                             |

### 2. Fluency (0–100)

Measured by pause frequency, speech rate, and rhythm. Derived from STT timestamps and silence detection.

| Score Range | Label     | Description                                      |
|-------------|-----------|--------------------------------------------------|
| 90–100      | Excellent | Natural pace, smooth transitions                 |
| 75–89       | Good      | Minor hesitations, overall smooth                |
| 60–74       | Fair      | Noticeable pauses, some unnatural breaks         |
| 40–59       | Poor      | Frequent long pauses, choppy delivery            |
| 0–39        | Very Poor | Word-by-word, unable to form phrases             |

### 3. Grammar (0–100)

Assessed by the LLM comparing the learner's transcript to the model answer, checking for grammatical correctness, word order, and particle usage.

| Score Range | Label     | Description                                      |
|-------------|-----------|--------------------------------------------------|
| 90–100      | Excellent | No errors or one trivial slip                    |
| 75–89       | Good      | Minor errors that don't affect meaning           |
| 60–74       | Fair      | Some errors, meaning still clear                 |
| 40–59       | Poor      | Frequent errors, meaning partially obscured      |
| 0–39        | Very Poor | Pervasive errors, meaning unclear                |

### 4. Vocabulary / Task Completion (0–100)

Assessed by the LLM: did the learner use appropriate vocabulary for the scene? Did they complete the communicative task?

| Score Range | Label     | Description                                      |
|-------------|-----------|--------------------------------------------------|
| 90–100      | Excellent | Rich, appropriate vocabulary; task fully done    |
| 75–89       | Good      | Good word choices; task mostly complete          |
| 60–74       | Fair      | Basic vocabulary; task partially done            |
| 40–59       | Poor      | Limited vocabulary; task incomplete              |
| 0–39        | Very Poor | Insufficient vocabulary; task not attempted      |

## Overall Score

```
overall = (pronunciation * 0.35) + (fluency * 0.20) + (grammar * 0.25) + (vocabulary * 0.20)
```

Pronunciation carries the highest weight because spoken intelligibility is the primary goal of scene-based practice.

## Feedback Format

Feedback is delivered in three tiers:

1. **At-a-glance** — overall score + four dimension scores (shown as bars/charts).
2. **Specific** — phoneme-level pronunciation notes, grammar corrections with explanations.
3. **Actionable** — "Try saying X instead of Y" suggestions, linked to the model answer.

## Difficulty Calibration

Scores are calibrated per difficulty level:

- **A1/A2**: Lenient scoring. Focus on being understood, not perfection.
- **B1/B2**: Balanced scoring. Expect correct grammar and decent pronunciation.
- **C1/C2**: Strict scoring. Near-native performance expected.
