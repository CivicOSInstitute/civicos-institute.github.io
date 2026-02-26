# CivicOS Pre-Course Bootcamp (10 Days)
## Prep Plan for MIT 15.773: Hands-on Deep Learning

## Goal
Get a CivicOS learner from "general technical comfort" to "ready to absorb MIT 15.773 lecture notes and implement examples" in 10 days.

---

## Outcomes by Day 10
- Can read and modify Python ML/DL scripts confidently
- Understands train/val/test, overfitting, metrics, and error analysis
- Can build and train a basic Keras model end-to-end
- Understands embeddings, transformers, and LLM finetuning at a practical level
- Can map AI implementation choices to governance/accountability tradeoffs

---

## Daily Schedule (90–120 min/day)

### Day 1 — Python Refresh for ML
**Focus:** syntax + data structures + functions + files
- Topics: lists/dicts, loops, comprehensions, functions, imports, reading CSV/JSON
- Deliverable: `python_basics_exercises.py`
- Success check: parse a CSV and produce summary stats

### Day 2 — NumPy + Pandas Fundamentals
**Focus:** arrays, DataFrames, filtering, joins, groupby
- Deliverable: notebook with data cleaning + feature columns
- Success check: transform raw table into model-ready matrix

### Day 3 — Intro Statistics + Evaluation Intuition
**Focus:** mean/variance, distributions, correlation, leakage, bias in datasets
- Deliverable: 1-page note on metric selection pitfalls
- Success check: choose correct metric for 3 use-cases (classification/regression/imbalanced)

### Day 4 — Classical ML Baselines
**Focus:** logistic regression / tree baseline; train/val/test split
- Deliverable: baseline model report (accuracy, precision/recall/F1)
- Success check: explain overfitting signs and one mitigation

### Day 5 — Neural Nets Essentials
**Focus:** perceptron, hidden layers, activations, loss, gradient descent, backprop intuition
- Deliverable: simple MLP in Keras on tabular data
- Success check: explain what backprop does in plain English

### Day 6 — Keras/TensorFlow Workflow
**Focus:** model build/compile/fit/evaluate; callbacks; early stopping
- Deliverable: reusable Keras training template
- Success check: run two experiments with different hyperparameters and compare

### Day 7 — Computer Vision Basics
**Focus:** CNN intuition, kernels/filters, transfer learning
- Deliverable: transfer-learning mini-classifier
- Success check: document why transfer learning beat training from scratch (or didn’t)

### Day 8 — NLP Foundations
**Focus:** tokenization, bag-of-words, TF-IDF, embeddings
- Deliverable: text classification baseline + embedding version
- Success check: compare BoW vs embedding tradeoffs

### Day 9 — Transformers + LLM Practical Concepts
**Focus:** attention intuition, transformer blocks, prompting, finetuning vs RAG
- Deliverable: one-page architecture explainer for non-technical stakeholders
- Success check: choose between prompt-only, RAG, and finetuning for 3 scenarios

### Day 10 — CivicOS Integration Day
**Focus:** applying course concepts to government/public-interest contexts
- Deliverable: "CivicOS AI Readiness Memo" (2 pages)
  - model choice
  - governance controls
  - evaluation plan
  - risk and accountability checkpoints
- Success check: present recommendation with explicit auditability + human-oversight criteria

---

## Required Tooling
- Python 3.10+
- JupyterLab or VS Code notebooks
- `numpy`, `pandas`, `matplotlib`, `scikit-learn`, `tensorflow` (or `torch` if preferred)
- Optional GPU/Colab for faster experimentation

---

## Weekly Checkpoints
### Checkpoint A (after Day 5)
- Can train a basic NN and interpret learning curves

### Checkpoint B (after Day 10)
- Can follow MIT 15.773 lectures 1–11 without getting lost in prerequisites
- Can convert technical concepts into CivicOS policy/governance implications

---

## CivicOS Lens (Non-Negotiables)
Every mini-project should answer:
1. What public decision could this model affect?
2. How do we audit outcomes?
3. Where is human override mandatory?
4. What failure mode harms public trust most?

---

## Stretch (Optional, 5 extra days)
- Day 11–12: model monitoring + drift detection
- Day 13: fairness testing and subgroup analysis
- Day 14: inference latency/cost benchmarking
- Day 15: production playbook draft (model card + risk register)
