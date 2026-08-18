#!/bin/bash

# === Configuration ===
CERTS_DIR=".secrets"
DAYS_VALID=36500

mkdir -p $CERTS_DIR
cd $CERTS_DIR

# === 1. Generate Root CA ===
echo "🔐 Generating Root CA..."
openssl genrsa -out rootCA.key 4096
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days $DAYS_VALID \
  -out rootCA.crt \
  -subj "/C=PL/ST=Malopolska/L=Cracow/O=MyOrg/OU=IT/CN=Root CA"

# === 2. Generate Server Certificate ===
echo "🔐 Generating Server Certificate..."
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr \
  -subj "/C=PL/ST=Malopolska/L=Cracow/O=MyOrg/OU=DB/CN=db"

openssl x509 -req -in server.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial \
  -out server.crt -days $DAYS_VALID -sha256 \
  -extfile <(cat <<-EOF
    subjectAltName=DNS:db,DNS:localhost,IP:127.0.0.1
    extendedKeyUsage=serverAuth
EOF
)

# === 3. Generate Client Certificate ===
echo "🔐 Generating Client Certificate..."
openssl genrsa -out client.key 4096
openssl req -new -key client.key -out client.csr \
  -subj "/C=PL/ST=Malopolska/L=Cracow/O=MyOrg/OU=Dev/CN=raketa_user"

openssl x509 -req -in client.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial \
  -out client.crt -days $DAYS_VALID -sha256 \
  -extfile <(echo "extendedKeyUsage=clientAuth")

# === Set Permissions ===
chmod 600 *.key

cd -
echo "✅ Certificates generated in $CERTS_DIR"
