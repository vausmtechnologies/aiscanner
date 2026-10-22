<?php

return [

    /*
    | Cross-origin settings for the JSON API. Defaults to any origin so any frontend can connect;
    | set CORS_ALLOWED_ORIGINS to a comma separated list (e.g. https://app.example.com) to restrict it.
    */

    'paths' => ['api/*'],

    'allowed_methods' => ['*'],

    'allowed_origins' => array_values(array_filter(array_map('trim', explode(',', env('CORS_ALLOWED_ORIGINS', '*'))))),

    'allowed_origins_patterns' => [],

    'allowed_headers' => ['*'],

    'exposed_headers' => [],

    'max_age' => 600,

    'supports_credentials' => false,

];
