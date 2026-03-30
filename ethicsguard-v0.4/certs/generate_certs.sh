#!/usr/bin/env bash
# =============================================================================
# EthicsGuard v0.4 — Self-Signed Certificate Generator
# =============================================================================
# Generates a self-signed CA and per-service TLS certificates for local
# development and testing. NOT for production use.
# =============================================================================

set -euo pipefail

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAYS_VALID=365
CA_SUBJECT="/C=US/ST=California/L=SanFrancisco/O=EthicsGuard/OU=Dev/CN=EthicsGuard-CA"
SERVICES=("guardrail-service" "redteam-service" "evaluation-service" "dashboard-service")

echo "=== EthicsGuard Certificate Generator ==="
echo "Output directory: ${CERT_DIR}"
echo ""

# ---- Generate CA key and certificate ----
echo "[1/3] Generating Certificate Authority (CA)..."
openssl genrsa -out "${CERT_DIR}/ca.key" 4096
openssl req -new -x509 \
    -key "${CERT_DIR}/ca.key" \
    -sha256 \
    -subj "${CA_SUBJECT}" \
    -days ${DAYS_VALID} \
    -out "${CERT_DIR}/ca.crt"
echo "  -> ca.key, ca.crt"

# ---- Generate per-service certificates ----
echo "[2/3] Generating per-service certificates..."
for SERVICE in "${SERVICES[@]}"; do
    echo "  Generating cert for: ${SERVICE}"

    # Create private key
    openssl genrsa -out "${CERT_DIR}/${SERVICE}.key" 2048

    # Create Certificate Signing Request (CSR)
    openssl req -new \
        -key "${CERT_DIR}/${SERVICE}.key" \
        -subj "/C=US/ST=California/L=SanFrancisco/O=EthicsGuard/OU=${SERVICE}/CN=${SERVICE}" \
        -out "${CERT_DIR}/${SERVICE}.csr"

    # Create extensions file for SAN (Subject Alternative Names)
    cat > "${CERT_DIR}/${SERVICE}.ext" <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${SERVICE}
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF

    # Sign the certificate with our CA
    openssl x509 -req \
        -in "${CERT_DIR}/${SERVICE}.csr" \
        -CA "${CERT_DIR}/ca.crt" \
        -CAkey "${CERT_DIR}/ca.key" \
        -CAcreateserial \
        -out "${CERT_DIR}/${SERVICE}.crt" \
        -days ${DAYS_VALID} \
        -sha256 \
        -extfile "${CERT_DIR}/${SERVICE}.ext"

    # Clean up CSR and extensions file
    rm -f "${CERT_DIR}/${SERVICE}.csr" "${CERT_DIR}/${SERVICE}.ext"

    echo "    -> ${SERVICE}.key, ${SERVICE}.crt"
done

# ---- Generate a combined server cert for simple setups ----
echo "[3/3] Generating combined server certificate..."
openssl genrsa -out "${CERT_DIR}/server.key" 2048
openssl req -new \
    -key "${CERT_DIR}/server.key" \
    -subj "/C=US/ST=California/L=SanFrancisco/O=EthicsGuard/OU=Server/CN=ethicsguard-server" \
    -out "${CERT_DIR}/server.csr"

cat > "${CERT_DIR}/server.ext" <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = guardrail-service
DNS.2 = redteam-service
DNS.3 = evaluation-service
DNS.4 = dashboard-service
DNS.5 = localhost
IP.1 = 127.0.0.1
EOF

openssl x509 -req \
    -in "${CERT_DIR}/server.csr" \
    -CA "${CERT_DIR}/ca.crt" \
    -CAkey "${CERT_DIR}/ca.key" \
    -CAcreateserial \
    -out "${CERT_DIR}/server.crt" \
    -days ${DAYS_VALID} \
    -sha256 \
    -extfile "${CERT_DIR}/server.ext"

rm -f "${CERT_DIR}/server.csr" "${CERT_DIR}/server.ext" "${CERT_DIR}/ca.srl"

echo "  -> server.key, server.crt"
echo ""
echo "=== Done! All certificates generated in ${CERT_DIR} ==="
echo ""
echo "Files created:"
ls -la "${CERT_DIR}"/*.{key,crt} 2>/dev/null || true
