# Style Rule Copy Editor — Take-Home Assessment

## Overview

POLITICO's newsroom engineering team builds tools at the intersection of editorial judgment and technical systems. One of our active internal products is a style guide copy editor: a pipeline that takes paragraphs of editorial copy, retrieves relevant rules from POLITICO's style guide, and returns corrected text with citations to the rules applied.

This assessment asks you to build a simplified version of that system. You'll receive a database of style rules and a set of test paragraphs. Your job is to design and implement a pipeline that identifies which rules apply, produces corrected text, and returns structured output citing the rules used.

This is a work-sample exercise. It mirrors the kind of problem you'd actually work on in this role. We're looking at how you think about system design, how you use AI tools, and how you reason about tradeoffs where editorial accuracy is the constraint that matters most.

**A note on timeboxing:** This exercise is designed to be completed in 2–3 hours. If you haven't worked with AI-powered text pipelines before, know that chasing perfect accuracy on a problem like this can take days of iteration. That's not the goal. The goal is not to design a perfect system. You'll be evaluated based on your approach, your reasoning, and how you spend your time per the rubric below. Ship what you have when the timebox is up, and use your memo to explain what's working, what isn't, and what you'd improve.

> **Need an API key?** If your approach uses an LLM service (OpenAI, etc.), we are happy to provide an OpenAI API key — just ask. You are not required to use OpenAI or any specific service; use whatever tools make sense for your design.

---

## The Task

Build a style-rule copy editor that:

1. **Reads** `data/input.json` — a list of paragraphs with IDs.
2. **For each paragraph**, identifies which rules from the provided database are violated, applies corrections, and records which rules were used. Only apply corrections sourced from the rules in `data/DB.json` — do not apply AP Stylebook, Chicago Manual, or any other external style conventions.
3. **Writes** `data/output.json` — the corrected paragraphs with citations.

Assume the provided inputs are **body-copy paragraphs**, not headlines, captions or display text.

### Input Schema

```json
{
  "input": [
    {
      "id": "para-001",
      "text": "Input paragraph here."
    }
  ]
}
```

### Output Schema

```json
{
  "output": [
    {
      "id": "para-001",
      "edit": "Corrected paragraph here.",
      "citations": ["52a651d0-00d6-4192-86e5-72c58f828cd2"]
    }
  ]
}
```

Each output entry must:

- Have an `id` matching the corresponding input paragraph.
- Contain the corrected text in `edit`.
- List the rule IDs applied in `citations`.

### How to Run

```bash
./run.sh
```

This reads `data/input.json`, applies your pipeline, and writes the result to `data/output.json`.

---

## Deliverables

Your submission should include two things: a **codebase** (zip archive) and a **memo** (separate attachment).

### 1. Working Implementation (zip archive)

A codebase that reads `data/input.json`, runs your pipeline, and writes `data/output.json`. Wire it up through `run.sh` so we can run it with a single command. Include a README or setup instructions in the zip so we know how to install dependencies and run your code.

### 2. Evaluation Harness

Include a script or test suite that runs your system and generates an evaluation report. How you structure the evaluation is up to you — define your accuracy metric(s) and explain what the harness can and cannot tell you. Use the memo to explain your evaluation approach and results.

### 3. Business Memo (separate attachment, 1–2 pages)

Write a short memo that covers:

- **Business context.** Include at least one concrete insight about how this kind of tool would need to work differently in a newsroom vs. a generic text-correction product.
- **AI usage.** Document how you used AI tools throughout the project — what you delegated, what you accepted or rejected and why, and how you verified AI-generated output. This is not a gotcha. There is no penalty for heavy AI use. There is signal in how you direct it, what you trust, and what you check.
- **Evaluation results.** Explain how successful your codebase was at achieving accurate style edits, using whatever evaluation approach you designed.
- **Tradeoffs and next steps.** What you chose and why. What you'd do with more time.

Deliver the memo as a PDF or Markdown file.

---

## Hard Constraints

These mirror real constraints in our production system:

1. **Do not change meaning, emphasis, attribution, or factual detail.** Make the minimum edit required by the rule and nothing else.
2. **Quoted text is not automatically exempt from edits.** Whether text inside quotation marks should change depends on the supplied rule. Follow the rule text and make the minimum justified edit.
3. **Treat the paragraph as raw text.** Do not add formatting markup or introduce structural changes that are not required by the rule.
4. **Only apply rules from the provided database.** Do not invent style corrections, even if you'd make them yourself.

---

## Example Input and Output

The `data/input.json` and `data/output.json` files contain **example data only**. They demonstrate the input format your code should accept and the output format it should produce.

**These are NOT the golden dataset used to evaluate your submission.** During evaluation, we will run your pipeline against a separate set of input paragraphs with human-validated expected outputs. Your code must generalize to unseen paragraphs — not just handle the examples provided here.

You are free to add more examples to `data/input.json` and `data/output.json` for your own development and testing.

Use the examples to:

- Understand the input/output contract.
- Develop and debug your pipeline.
- Validate that your system produces well-formed output.

---

## Logistics

| Detail       | Info                                                                                                                                |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Timebox**  | 2–3 hours for the build. 30–45 minutes for the memo. If you go over, stop and document what you'd do next.                          |
| **Window**   | 5 calendar days from receipt.                                                                                                       |
| **AI Tools** | Allowed and expected. Use whatever you'd use on the job: copilots, chat assistants, agentic workflows. Document usage in your memo. |
| **Language** | TypeScript or Python preferred. Use whatever you'd reach for in a real sprint.                                                      |
| **Delivery** | Zip archive of your codebase, plus the memo as a separate attachment.                                                               |

---

## Repository Structure

```
.
├── README.md          ← You are here.
├── run.sh             ← Entry point. Edit this to call your code.
├── data/
│   ├── DB.json        ← Style rules database. DO NOT MODIFY.
│   ├── input.json     ← Example input paragraphs.
│   └── output.json    ← Example expected output (see note below).
└── src/
    └── .gitkeep       ← Your code goes here. Add whatever files you need.
```

### Notes on the files

- **`data/DB.json`** — The rules database is fixed. Do not add, remove, or modify rules. Your code does not have to read from this file directly — you may transform or index it as needed, but the source rules must remain unchanged.
- **`data/input.json`** — Example input. You may add more paragraphs for your own testing. Your code should accept any file in this format.
- **`data/output.json`** — Example output. You may add more examples or update this file to match your added inputs. This is example data, not the evaluation set.
- **`run.sh`** — Edit to invoke your pipeline.
- **`src/`** — All your code goes here. Add any files and subdirectories you need.

---

## What We Evaluate

Your submission is scored across five dimensions. The weights reflect what matters most for this role.

| Dimension                     | What we're looking for                                                                                                                                                                   | Weight |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| **Functional correctness**    | Does it find the right rules and produce correct edits? Do the gold-standard evals pass?                                                                                                 | 25%    |
| **System design**             | Clean retrieval → correction → output pipeline. Can we follow how a paragraph moves through your system and understand why a specific edit was made?                                     | 25%    |
| **AI collaboration**          | Thoughtful delegation to LLMs. Clear boundaries on what the model decides vs. what the system constrains. Did you add an `Agents.md`, prompt files, or another harness for directing AI? | 20%    |
| **Evaluation + verification** | You built something that tests your own system and you can articulate where it works, where it doesn't, and why.                                                                         | 15%    |
| **Business context**          | Memo shows you engaged with our domain. Plausible thinking about adoption, failure modes, and newsroom tradeoffs.                                                                        | 15%    |

---

## Evaluation Process

After you submit:

1. **Separate golden dataset.** We will run your pipeline (`./run.sh`) against a different set of input paragraphs with human-validated expected outputs. The goal is to measure whether the system you built generalizes to unseen input — not to trick you. If your system only works on the provided examples, that will show. If it handles new paragraphs well, that will also show.
2. **Citation accuracy.** We check that your system cites the correct rules for each edit. Precision and recall both matter.
3. **Human review of edits.** A human evaluator reviews whether your system correctly applied the rules — whether it made the right edits, avoided editing things it shouldn't have, and respected the hard constraints. **AI will not be used in this evaluation.**
