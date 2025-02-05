#!/bin/bash
# setup.sh

set -e

alias python="py"

# Full paths for Windows tools
# GCLOUD="/c/Users/srama/AppData/Local/Google/Cloud\ SDK/google-cloud-sdk/bin/gcloud"
GCLOUD="gcloud"
TERRAFORM="/c/Terraform/terraform"
# PSQL="/c/'Program Files'/PostgreSQL/17/bin/psql"
PSQL="psql"
export CLOUDSDK_PYTHON="py"

# Check for required tools
command -v "$TERRAFORM" >/dev/null 2>&1 || { echo "Terraform is required but not installed. Aborting." >&2; exit 1; }
command -v "$GCLOUD" >/dev/null 2>&1 || { echo "Google Cloud SDK is required but not installed. Aborting." >&2; exit 1; }
command -v "$PSQL" >/dev/null 2>&1 || { echo "PostgreSQL client is required but not installed. Aborting." >&2; exit 1; }

# Configuration
PROJECT_ID="budget-management-449817"
REGION="us-west2"
DB_PASSWORD=$(openssl rand -base64 32)

# Initialize GCP project
echo "Initializing GCP project..."
gcloud config set project $PROJECT_ID

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id = "${PROJECT_ID}"
region     = "${REGION}"
db_password = "${DB_PASSWORD}"
EOF

# Apply Terraform configuration
echo "Applying Terraform configuration..."
terraform apply -auto-approve

# Get database instance name
DB_INSTANCE=$(terraform output -raw db_instance_name)

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 60  # Adjust if needed

# Download and start Cloud SQL Proxy
echo "Setting up Cloud SQL Proxy..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64
else
    wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
fi
chmod +x cloud_sql_proxy

# Start Cloud SQL Proxy in background
./cloud_sql_proxy -instances=${PROJECT_ID}:${REGION}:${DB_INSTANCE}=tcp:5432 &
PROXY_PID=$!

# Wait for proxy to be ready
sleep 10

# Create database schema
echo "Creating database schema..."
PGPASSWORD=$DB_PASSWORD psql -h localhost -U budget_app -d budget_management <<EOF
CREATE TABLE users (
    ldap VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    level INTEGER CHECK (level >= 1 AND level <= 12)
);

CREATE TABLE org_hierarchy (
    employee_ldap VARCHAR(50) REFERENCES users(ldap),
    manager_ldap VARCHAR(50) REFERENCES users(ldap),
    PRIMARY KEY (employee_ldap)
);

CREATE TABLE annual_operating_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    state VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_state CHECK (state IN ('draft', 'active', 'EOL'))
);

CREATE TABLE budgets (
    id SERIAL PRIMARY KEY,
    unique_identifier VARCHAR(50) UNIQUE,
    aop_id INTEGER REFERENCES annual_operating_plans(id),
    requestor_ldap VARCHAR(50) REFERENCES users(ldap),
    responsible_ldap VARCHAR(50) REFERENCES users(ldap),
    budget_driver VARCHAR(255),
    description TEXT,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

# Clean up
kill $PROXY_PID

echo "Setup complete!"
echo "Database password: $DB_PASSWORD"
echo "Please save these credentials securely."
echo "Cloud Run URL: $(terraform output -raw cloud_run_url)"
