# Citation

## Paper

Prabhu Rangaraju. *No Learning Under This Protocol:
A Preregistered Validity Audit of a Downsized Frozen-Student Replication of
Sherpa's Simulator.* Manuscript
prepared for the *Journal of Educational Data Mining*. 2026.

```bibtex
@unpublished{rangaraju2026sherpa,
  author = {Rangaraju, Prabhu},
  title  = {No Learning Under This Protocol:
            A Preregistered Validity Audit of a Downsized Frozen-Student
            Replication of {Sherpa}'s Simulator},
  note   = {Manuscript prepared for the Journal of Educational Data Mining},
  year   = {2026}
}
```

## Code

The analysis code in this package (`scripts/`, `reproduce.sh`) was authored
by Prabhu Rangaraju for this paper.

## Datasets

- 300 simulated tutoring episodes (`data/trajectories.jsonl`), generated for
  this audit with the Qwen3-1.7B model under the preregistered protocol.
- ASSISTments 2009–2010 skill-builder data (Feng, Heffernan & Koedinger,
  2009), free to use for research; `data/real_pool.json` is a derived seeded
  sample of 5,000 (student, skill) sequences.
- Sherpa upstream repository (SALT-NLP/Sherpa, Apache-2.0): gate prompts and
  teaching templates replicated verbatim; paper arXiv:2610.08778.
- MATH dataset (Hendrycks et al., MIT license): the paper's shipped filtered
  test split supplied the 300 problems.
