CREATE DATABASE IF NOT EXISTS clinical_genomics_db;

USE clinical_genomics_db;

CREATE TABLE diagnoses (
diagnosis_id INT PRIMARY KEY AUTO_INCREMENT,
disease_name VARCHAR(100),
disease_category VARCHAR(100)
);

CREATE TABLE patients (
patient_id INT PRIMARY KEY AUTO_INCREMENT,
patient_code VARCHAR(20) UNIQUE,
age INT,
sex VARCHAR(10),
diagnosis_id INT,
registration_date DATE,
FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(diagnosis_id)
);

CREATE TABLE samples (
sample_id INT PRIMARY KEY AUTO_INCREMENT,
patient_id INT,
sample_type VARCHAR(50),
collection_date DATE,
sequencing_status VARCHAR(20),
FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE sequencing_runs (
run_id INT PRIMARY KEY AUTO_INCREMENT,
sample_id INT,
platform VARCHAR(50),
run_date DATE,
read_count INT,
qc_status VARCHAR(20),
FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
);

CREATE TABLE genes (
gene_id INT PRIMARY KEY AUTO_INCREMENT,
gene_symbol VARCHAR(20) UNIQUE,
gene_name VARCHAR(100),
chromosome VARCHAR(20)
);

CREATE TABLE variants (
variant_id INT PRIMARY KEY AUTO_INCREMENT,
gene_id INT,
chromosome VARCHAR(20),
position INT,
reference_allele VARCHAR(10),
alternate_allele VARCHAR(10),
variant_type VARCHAR(20),
clinical_significance VARCHAR(30),
FOREIGN KEY (gene_id) REFERENCES genes(gene_id)
);

CREATE TABLE sample_variants (
sample_id INT,
variant_id INT,
allele_frequency DECIMAL(5,2),
depth INT,
zygosity VARCHAR(20),
PRIMARY KEY (sample_id, variant_id),
FOREIGN KEY (sample_id) REFERENCES samples(sample_id),
FOREIGN KEY (variant_id) REFERENCES variants(variant_id)
);

CREATE TABLE clinical_annotations (
annotation_id INT PRIMARY KEY AUTO_INCREMENT,
variant_id INT,
evidence_level VARCHAR(30),
`condition` VARCHAR(100),
source_database VARCHAR(50),
interpretation_date DATE,
FOREIGN KEY (variant_id) REFERENCES variants(variant_id)
);

INSERT INTO diagnoses (disease_name, disease_category)
VALUES
('Hypertension', 'Cardiovascular Disease'),
('Type 2 Diabetes', 'Metabolic Disease'),
('Asthma', 'Respiratory Disease'),
('Coronary Artery Disease', 'Cardiovascular Disease'),
('Breast Cancer', 'Cancer'),
('Lung Cancer', 'Cancer'),
('Colorectal Cancer', 'Cancer'),
('Prostate Cancer', 'Cancer'),
('Cystic Fibrosis', 'Congenital/Genetic Disease'),
('Sickle Cell Disease', 'Inherited Disease'),
('Thalassemia', 'Inherited Disease'),
('Congenital Heart Disease', 'Congenital Disease');
