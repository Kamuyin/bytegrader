#!/bin/bash
# =============================================================================
# Moodle Docker Entrypoint
# Handles first-time installation and configuration
# =============================================================================

set -e

# Configuration
MOODLE_WWW=/var/www/html
MOODLE_DATA=/var/www/moodledata
CONFIG_FILE="${MOODLE_WWW}/config.php"
INSTALL_LOCK="${MOODLE_DATA}/.moodle_installed"

echo "=== Moodle Docker Entrypoint ==="

# Ensure moodledata directory exists and has correct permissions
mkdir -p "${MOODLE_DATA}"
mkdir -p "${MOODLE_DATA}/sessions"
chown -R www-data:www-data "${MOODLE_DATA}"
chmod -R 0777 "${MOODLE_DATA}"

# Copy config.php from template if not exists
if [ ! -f "${CONFIG_FILE}" ]; then
    echo "Creating config.php from template..."
    cp "${MOODLE_WWW}/config.php.template" "${CONFIG_FILE}"
    chown www-data:www-data "${CONFIG_FILE}"
fi

# Wait for database to be ready
wait_for_db() {
    local host="${MOODLE_DB_HOST:-moodle-db}"
    local port="${MOODLE_DB_PORT:-5432}"
    local max_attempts=60
    local attempt=1
    
    echo "Waiting for PostgreSQL at ${host}:${port}..."
    while ! pg_isready -h "${host}" -p "${port}" -q 2>/dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            echo "ERROR: Database not available after ${max_attempts} attempts"
            exit 1
        fi
        echo "  Attempt ${attempt}/${max_attempts}..."
        sleep 2
        ((attempt++))
    done
    echo "Database is ready!"
}

# Install Moodle if not already installed
install_moodle() {
    if [ -f "${INSTALL_LOCK}" ]; then
        echo "Moodle already installed (lock file exists)"
        return 0
    fi
    
    echo "=== Installing Moodle ==="
    
    # Get configuration from environment
    local admin_user="${MOODLE_ADMIN_USER:-admin}"
    local admin_pass="${MOODLE_ADMIN_PASSWORD:-Admin123!}"
    local admin_email="${MOODLE_ADMIN_EMAIL:-admin@example.com}"
    local site_name="${MOODLE_SITE_NAME:-BYTEGrader LMS}"
    local site_shortname="${MOODLE_SITE_SHORTNAME:-bytegrader}"
    
    echo "Installing with:"
    echo "  Admin User: ${admin_user}"
    echo "  Admin Email: ${admin_email}"
    echo "  Site Name: ${site_name}"
    
    # Run Moodle CLI installer
    php "${MOODLE_WWW}/admin/cli/install_database.php" \
        --agree-license \
        --fullname="${site_name}" \
        --shortname="${site_shortname}" \
        --summary="Learning Management System for BYTEGrader" \
        --adminuser="${admin_user}" \
        --adminpass="${admin_pass}" \
        --adminemail="${admin_email}"
    
    if [ $? -eq 0 ]; then
        echo "Moodle installation completed successfully!"
        touch "${INSTALL_LOCK}"
        
        # Enable LTI plugin
        echo "Enabling LTI external tool plugin..."
        php "${MOODLE_WWW}/admin/cli/cfg.php" --name=enablewebservices --set=1 2>/dev/null || true
        
    else
        echo "ERROR: Moodle installation failed!"
        exit 1
    fi
}

# Upgrade Moodle if needed
upgrade_moodle() {
    echo "Checking for Moodle upgrades..."
    php "${MOODLE_WWW}/admin/cli/upgrade.php" --non-interactive 2>/dev/null || true
}

# Main entrypoint logic
main() {
    # Wait for database
    wait_for_db
    
    # Install or upgrade Moodle
    if [ ! -f "${INSTALL_LOCK}" ]; then
        install_moodle
    else
        upgrade_moodle
    fi
    
    # Fix permissions one more time
    chown -R www-data:www-data "${MOODLE_DATA}"
    chown -R www-data:www-data "${MOODLE_WWW}"
    
    echo "=== Starting Apache ==="
    
    # Execute the main command (apache2-foreground)
    exec "$@"
}

main "$@"
