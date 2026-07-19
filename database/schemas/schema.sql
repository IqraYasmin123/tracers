-- TRACER database schema (PostgreSQL)
-- Auto-generated from database/models.py — do not hand-edit.
-- Regenerate via: python scripts/generate_schema_sql.py

CREATE TABLE users (
	id VARCHAR(36) NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role userrole NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE audit_logs (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36), 
	action VARCHAR(100) NOT NULL, 
	resource_type VARCHAR(50) NOT NULL, 
	resource_id VARCHAR(36), 
	details JSON NOT NULL, 
	ip_address VARCHAR(45), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE cases (
	id VARCHAR(36) NOT NULL, 
	case_number VARCHAR(50) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	status casestatus NOT NULL, 
	created_by VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE TABLE evidence (
	id VARCHAR(36) NOT NULL, 
	case_id VARCHAR(36) NOT NULL, 
	original_filename VARCHAR(255) NOT NULL, 
	storage_path VARCHAR(500) NOT NULL, 
	sha256_hash VARCHAR(64) NOT NULL, 
	mime_type VARCHAR(100) NOT NULL, 
	file_size_bytes INTEGER NOT NULL, 
	uploaded_by VARCHAR(36) NOT NULL, 
	uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES cases (id), 
	FOREIGN KEY(uploaded_by) REFERENCES users (id)
);

CREATE TABLE reports (
	id VARCHAR(36) NOT NULL, 
	case_id VARCHAR(36) NOT NULL, 
	generated_by VARCHAR(36) NOT NULL, 
	file_path VARCHAR(500) NOT NULL, 
	format reportformat NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES cases (id), 
	FOREIGN KEY(generated_by) REFERENCES users (id)
);

CREATE TABLE ai_results (
	id VARCHAR(36) NOT NULL, 
	evidence_id VARCHAR(36) NOT NULL, 
	verdict verdict NOT NULL, 
	confidence FLOAT NOT NULL, 
	attack_type VARCHAR(50), 
	attack_type_confidence FLOAT, 
	attribution_method VARCHAR(100) NOT NULL, 
	attribution_heatmap_path VARCHAR(500), 
	attribution_peak_fraction FLOAT, 
	reconstruction_ssim FLOAT, 
	reconstruction_psnr FLOAT, 
	reconstruction_path VARCHAR(500), 
	explanation_summary TEXT NOT NULL, 
	explanation_details JSON NOT NULL, 
	processing_time_ms FLOAT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(evidence_id) REFERENCES evidence (id)
);
