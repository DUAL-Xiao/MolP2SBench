# MolP2SBench

MolP2SBench

Usual molecular benchmarks give a complete structure and ask for a property.
MolP2SBench studies the inverse problem: a fragment of the molecule is
hidden, and the system must decide which chemically valid completion fits the
remaining graph and the supplied physical evidence.

The work is a test of property-grounded completion. A high recovery rate can
come from valence, common functional-group templates, or SMILES familiarity.
The released views ask a narrower question: when several completions are
already valid on the same scaffold, does the supplied property change the
selection in the direction the evidence implies?

## Task

The task is defined on molecular graphs and shown as SMILES. A connected
functional group is replaced by a mask token. The system receives:

- the masked SMILES and mask metadata
- a short list of completed candidate SMILES, all valid on that scaffold
- the properties listed for that directory

It returns one candidate index. The closed comparison supplies that task
text only: no tools, and no web search or literature retrieval.


| Artifact      | Path                                                        |
| ------------- | ----------------------------------------------------------- |
| Single-property prompt | `prompts/single_property_system.txt`, `prompts/single_property_user.txt` |
| Bundle prompt | `prompts/property_bundle_system.txt`, `prompts/property_bundle_user.txt` |
| All-properties prompt | `prompts/all_properties_system.txt`, `prompts/all_properties_user.txt` |
| Tasks         | `data/<property>/{correct,shuffled,counterfactual}.jsonl`   |
| Labels        | `data/<property>/{correct,shuffled,counterfactual}.labels.jsonl` |


Each task line is one JSON object with `record_id`, `masked_smiles`, `mask`,
`properties`, and `candidate_completed_smiles`. The answer is not in that
object. It is the sibling file `<condition>.labels.jsonl`. A label line has
`record_id` and `label`. `label` is the 0-based index of the target
candidate.

The returned object matches the prompt:

```json
{
  "record_id": "<input record_id>",
  "selected_candidate_index": 0,
  "reasoning": "<concise justification>"
}
```

`selected_candidate_index` is a 0-based index into
`candidate_completed_smiles`, in the order given.

Single-property directories carry one representation. A bundle carries one
family. `all_properties` carries seven properties: the dipole norm, the gap,
infrared, Raman, ultraviolet–visible, proton NMR with integration, and
carbon NMR with degeneracy.


| Directory                | Property                                                                  |
| ------------------------ | ------------------------------------------------------------------------- |
| `dipole`                 | Dipole moment, Euclidean norm                                             |
| `gap`                    | Gap between the highest occupied and lowest unoccupied molecular orbitals |
| `infrared`               | Infrared spectrum                                                         |
| `raman`                  | Raman spectrum                                                            |
| `ultraviolet_visible`    | Ultraviolet–visible excitations                                           |
| `proton_nmr_peaks`       | Proton NMR, peaks only                                                    |
| `proton_nmr_integration` | Proton NMR, peaks with integration                                        |
| `proton_nmr_atom`        | Proton NMR, atom-wise                                                     |
| `carbon_nmr_peaks`       | Carbon NMR, peaks only                                                    |
| `carbon_nmr_degeneracy`  | Carbon NMR, peaks with degeneracy                                         |
| `carbon_nmr_atom`        | Carbon NMR, atom-wise                                                     |
| `electronic`             | Dipole norm, gap, and ultraviolet–visible                                 |
| `magnetic_resonance`     | Proton NMR with integration, and carbon NMR with degeneracy               |
| `vibrational`            | Infrared and Raman spectra                                                |
| `all_properties`         | The seven properties listed above                                         |


Correct and shuffled files have 136 records each. Counterfactual files have
240 records for dipole, infrared, Raman, ultraviolet–visible, `electronic`,
`vibrational`, and `all_properties`. They have 258 records for the gap, each
NMR representation, and `magnetic_resonance`.

## Views

Exact match on the correct-property view is not evidence that the property
was used. The same scaffolds are released under three views:


| View                    | File                   | What is supplied                                              | What it tests                                   |
| ----------------------- | ---------------------- | ------------------------------------------------------------- | ----------------------------------------------- |
| Correct property        | `correct.jsonl`        | The property of the source molecule                           | Recovery under the matched property             |
| Shuffled property       | `shuffled.jsonl`       | The same property type, taken from a different molecule       | Whether the value is read or ignored            |
| Counterfactual property | `counterfactual.jsonl` | The property of another valid completion on the same scaffold | Whether the choice moves toward that completion |


Correct and shuffled views of a property share `record_id` and the candidate
list. The shuffled file changes the property, not the answer index. A
structure-only comparison uses that same masked graph and candidate list
with the property omitted. The prompt states that case: if no property is
supplied, use only the structural context.

A use claim needs a shuffle drop and a donor-directed counterfactual flip,
scoped to one model and one property.

## Environment

Loading and scoring use Python 3.9 or newer and the standard library.

```bash
python3 scripts/build_tasks.py
python3 scripts/score_tasks.py \
  --property dipole \
  --condition correct \
  --predictions predictions.jsonl
```

`scripts/build_tasks.py` loads every task file and prints the record counts.
`scripts/score_tasks.py` compares one prediction file with the label file
for that property and view. `--property` is a directory name from the table
above. `--condition` is `correct`, `shuffled`, or `counterfactual`.

## Trajectory

Score one property and one view at a time. The prediction file is JSONL,
one object per line:


| Field                      | Contents                                                                |
| -------------------------- | ----------------------------------------------------------------------- |
| `record_id`                | Task id                                                                 |
| `selected_candidate_index` | 0-based index into `candidate_completed_smiles`                         |
| `reasoning`                | Justification. The scorer does not read this field.                     |
| `invalid`                  | `true` when the submission does not parse. Omit the index on that line. |


A missing record, a line marked invalid, or an index outside the candidate
list counts as incorrect. A duplicate `record_id` is rejected. The scorer
prints the hit count, the number of tasks, the accuracy, and the counts of
missing, invalid, and out-of-range lines.