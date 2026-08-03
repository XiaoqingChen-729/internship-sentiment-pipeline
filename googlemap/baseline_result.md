# Baseline Analysis — Google Play Sentiment Pipeline

## Overview

A lightweight baseline sentiment classification model was trained on top
of the feature engineering layer to evaluate whether the current features
provide useful signal for downstream sentiment analysis.

**Script:** `baseline_analysis.py`
**Model:** Logistic Regression (class_weight='balanced', max_iter=3000)
**Target:** 3-class sentiment classification (positive / neutral / negative)
**Dataset:** 20,731 reviews across 20 apps and 16 categories

---

## Prediction Target Definition

Star ratings were grouped into three sentiment classes:

| Class | Rating | Count | Percentage |
|-------|--------|-------|------------|
| positive | 4-5 stars | 13,523 | 65.2% |
| negative | 1-2 stars | 6,304 | 30.4% |
| neutral | 3 stars | 904 | 4.4% |

Note: `rating_group` was excluded from model inputs to avoid label leakage.
The `score` field was used only to derive the prediction target label.

---

## Feature Inputs

The following features were used as model inputs:

| Feature | Type | Description |
|---------|------|-------------|
| review_length | INT | Character count of review text |
| has_reply | BOOLEAN | Whether developer replied |
| low_signal | BOOLEAN | Review under 20 characters |
| is_duplicate | BOOLEAN | Duplicate content flag |
| is_english | BOOLEAN | Language indicator |
| service_signal | BOOLEAN | Service-related keywords |
| login_signal | BOOLEAN | Login/account-related keywords |
| price_signal | BOOLEAN | Price/payment-related keywords |
| refund_signal | BOOLEAN | Refund/billing-related keywords |
| update_signal | BOOLEAN | Update/version-related keywords |
| positive_signal | BOOLEAN | Strongly positive keywords |
| negative_signal | BOOLEAN | Strongly negative keywords |

Excluded from inputs: `rating_group`, `review_date`, `review_weekday`,
`review_month`, `review_id`, `app_name`, `app_category`

---

## Evaluation Results

**Train/Test Split:** 80/20 (stratified)
**Train size:** 16,584 | **Test size:** 4,147

| Class | Precision | Recall | F1 |
|-------|-----------|--------|----|
| positive | 0.891 | 0.689 | 0.777 |
| negative | 0.777 | 0.469 | 0.585 |
| neutral | 0.063 | 0.453 | 0.111 |
| **Macro F1** | **0.577** | **0.537** | **0.491** |
| Accuracy | | | 0.612 |

---

## Confusion Matrix

| | pred_positive | pred_neutral | pred_negative |
|--|--------------|--------------|---------------|
| true_positive | 1,864 | 713 | 128 |
| true_neutral | 57 | 82 | 42 |
| true_negative | 172 | 497 | 592 |

---

## Feature Coefficients (positive class)

| Feature | Coefficient | Interpretation |
|---------|-------------|----------------|
| negative_signal | -1.681 | Strongest negative predictor |
| positive_signal | +1.462 | Strongest positive predictor |
| refund_signal | -0.921 | Strong negative signal |
| login_signal | -0.615 | Moderately negative signal |
| has_reply | -0.591 | Reviews with replies tend to be negative |
| update_signal | -0.572 | Update mentions tend to be negative |
| low_signal | +0.451 | Short reviews tend to be positive |
| is_duplicate | +0.401 | Duplicate reviews tend to be positive |
| service_signal | +0.390 | Service mentions slightly positive |
| price_signal | -0.173 | Price mentions slightly negative |
| is_english | -0.173 | Minor negative predictor |
| review_length | -0.005 | Minimal effect |

---

## Error Analysis

**Total errors:** 1,609 (38.8%)

| True Label | Error Count |
|-----------|-------------|
| positive | 841 |
| negative | 669 |
| neutral | 99 |

**Sample errors (true=negative, predicted=positive):**

All sample errors share the same pattern — no keyword signals present
and very short content:

| Score | Content | pos_signal | neg_signal |
|-------|---------|------------|------------|
| 1 | "Ok" | False | False |
| 1 | "not user friendly" | False | False |
| 2 | "Naked king" | False | False |

This confirms that when no keyword signals are present, the model
lacks sufficient information to correctly classify the review.

---

## Key Findings

**1. Macro F1 = 0.491**
The model performs at a moderate level overall. Performance varies
significantly across classes, with positive performing well (F1=0.777)
and neutral performing very poorly (F1=0.111).

**2. Sentiment signals are the most informative features**
positive_signal and negative_signal have the highest absolute coefficients,
confirming that keyword-based sentiment proxies are the most useful
features in the current set.

**3. Topic signals show meaningful correlation with negative ratings**
refund_signal (-0.921) and login_signal (-0.615) have strong negative
coefficients, consistent with earlier findings that these topics correlate
heavily with 1-star ratings. However, these signals are inherently neutral
in direction and should not be treated as direct sentiment indicators.

**4. Neutral class is the primary weakness**
With only 4.4% of the data, the neutral class is severely underrepresented.
The confusion matrix shows 713 positive reviews misclassified as neutral,
suggesting the model struggles to distinguish between positive and neutral.

**5. Short reviews without keyword signals are the main failure case**
Most prediction errors occur on reviews with no keyword signals present,
leaving the model with only structural features for those cases.

---

## Identified Limitations

**1. Feature direction**
Topic signals such as login_signal and service_signal are inherently
neutral and do not carry clear sentiment direction. Their presence adds
noise rather than useful signal to the model.

**2. Label quality**
Star ratings do not always reflect the sentiment of the review text.
A 3-star review may contain clearly positive or negative language,
making rating-derived labels an imperfect proxy for sentiment.

**3. Neutral class ambiguity**
It is unclear whether 3-star reviews should be treated as neutral or
discarded. This ambiguity increases prediction difficulty and contributes
to the very low neutral F1 of 0.111.

**4. Boolean feature limitation**
All keyword signals are binary, which loses information about how many
signals appear in a review. A review with three negative keywords is
treated the same as one with a single mention.

**5. Negation handling**
Phrases like "not great" or "can't login" trigger keyword signals but
carry the opposite sentiment, leading to misclassification.

---

## Conclusions

The current feature layer provides useful but limited signal for sentiment
classification. The main bottlenecks are feature coverage, label quality,
and class imbalance.

Future improvements could focus on:
- Replacing or supplementing keyword signals with TF-IDF or text
  embeddings to cover reviews without keyword signals
- Revisiting the label definition, either by removing the neutral class
  or using a more reliable labeling approach
- Exploring negation-aware feature extraction to reduce misclassification
  from phrases like "not great" or "can't login"
