# Cross-model verification

Sycophancy and context rot are the two most expensive failure modes in long-conversation agent work. This rule is the defense against both.

## The rule

When in a single conversation for **15+ back-and-forth exchanges on a hard decision**, stop. Paste the key context into a different model (Gemini, GPT-5, or whichever second opinion is available). Compare outputs.

- If the second model **disagrees**: you've caught a spiral. Investigate which position is correct before acting.
- If the second model **agrees**: you've verified. Proceed with higher confidence.

## What counts as a "hard decision"

- Architectural choice with multiple reasonable paths.
- Synthesis output where confidence is uniformly high (suspicious).
- Debugging that's been stuck for 20+ minutes and you're starting to repeat hypotheses.
- Any decision where the cost of being wrong is irreversible or high-impact.

Does NOT include:
- Simple code edits.
- Lookups ("what does this function do").
- Quick trivial fixes.

## The second model

- **Primary second model:** _TBD — user to choose._ Suggested: Gemini 2.5 Pro (different family, different training signal), or GPT-5 when available.
- **Keep the prompt stateless.** Do not paste the entire conversation — paste just the decision, the options, the evidence. That way the second model isn't biased by your framing.
- **Adversarial prompt:** "Here is a decision I'm about to make. Give me the strongest counterargument first, then your assessment. Do not validate uncritically."

## How to apply this in practice

1. Counter exchanges in your head (or check the conversation length).
2. At ~15 exchanges on a single hard question, pause.
3. Write the decision as a short prompt. Include: (a) the question, (b) the two or three options, (c) the evidence available.
4. Paste into the second model.
5. If agreement: note in `tasks/progress.md` as "cross-verified with <model>."
6. If disagreement: investigate the disagreement. Do not simply average the two views.

## User commitment

_Fill in once the user decides._

- Second model of choice: [ ] Gemini 2.5 Pro  [ ] GPT-5  [ ] Claude Sonnet (different session, so different context)  [ ] Other: ________
- Commitment level: [ ] mandatory at 15 exchanges  [ ] advisory at 15, mandatory at 25
- Paste format: [ ] web UI  [ ] API call from a helper script  [ ] manual copy-paste
