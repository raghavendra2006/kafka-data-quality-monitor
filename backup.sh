#!/bin/bash
# =============================================
# Warehouse Database Backup Script
# =============================================
# Usage: docker-compose exec postgres-warehouse bash /backup.sh
#
# Creates a timestamped pg_dump of the warehouse database
# in the /backups directory (mounted from host ./backups/).

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
BACKUP_FILE="${BACKUP_DIR}/warehouse_backup_${TIMESTAMP}.sql"

DB_NAME="${POSTGRES_DB:-warehouse_db}"
DB_USER="${POSTGRES_USER:-warehouse_user}"

echo "============================================="
echo "  Data Warehouse Backup"
echo "============================================="
echo "  Database : ${DB_NAME}"
echo "  User     : ${DB_USER}"
echo "  Output   : ${BACKUP_FILE}"
echo "  Time     : $(date)"
echo "============================================="

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# Perform the backup
pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists --create > "${BACKUP_FILE}"

# Verify
if [ -s "${BACKUP_FILE}" ]; then
    FILE_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo ""
    echo "  ✓ Backup completed successfully!"
    echo "  File size: ${FILE_SIZE}"
    echo "  Location : ${BACKUP_FILE}"
    echo "============================================="
else
    echo "  ✗ ERROR: Backup file is empty!"
    exit 1
fi
