# =============================================================================
# Custom Moodle Docker Image
# Uses official moodlehq/moodle-php-apache base with Moodle source
# =============================================================================

FROM moodlehq/moodle-php-apache:8.2-bullseye

# Moodle version to install
ARG MOODLE_VERSION=MOODLE_405_STABLE

# Set environment variables
ENV MOODLE_DATA=/var/www/moodledata \
    MOODLE_WWW=/var/www/html \
    APACHE_RUN_USER=www-data \
    APACHE_RUN_GROUP=www-data

# Install additional dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    unzip \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create moodledata directory
RUN mkdir -p ${MOODLE_DATA} && \
    chown -R www-data:www-data ${MOODLE_DATA} && \
    chmod 755 ${MOODLE_DATA}

# Clone Moodle source code
RUN git clone --depth=1 --branch ${MOODLE_VERSION} \
    https://github.com/moodle/moodle.git ${MOODLE_WWW} && \
    chown -R www-data:www-data ${MOODLE_WWW}

# Copy configuration template
COPY config.php.template /var/www/html/config.php.template

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose port 80
EXPOSE 80

# Set working directory
WORKDIR /var/www/html

# Custom entrypoint for initialization
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["apache2-foreground"]
