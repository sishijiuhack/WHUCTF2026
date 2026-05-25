FROM php:5.6-apache

RUN docker-php-ext-install exif \
    && echo 'date.timezone=UTC' > /usr/local/etc/php/conf.d/date_timezone.ini

COPY . /var/www/html/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN mkdir -p /var/www/html/uploads \
    && chmod -R 777 /var/www/html/uploads \
    && chmod +x /usr/local/bin/docker-entrypoint.sh

WORKDIR /var/www/html

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["apache2-foreground"]
