<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/** Gates the web UI behind APP_PASSWORD. When APP_PASSWORD is empty the UI stays open. */
class RequireAppPassword
{
    public function handle(Request $request, Closure $next): Response
    {
        $password = (string) config('services.app.password');
        if ($password === '' || $request->session()->get('app_authed') === true) {
            return $next($request);
        }

        return redirect()->route('login');
    }
}
