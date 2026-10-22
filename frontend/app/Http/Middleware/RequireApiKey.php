<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/** Guards the JSON API with the shared API_KEY. A server without a key refuses every call. */
class RequireApiKey
{
    public function handle(Request $request, Closure $next): Response
    {
        $expected = (string) config('services.api.key');
        if ($expected === '') {
            return response()->json(['message' => 'API_KEY is not configured on the server.'], 503);
        }

        $given = (string) ($request->header('X-API-Key') ?: $request->bearerToken());
        if (! hash_equals($expected, $given)) {
            return response()->json(['message' => 'Invalid or missing API key.'], 401);
        }

        return $next($request);
    }
}
