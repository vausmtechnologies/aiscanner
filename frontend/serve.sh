#!/bin/sh
# Same as `php artisan serve`, but with 50 MB uploads (PHP's default is 2 MB).
cd "$(dirname "$0")/public" || exit 1
exec php -d upload_max_filesize=50M -d post_max_size=55M -d memory_limit=512M -d max_execution_time=300 \
  -S 127.0.0.1:${1:-8001} ../vendor/laravel/framework/src/Illuminate/Foundation/resources/server.php
