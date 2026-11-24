# judge-agreement

**Is your LLM grader actually agreeing with humans?**

Many AI evaluations now use one model to grade another. That is fast, but a grader can look accurate while carrying almost no information, for example by saying "correct" most of the time on a dataset where most answers are correct. Raw agreement hides this. Cohen's kappa does not.

`judge-agreement` compares an automated grader's labels with a blind human-labeled sample and tells you whether the grader is safe to use.

## What it reports

- raw agreement
- Cohen's kappa with a bootstrap 95% confidence interval and its standard interpretation band
- a confusion matrix
- precision and recall per label, with human labels as ground truth
- a plain verdict: usable, or do not trust it yet

## Usage

```bash
python judge_agreement.py example_labels.csv --human human --model model
```

The CSV needs one row per item, with a human-label column and a grader-label column. Labels can be any strings. Only the Python standard library is used.

```text
items compared      100
raw agreement       78.0%
Cohen's kappa       0.530  (95% bootstrap CI 0.357 to 0.690; moderate)
...
verdict: do not trust this grader yet. The lower bound of kappa (0.357) is below 0.6.
```

78% raw agreement sounds fine. The kappa interval says the grader is not yet reliable enough to report results with.

## Options

| Flag | Default | Meaning |
|---|---|---|
| `--human` | `human` | column with human labels |
| `--model` | `model` | column with grader labels |
| `--boot` | `2000` | bootstrap resamples |
| `--seed` | `0` | random seed, for reproducible intervals |
| `--threshold` | `0.6` | lowest acceptable lower bound for kappa |

## Tests

```bash
python -m unittest test_judge_agreement
```

`example_labels.csv` is synthetic data generated for this demo.

## Why this exists

In my own research, a check like this caught an LLM grader that agreed with human labels at chance level, before any result was reported. Validating the grader is now the first step of every evaluation I run.
