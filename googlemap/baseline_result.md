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

## Class Distribution

The dataset is significantly imbalanced. Positive reviews account for
65.2% of the data, while neutral reviews make up only 4.4%. This
imbalance is handled by setting `class_weight='balanced'` in the model,
which assigns higher penalty to misclassifying minority classes.

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

## Model Comparison

| Model | Macro F1 | Notes |
|-------|----------|-------|
| Majority Class Baseline | 0.263 | Always predicts positive (most frequent class) |
| Logistic Regression | 0.491 | Current model with engineered features |

The Logistic Regression model achieves a Macro F1 of 0.491, which is
1.87x higher than the majority class baseline of 0.263. This confirms
that the engineered features provide meaningful signal beyond simply
predicting the most frequent class.

---

## Evaluation Results

**Train/Test Split:** 80/20 (stratified)
**Train size:** 16,584 | **Test size:** 4,147

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|----|---------|
| positive | 0.891 | 0.689 | 0.777 | 2,705 |
| negative | 0.777 | 0.469 | 0.585 | 1,261 |
| neutral | 0.063 | 0.453 | 0.111 | 181 |
| **Macro F1** | **0.577** | **0.537** | **0.491** | |
| Accuracy | | | 0.612 | 4,147 |

Note: The current evaluation uses a stratified random split within the
same collection of apps. This result is useful as an internal baseline
but should not be interpreted as evidence that the model will generalize
to completely new apps.

---

## Confusion Matrix

| | pred_positive | pred_neutral | pred_negative |
|--|--------------|--------------|---------------|
| true_positive | 1,864 | 713 | 128 |
| true_neutral | 57 | 82 | 42 |
| true_negative | 172 | 497 | 592 |

---

## Feature Coefficients (positive class)

The coefficients below indicate the strength of association between each
feature and the positive class within this model. They reflect learned
correlations in the training data and do not by themselves confirm that
a feature improves predictive performance.

| Feature | Coefficient | Interpretation |
|---------|-------------|----------------|
| negative_signal | -1.681 | Strongest association with negative class |
| positive_signal | +1.462 | Strongest association with positive class |
| refund_signal | -0.921 | Strong association with negative class |
| login_signal | -0.615 | Moderate association with negative class |
| has_reply | -0.591 | Reviews with replies tend to be negative |
| update_signal | -0.572 | Update mentions tend to be negative |
| low_signal | +0.451 | Short reviews tend to be positive |
| is_duplicate | +0.401 | Duplicate reviews tend to be positive |
| service_signal | +0.390 | Slight association with positive class |
| price_signal | -0.173 | Slight association with negative class |
| is_english | -0.173 | Minor association with negative class |
| review_length | -0.005 | Minimal effect |

---

## Error Analysis

**Total errors:** 1,609 (38.8%)

| True Label | Error Count |
|-----------|-------------|
| positive | 841 |
| negative | 669 |
| neutral | 99 |

**Errors with no keyword signals: 1,537 out of 1,609 (95.5%)**

95.5% of prediction errors occur on reviews where neither
`positive_signal` nor `negative_signal` is present. This indicates
that the model has very limited information for reviews without keyword
signals and relies primarily on structural features in those cases.

**Sample errors (true=negative, predicted=positive):**

| Score | Content | pos_signal | neg_signal |
|-------|---------|------------|------------|
| 1 | "Ok" | False | False |
| 1 | "not user friendly" | False | False |
| 2 | "Naked king" | False | False |

All sampled errors share the same pattern: no keyword signals present
and very short content, confirming that keyword coverage is the primary
bottleneck for the current feature set.

---

## Key Findings

**1. Features provide meaningful signal above baseline**
The Logistic Regression model achieves Macro F1 of 0.491 compared to
the majority class baseline of 0.263, confirming that the engineered
features carry useful information beyond the class distribution alone.

**2. Sentiment signals have the strongest associations**
`positive_signal` and `negative_signal` have the highest absolute
coefficients, suggesting they are the most informative features in
the current set. However, this reflects association within the model
and should not be taken as confirmation of causal impact without
a controlled ablation experiment.

**3. Topic signals show correlation with negative ratings**
`refund_signal` (-0.921) and `login_signal` (-0.615) show strong
negative associations, consistent with earlier findings that these
topics correlate with 1-star ratings. However, these signals are
inherently neutral in direction. It is hypothesized that topic signals
such as `login_signal` and `service_signal` may add noise rather than
useful sentiment signal, since their presence does not indicate whether
the user experience was positive or negative. This hypothesis has not
been confirmed by a controlled feature ablation experiment.

**4. Neutral class is the primary weakness**
With only 4.4% of the data and an F1 of 0.111, the neutral class
is not reliably classifiable with the current setup. The confusion
matrix shows 713 positive reviews misclassified as neutral, suggesting
the boundary between positive and neutral is not well-defined in the
current feature space.

**5. Keyword coverage is the main failure mode**
95.5% of prediction errors occur on reviews with no keyword signals.
This is the core limitation of the current feature approach.

---

## Identified Limitations

**1. Feature direction**
Topic signals such as `login_signal` and `service_signal` are
inherently neutral and do not carry clear sentiment direction.

**2. Label quality**
Star ratings do not always reflect the sentiment of the review text.
A 3-star review may contain clearly positive or negative language,
making rating-derived labels an imperfect proxy for sentiment.

**3. Neutral class ambiguity**
It is unclear whether 3-star reviews represent a meaningful neutral
sentiment class. Their small proportion (4.4%) and low F1 (0.111)
suggest the current setup does not support treating them as a clean
neutral class.

**4. Boolean feature limitation**
All keyword signals are binary, losing information about how many
signals appear in a review. A review with three negative keywords
is treated identically to one with a single mention.

**5. Negation handling**
Phrases like "not great" or "can't login" trigger keyword signals
but carry the opposite sentiment, leading to misclassification.

**6. Generalization**
The evaluation is based on a random stratified split within the same
app collection. Results should not be interpreted as evidence of
generalization to new apps or domains.

---

## Conclusions and Recommended Future Work

The current feature layer provides useful but limited signal. The Logistic
Regression model outperforms the majority class baseline by a meaningful
margin, but overall performance is constrained by keyword coverage gaps,
label quality, and class imbalance.

Recommended future directions:

- **Better text features:** Replace or supplement keyword signals with
  TF-IDF or text embeddings to cover reviews without keyword signals
- **Label refinement:** Consider removing the neutral class or using
  a more reliable labeling approach beyond star ratings
- **Negation handling:** Implement negation-aware feature extraction
  to reduce misclassification from phrases like "not great"
- **Feature ablation:** Run controlled experiments removing topic signals
  to test whether they help or hurt model performance
- **Cross-app evaluation:** Evaluate on held-out apps to measure
  generalization beyond the current app collection