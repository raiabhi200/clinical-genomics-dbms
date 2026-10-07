# Clinical Genomics & Precision Medicine Data Management System

A Flask + MySQL academic DBMS application for managing a synthetic clinical genomics dataset.

## Completed features

- Sage/charcoal interface inspired by the supplied color reference
- Live dashboard counts
- Diagnosis reference page
- Patient CRUD + patient search
- Sample CRUD
- Sequencing run CRUD
- Gene CRUD
- Variant CRUD
- Sample-variant many-to-many CRUD
- Clinical annotation CRUD
- Reports using JOIN, GROUP BY, HAVING and a subquery
- Foreign-key-linked dropdowns for related records
- Separate MySQL connection module
- Environment variables kept out of GitHub
- Basic documentation and ER relationship map

## Project structure

```text
clinical-genomics-dbms/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── database/
│   ├── db_connection.py
│   └── schema.sql
├── docs/
├── screenshots/
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/
```

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and enter your local MySQL credentials.
4. On a fresh database, run `database/schema.sql`.
5. Start the app:

```bash
python app.py
```

6. Open `http://127.0.0.1:5000`.

All patient, sample, sequencing, gene, variant, sample-variant and annotation records are entered through the website. The included diagnosis rows are synthetic lookup data.
