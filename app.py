import os
from flask import Flask, render_template, request, redirect, url_for, flash
from database.db_connection import get_db_connection

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "clinical-genomics-dev-key")


def fetch_all(query, params=()):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


def fetch_one(query, params=()):
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute_query(query, params=()):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(query, params)
        db.commit()
    finally:
        cursor.close()
        db.close()


@app.context_processor
def inject_navigation_counts():
    try:
        counts = {
            "patients": fetch_one(
                "SELECT COUNT(*) AS count FROM patients"
            )["count"],
            "samples": fetch_one(
                "SELECT COUNT(*) AS count FROM samples"
            )["count"],
            "runs": fetch_one(
                "SELECT COUNT(*) AS count FROM sequencing_runs"
            )["count"],
            "genes": fetch_one(
                "SELECT COUNT(*) AS count FROM genes"
            )["count"],
            "variants": fetch_one(
                "SELECT COUNT(*) AS count FROM variants"
            )["count"]
        }
    except Exception:
        counts = {
            "patients": 0,
            "samples": 0,
            "runs": 0,
            "genes": 0,
            "variants": 0
        }

    return {"nav_counts": counts}


@app.route("/")
def home():
    counts = {
        "patients": fetch_one(
            "SELECT COUNT(*) AS count FROM patients"
        )["count"],
        "samples": fetch_one(
            "SELECT COUNT(*) AS count FROM samples"
        )["count"],
        "runs": fetch_one(
            "SELECT COUNT(*) AS count FROM sequencing_runs"
        )["count"],
        "genes": fetch_one(
            "SELECT COUNT(*) AS count FROM genes"
        )["count"],
        "variants": fetch_one(
            "SELECT COUNT(*) AS count FROM variants"
        )["count"],
        "pathogenic": fetch_one(
            "SELECT COUNT(*) AS count FROM variants "
            "WHERE clinical_significance = 'Pathogenic'"
        )["count"],
        "qc_passed": fetch_one(
            "SELECT COUNT(*) AS count FROM sequencing_runs "
            "WHERE qc_status = 'Passed'"
        )["count"]
    }

    return render_template("index.html", counts=counts)


@app.route("/diagnoses", methods=["GET", "POST"])
def diagnoses():
    if request.method == "POST":
        try:
            diagnosis_id = request.form["diagnosis_id"]
            disease_name = request.form["disease_name"]
            disease_category = request.form["disease_category"]

            execute_query(
                """
                INSERT INTO diagnoses
                (diagnosis_id, disease_name, disease_category)
                VALUES (%s, %s, %s)
                """,
                (
                    diagnosis_id,
                    disease_name,
                    disease_category
                )
            )

            flash(
                "Diagnosis added successfully.",
                "success"
            )

        except Exception as error:
            if "Duplicate entry" in str(error):
                flash(
                    "Diagnosis ID already exists. Please enter a unique ID.",
                    "error"
                )
            else:
                flash(
                    f"Could not add diagnosis: {error}",
                    "error"
                )

        return redirect(url_for("diagnoses"))

    rows = fetch_all(
        "SELECT * FROM diagnoses "
        "ORDER BY diagnosis_id ASC"
    )

    return render_template(
        "diagnoses.html",
        diagnoses=rows
    )


@app.route(
    "/diagnoses/edit/<int:diagnosis_id>",
    methods=["GET", "POST"]
)
def edit_diagnosis(diagnosis_id):
    if request.method == "POST":
        try:
            execute_query(
                """
                UPDATE diagnoses
                SET disease_name=%s,
                    disease_category=%s
                WHERE diagnosis_id=%s
                """,
                (
                    request.form["disease_name"],
                    request.form["disease_category"],
                    diagnosis_id
                )
            )

            flash(
                "Diagnosis updated successfully.",
                "success"
            )

            return redirect(url_for("diagnoses"))

        except Exception as error:
            flash(
                f"Could not update diagnosis: {error}",
                "error"
            )

    diagnosis = fetch_one(
        "SELECT * FROM diagnoses WHERE diagnosis_id=%s",
        (diagnosis_id,)
    )

    if not diagnosis:
        flash(
            "Diagnosis not found.",
            "error"
        )

        return redirect(url_for("diagnoses"))

    return render_template(
        "diagnosis_edit.html",
        diagnosis=diagnosis
    )


@app.route(
    "/diagnoses/delete/<int:diagnosis_id>",
    methods=["POST"]
)
def delete_diagnosis(diagnosis_id):
    try:
        execute_query(
            "DELETE FROM diagnoses WHERE diagnosis_id=%s",
            (diagnosis_id,)
        )

        flash(
            "Diagnosis deleted successfully.",
            "success"
        )

    except Exception as error:
        flash(
            f"Could not delete diagnosis: {error}",
            "error"
        )

    return redirect(url_for("diagnoses"))


@app.route("/patients", methods=["GET", "POST"])
def patients():
    if request.method == "POST":
        try:
            execute_query(
                """
                INSERT INTO patients
                (
                    patient_code,
                    age,
                    sex,
                    diagnosis_id,
                    registration_date
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    request.form["patient_code"],
                    request.form["age"],
                    request.form["sex"],
                    request.form["diagnosis_id"],
                    request.form["registration_date"]
                )
            )

            flash(
                "Patient added successfully.",
                "success"
            )

        except Exception as error:
            flash(
                f"Could not add patient: {error}",
                "error"
            )

        return redirect(url_for("patients"))

    search = request.args.get(
        "q",
        ""
    ).strip()

    diagnoses_list = fetch_all(
        "SELECT diagnosis_id, disease_name "
        "FROM diagnoses "
        "ORDER BY disease_name"
    )

    if search:
        rows = fetch_all(
            """
            SELECT
                p.patient_id,
                p.patient_code,
                p.age,
                p.sex,
                d.disease_name,
                p.registration_date
            FROM patients p
            JOIN diagnoses d
                ON p.diagnosis_id = d.diagnosis_id
            WHERE p.patient_code LIKE %s
               OR d.disease_name LIKE %s
            ORDER BY p.patient_id
            """,
            (
                f"%{search}%",
                f"%{search}%"
            )
        )

    else:
        rows = fetch_all(
            """
            SELECT
                p.patient_id,
                p.patient_code,
                p.age,
                p.sex,
                d.disease_name,
                p.registration_date
            FROM patients p
            JOIN diagnoses d
                ON p.diagnosis_id = d.diagnosis_id
            ORDER BY p.patient_id
            """
        )

    return render_template(
        "patients.html",
        diagnoses=diagnoses_list,
        patients=rows,
        search=search
    )


@app.route(
    "/patients/edit/<int:patient_id>",
    methods=["GET", "POST"]
)
def edit_patient(patient_id):
    if request.method == "POST":
        try:
            execute_query(
                """
                UPDATE patients
                SET
                    patient_code=%s,
                    age=%s,
                    sex=%s,
                    diagnosis_id=%s,
                    registration_date=%s
                WHERE patient_id=%s
                """,
                (
                    request.form["patient_code"],
                    request.form["age"],
                    request.form["sex"],
                    request.form["diagnosis_id"],
                    request.form["registration_date"],
                    patient_id
                )
            )

            flash(
                "Patient updated successfully.",
                "success"
            )

            return redirect(url_for("patients"))

        except Exception as error:
            flash(
                f"Could not update patient: {error}",
                "error"
            )

    patient = fetch_one(
        """
        SELECT
            patient_id,
            patient_code,
            age,
            sex,
            diagnosis_id,
            registration_date
        FROM patients
        WHERE patient_id=%s
        """,
        (patient_id,)
    )

    diagnoses_list = fetch_all(
        "SELECT diagnosis_id, disease_name "
        "FROM diagnoses "
        "ORDER BY disease_name"
    )

    if not patient:
        flash(
            "Patient not found.",
            "error"
        )

        return redirect(url_for("patients"))

    return render_template(
        "patient_edit.html",
        patient=patient,
        diagnoses=diagnoses_list
    )


@app.route(
    "/patients/delete/<int:patient_id>",
    methods=["POST"]
)
def delete_patient(patient_id):
    try:
        execute_query(
            "DELETE FROM patients WHERE patient_id=%s",
            (patient_id,)
        )

        flash(
            "Patient deleted successfully.",
            "success"
        )

    except Exception as error:
        flash(
            f"Could not delete patient: {error}",
            "error"
        )

    return redirect(url_for("patients"))


@app.route("/samples", methods=["GET", "POST"])
def samples():
    if request.method == "POST":
        try:
            execute_query(
                """
                INSERT INTO samples
                (
                    patient_id,
                    sample_type,
                    collection_date,
                    sequencing_status
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    request.form["patient_id"],
                    request.form["sample_type"],
                    request.form["collection_date"],
                    request.form["sequencing_status"]
                )
            )

            flash(
                "Sample added successfully.",
                "success"
            )

        except Exception as error:
            flash(
                f"Could not add sample: {error}",
                "error"
            )

        return redirect(url_for("samples"))

    patients_list = fetch_all(
        "SELECT patient_id, patient_code "
        "FROM patients "
        "ORDER BY patient_code"
    )

    rows = fetch_all(
        """
        SELECT
            s.sample_id,
            p.patient_code,
            s.sample_type,
            s.collection_date,
            s.sequencing_status
        FROM samples s
        JOIN patients p
            ON s.patient_id=p.patient_id
        ORDER BY s.sample_id
        """
    )

    return render_template(
        "samples.html",
        samples=rows,
        patients=patients_list
    )


@app.route(
    "/samples/edit/<int:sample_id>",
    methods=["GET", "POST"]
)
def edit_sample(sample_id):
    if request.method == "POST":
        try:
            execute_query(
                """
                UPDATE samples
                SET
                    patient_id=%s,
                    sample_type=%s,
                    collection_date=%s,
                    sequencing_status=%s
                WHERE sample_id=%s
                """,
                (
                    request.form["patient_id"],
                    request.form["sample_type"],
                    request.form["collection_date"],
                    request.form["sequencing_status"],
                    sample_id
                )
            )

            flash(
                "Sample updated successfully.",
                "success"
            )

            return redirect(url_for("samples"))

        except Exception as error:
            flash(
                f"Could not update sample: {error}",
                "error"
            )

    sample = fetch_one(
        "SELECT * FROM samples WHERE sample_id=%s",
        (sample_id,)
    )

    patients_list = fetch_all(
        "SELECT patient_id, patient_code "
        "FROM patients "
        "ORDER BY patient_code"
    )

    if not sample:
        flash(
            "Sample not found.",
            "error"
        )

        return redirect(url_for("samples"))

    return render_template(
        "sample_edit.html",
        sample=sample,
        patients=patients_list
    )


@app.route(
    "/samples/delete/<int:sample_id>",
    methods=["POST"]
)
def delete_sample(sample_id):
    try:
        execute_query(
            "DELETE FROM samples WHERE sample_id=%s",
            (sample_id,)
        )

        flash(
            "Sample deleted successfully.",
            "success"
        )

    except Exception as error:
        flash(
            f"Could not delete sample: {error}",
            "error"
        )

    return redirect(url_for("samples"))


@app.route(
    "/sequencing-runs",
    methods=["GET", "POST"]
)
def sequencing_runs():
    if request.method == "POST":
        try:
            execute_query(
                """
                INSERT INTO sequencing_runs
                (
                    sample_id,
                    platform,
                    run_date,
                    read_count,
                    qc_status
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    request.form["sample_id"],
                    request.form["platform"],
                    request.form["run_date"],
                    request.form["read_count"],
                    request.form["qc_status"]
                )
            )

            flash(
                "Sequencing run added successfully.",
                "success"
            )

        except Exception as error:
            flash(
                f"Could not add sequencing run: {error}",
                "error"
            )

        return redirect(url_for("sequencing_runs"))

    samples_list = fetch_all(
        """
        SELECT
            s.sample_id,
            p.patient_code
        FROM samples s
        JOIN patients p
            ON s.patient_id=p.patient_id
        ORDER BY s.sample_id
        """
    )

    rows = fetch_all(
        """
        SELECT
            r.run_id,
            r.sample_id,
            p.patient_code,
            r.platform,
            r.run_date,
            r.read_count,
            r.qc_status
        FROM sequencing_runs r
        JOIN samples s
            ON r.sample_id=s.sample_id
        JOIN patients p
            ON s.patient_id=p.patient_id
        ORDER BY r.run_id
        """
    )

    return render_template(
        "sequencing_runs.html",
        runs=rows,
        samples=samples_list
    )


@app.route(
    "/sequencing-runs/edit/<int:run_id>",
    methods=["GET", "POST"]
)
def edit_sequencing_run(run_id):
    if request.method == "POST":
        try:
            execute_query(
                """
                UPDATE sequencing_runs
                SET
                    sample_id=%s,
                    platform=%s,
                    run_date=%s,
                    read_count=%s,
                    qc_status=%s
                WHERE run_id=%s
                """,
                (
                    request.form["sample_id"],
                    request.form["platform"],
                    request.form["run_date"],
                    request.form["read_count"],
                    request.form["qc_status"],
                    run_id
                )
            )

            flash(
                "Sequencing run updated successfully.",
                "success"
            )

            return redirect(
                url_for("sequencing_runs")
            )

        except Exception as error:
            flash(
                f"Could not update sequencing run: {error}",
                "error"
            )

    run = fetch_one(
        "SELECT * FROM sequencing_runs WHERE run_id=%s",
        (run_id,)
    )

    samples_list = fetch_all(
        """
        SELECT
            s.sample_id,
            p.patient_code
        FROM samples s
        JOIN patients p
            ON s.patient_id=p.patient_id
        ORDER BY s.sample_id
        """
    )

    if not run:
        flash(
            "Sequencing run not found.",
            "error"
        )

        return redirect(
            url_for("sequencing_runs")
        )

    return render_template(
        "sequencing_run_edit.html",
        run=run,
        samples=samples_list
    )


@app.route(
    "/sequencing-runs/delete/<int:run_id>",
    methods=["POST"]
)
def delete_sequencing_run(run_id):
    try:
        execute_query(
            "DELETE FROM sequencing_runs WHERE run_id=%s",
            (run_id,)
        )

        flash(
            "Sequencing run deleted successfully.",
            "success"
        )

    except Exception as error:
        flash(
            f"Could not delete sequencing run: {error}",
            "error"
        )

    return redirect(
        url_for("sequencing_runs")
    )


@app.route("/genes", methods=["GET", "POST"])
def genes():
    if request.method == "POST":
        try:
            execute_query(
                """
                INSERT INTO genes
                (
                    gene_symbol,
                    gene_name,
                    chromosome
                )
                VALUES (%s, %s, %s)
                """,
                (
                    request.form["gene_symbol"],
                    request.form["gene_name"],
                    request.form["chromosome"]
                )
            )

            flash(
                "Gene added successfully.",
                "success"
            )

        except Exception as error:
            flash(
                f"Could not add gene: {error}",
                "error"
            )

        return redirect(url_for("genes"))

    rows = fetch_all(
        "SELECT * FROM genes ORDER BY gene_symbol"
    )

    return render_template(
        "genes.html",
        genes=rows
    )


@app.route(
    "/genes/edit/<int:gene_id>",
    methods=["GET", "POST"]
)
def edit_gene(gene_id):
    if request.method == "POST":
        try:
            execute_query(
                """
                UPDATE genes
                SET
                    gene_symbol=%s,
                    gene_name=%s,
                    chromosome=%s
                WHERE gene_id=%s
                """,
                (
                    request.form["gene_symbol"],
                    request.form["gene_name"],
                    request.form["chromosome"],
                    gene_id
                )
            )

            flash(
                "Gene updated successfully.",
                "success"
            )

            return redirect(
                url_for("genes")
            )

        except Exception as error:
            flash(
                f"Could not update gene: {error}",
                "error"
            )

    gene = fetch_one(
        "SELECT * FROM genes WHERE gene_id=%s",
        (gene_id,)
    )

    if not gene:
        flash(
            "Gene not found.",
            "error"
        )

        return redirect(
            url_for("genes")
        )

    return render_template(
        "gene_edit.html",
        gene=gene
    )


@app.route(
    "/genes/delete/<int:gene_id>",
    methods=["POST"]
)
def delete_gene(gene_id):
    try:
        execute_query(
            "DELETE FROM genes WHERE gene_id=%s",
            (gene_id,)
        )

        flash(
            "Gene deleted successfully.",
            "success"
        )

    except Exception as error:
        flash(
            f"Could not delete gene: {error}",
            "error"
        )

    return redirect(
        url_for("genes")
    )


@app.route("/variants", methods=["GET", "POST"])
def variants():
    if request.method == "POST":
        try:
            execute_query(
                """
                INSERT INTO variants
                (
                    gene_id,
                    chromosome,
                    position,
                    reference_allele,
                    alternate_allele,
                    variant_type,
                    clinical_significance
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    request.form["gene_id"],
                    request.form["chromosome"],
                    request.form["position"],
                    request.form["reference_allele"],
                    request.form["alternate_allele"],
                    request.form["variant_type"],
                    request.form["clinical_significance"]
                )
            )

            flash(
                "Variant added successfully.",
                "success"
            )

        except Exception as error:
            flash(
                f"Could not add variant: {error}",
                "error"
            )

        return redirect(
            url_for("variants")
        )

    genes_list = fetch_all(
        "SELECT gene_id, gene_symbol "
        "FROM genes "
        "ORDER BY gene_symbol"
    )

    rows = fetch_all(
        """
        SELECT
            v.*,
            g.gene_symbol
        FROM variants v
        LEFT JOIN genes g
            ON v.gene_id=g.gene_id
        ORDER BY v.variant_id
        """
    )

    return render_template(
        "variants.html",
        variants=rows,
        genes=genes_list
    )


@app.route(
    "/variants/edit/<int:variant_id>",
    methods=["GET", "POST"]
)
def edit_variant(variant_id):
    if request.method == "POST":
        try:
            execute_query(
                """
                UPDATE variants
                SET
                    gene_id=%s,
                    chromosome=%s,
                    position=%s,
                    reference_allele=%s,
                    alternate_allele=%s,
                    variant_type=%s,
                    clinical_significance=%s
                WHERE variant_id=%s
                """,
                (
                    request.form["gene_id"],
                    request.form["chromosome"],
                    request.form["position"],
                    request.form["reference_allele"],
                    request.form["alternate_allele"],
                    request.form["variant_type"],
                    request.form["clinical_significance"],
                    variant_id
                )
            )

            flash(
                "Variant updated successfully.",
                "success"
            )

            return redirect(
                url_for("variants")
            )

        except Exception as error:
            flash(
                f"Could not update variant: {error}",
                "error"
            )

    variant = fetch_one(
        "SELECT * FROM variants WHERE variant_id=%s",
        (variant_id,)
    )

    genes_list = fetch_all(
        "SELECT gene_id, gene_symbol "
        "FROM genes "
        "ORDER BY gene_symbol"
    )

    if not variant:
        flash(
            "Variant not found.",
            "error"
        )

        return redirect(
            url_for("variants")
        )

    return render_template(
        "variant_edit.html",
        variant=variant,
        genes=genes_list
    )


@app.route(
    "/variants/delete/<int:variant_id>",
    methods=["POST"]
)
def delete_variant(variant_id):
    try:
        execute_query(
            "DELETE FROM variants WHERE variant_id=%s",
            (variant_id,)
        )

        flash(
            "Variant deleted successfully.",
            "success"
        )

    except Exception as error:
        flash(
            f"Could not delete variant: {error}",
            "error"
        )

    return redirect(
        url_for("variants")
    )


@app.route(
    "/sample-variants",
    methods=["GET", "POST"]
)
def sample_variants():
    if request.method == "POST":
        try:
            execute_query(
                """
                INSERT INTO sample_variants
                (
                    sample_id,
                    variant_id,
                    allele_frequency,
                    depth,
                    zygosity
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    request.form["sample_id"],
                    request.form["variant_id"],
                    request.form["allele_frequency"],
                    request.form["depth"],
                    request.form["zygosity"]
                )
            )

            flash(
                "Sample-variant link added successfully.",
                "success"
            )

        except Exception as error:
            flash(
                f"Could not add sample-variant link: {error}",
                "error"
            )

        return redirect(
            url_for("sample_variants")
        )

    samples_list = fetch_all(
        "SELECT sample_id "
        "FROM samples "
        "ORDER BY sample_id"
    )

    variants_list = fetch_all(
        "SELECT variant_id, chromosome, position "
        "FROM variants "
        "ORDER BY variant_id"
    )

    rows = fetch_all(
        """
        SELECT
            sv.sample_id,
            sv.variant_id,
            sv.allele_frequency,
            sv.depth,
            sv.zygosity,
            p.patient_code,
            v.chromosome,
            v.position
        FROM sample_variants sv
        JOIN samples s
            ON sv.sample_id=s.sample_id
        JOIN patients p
            ON s.patient_id=p.patient_id
        JOIN variants v
            ON sv.variant_id=v.variant_id
        ORDER BY
            sv.sample_id,
            sv.variant_id
        """
    )

    return render_template(
        "sample_variants.html",
        sample_variants=rows,
        samples=samples_list,
        variants=variants_list
    )


@app.route(
    "/sample-variants/edit/<int:sample_id>/<int:variant_id>",
    methods=["GET", "POST"]
)
def edit_sample_variant(sample_id, variant_id):
    if request.method == "POST":
        try:
            execute_query(
                """
                UPDATE sample_variants
                SET
                    allele_frequency=%s,
                    depth=%s,
                    zygosity=%s
                WHERE sample_id=%s
                  AND variant_id=%s
                """,
                (
                    request.form["allele_frequency"],
                    request.form["depth"],
                    request.form["zygosity"],
                    sample_id,
                    variant_id
                )
            )

            flash(
                "Sample-variant link updated successfully.",
                "success"
            )

            return redirect(
                url_for("sample_variants")
            )

        except Exception as error:
            flash(
                f"Could not update sample-variant link: {error}",
                "error"
            )

    row = fetch_one(
        """
        SELECT *
        FROM sample_variants
        WHERE sample_id=%s
          AND variant_id=%s
        """,
        (
            sample_id,
            variant_id
        )
    )

    if not row:
        flash(
            "Sample-variant link not found.",
            "error"
        )

        return redirect(
            url_for("sample_variants")
        )

    return render_template(
        "sample_variant_edit.html",
        sample_variant=row
    )


@app.route(
    "/sample-variants/delete/<int:sample_id>/<int:variant_id>",
    methods=["POST"]
)
def delete_sample_variant(sample_id, variant_id):
    try:
        execute_query(
            """
            DELETE FROM sample_variants
            WHERE sample_id=%s
              AND variant_id=%s
            """,
            (
                sample_id,
                variant_id
            )
        )

        flash(
            "Sample-variant link deleted successfully.",
            "success"
        )

    except Exception as error:
        flash(
            f"Could not delete sample-variant link: {error}",
            "error"
        )

    return redirect(
        url_for("sample_variants")
    )


@app.route(
    "/clinical-annotations",
    methods=["GET", "POST"]
)
def clinical_annotations():
    if request.method == "POST":
        try:
            execute_query(
                """
                INSERT INTO clinical_annotations
                (
                    variant_id,
                    evidence_level,
                    `condition`,
                    source_database,
                    interpretation_date
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    request.form["variant_id"],
                    request.form["evidence_level"],
                    request.form["condition"],
                    request.form["source_database"],
                    request.form["interpretation_date"]
                )
            )

            flash(
                "Clinical annotation added successfully.",
                "success"
            )

        except Exception as error:
            flash(
                f"Could not add annotation: {error}",
                "error"
            )

        return redirect(
            url_for("clinical_annotations")
        )

    variants_list = fetch_all(
        "SELECT variant_id, chromosome, position "
        "FROM variants "
        "ORDER BY variant_id"
    )

    rows = fetch_all(
        """
        SELECT
            ca.annotation_id,
            ca.variant_id,
            ca.evidence_level,
            ca.`condition`,
            ca.source_database,
            ca.interpretation_date,
            v.chromosome,
            v.position,
            g.gene_symbol
        FROM clinical_annotations ca
        JOIN variants v
            ON ca.variant_id=v.variant_id
        LEFT JOIN genes g
            ON v.gene_id=g.gene_id
        ORDER BY ca.annotation_id
        """
    )

    return render_template(
        "clinical_annotations.html",
        annotations=rows,
        variants=variants_list
    )


@app.route(
    "/clinical-annotations/edit/<int:annotation_id>",
    methods=["GET", "POST"]
)
def edit_clinical_annotation(annotation_id):
    if request.method == "POST":
        try:
            execute_query(
                """
                UPDATE clinical_annotations
                SET
                    variant_id=%s,
                    evidence_level=%s,
                    `condition`=%s,
                    source_database=%s,
                    interpretation_date=%s
                WHERE annotation_id=%s
                """,
                (
                    request.form["variant_id"],
                    request.form["evidence_level"],
                    request.form["condition"],
                    request.form["source_database"],
                    request.form["interpretation_date"],
                    annotation_id
                )
            )

            flash(
                "Clinical annotation updated successfully.",
                "success"
            )

            return redirect(
                url_for("clinical_annotations")
            )

        except Exception as error:
            flash(
                f"Could not update annotation: {error}",
                "error"
            )

    annotation = fetch_one(
        """
        SELECT
            annotation_id,
            variant_id,
            evidence_level,
            `condition`,
            source_database,
            interpretation_date
        FROM clinical_annotations
        WHERE annotation_id=%s
        """,
        (annotation_id,)
    )

    variants_list = fetch_all(
        "SELECT variant_id, chromosome, position "
        "FROM variants "
        "ORDER BY variant_id"
    )

    if not annotation:
        flash(
            "Annotation not found.",
            "error"
        )

        return redirect(
            url_for("clinical_annotations")
        )

    return render_template(
        "clinical_annotation_edit.html",
        annotation=annotation,
        variants=variants_list
    )


@app.route(
    "/clinical-annotations/delete/<int:annotation_id>",
    methods=["POST"]
)
def delete_clinical_annotation(annotation_id):
    try:
        execute_query(
            "DELETE FROM clinical_annotations WHERE annotation_id=%s",
            (annotation_id,)
        )

        flash(
            "Clinical annotation deleted successfully.",
            "success"
        )

    except Exception as error:
        flash(
            f"Could not delete annotation: {error}",
            "error"
        )

    return redirect(
        url_for("clinical_annotations")
    )


@app.route("/reports")
def reports():
    disease_summary = fetch_all(
        """
        SELECT
            d.disease_name,
            d.disease_category,
            COUNT(p.patient_id) AS patient_count
        FROM diagnoses d
        LEFT JOIN patients p
            ON d.diagnosis_id=p.diagnosis_id
        GROUP BY
            d.diagnosis_id,
            d.disease_name,
            d.disease_category
        HAVING COUNT(p.patient_id) > 0
        ORDER BY
            patient_count DESC,
            d.disease_name
        """
    )

    gene_summary = fetch_all(
        """
        SELECT
            g.gene_symbol,
            g.gene_name,
            COUNT(v.variant_id) AS variant_count
        FROM genes g
        LEFT JOIN variants v
            ON g.gene_id=v.gene_id
        GROUP BY
            g.gene_id,
            g.gene_symbol,
            g.gene_name
        ORDER BY
            variant_count DESC,
            g.gene_symbol
        """
    )

    pathogenic_variants = fetch_all(
        """
        SELECT
            v.variant_id,
            g.gene_symbol,
            v.chromosome,
            v.position,
            v.reference_allele,
            v.alternate_allele
        FROM variants v
        LEFT JOIN genes g
            ON v.gene_id=g.gene_id
        WHERE v.clinical_significance='Pathogenic'
        ORDER BY
            g.gene_symbol,
            v.position
        """
    )

    high_frequency_variants = fetch_all(
        """
        SELECT DISTINCT
            v.variant_id,
            g.gene_symbol,
            v.chromosome,
            v.position,
            sv.allele_frequency
        FROM sample_variants sv
        JOIN variants v
            ON sv.variant_id=v.variant_id
        LEFT JOIN genes g
            ON v.gene_id=g.gene_id
        WHERE sv.allele_frequency >
              (
                  SELECT AVG(allele_frequency)
                  FROM sample_variants
              )
        ORDER BY
            sv.allele_frequency DESC
        """
    )

    return render_template(
        "reports.html",
        disease_summary=disease_summary,
        gene_summary=gene_summary,
        pathogenic_variants=pathogenic_variants,
        high_frequency_variants=high_frequency_variants
    )


@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        "error.html",
        message="Page not found."
    ), 404


@app.errorhandler(500)
def server_error(error):
    return render_template(
        "error.html",
        message="Something went wrong while processing the request."
    ), 500


if __name__ == "__main__":
    app.run(debug=True)