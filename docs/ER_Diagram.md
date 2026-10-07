# ER Diagram

```text
DIAGNOSES 1 ───────< PATIENTS
PATIENTS 1 ────────< SAMPLES
SAMPLES 1 ─────────< SEQUENCING_RUNS
GENES 1 ───────────< VARIANTS
SAMPLES >────────< VARIANTS
                    via SAMPLE_VARIANTS
VARIANTS 1 ────────< CLINICAL_ANNOTATIONS
```

`sample_variants` resolves the many-to-many relationship between samples and variants using the composite primary key `(sample_id, variant_id)`.
