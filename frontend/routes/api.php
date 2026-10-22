<?php

use App\Http\Controllers\Api\ScanController as ApiScanController;
use App\Http\Controllers\ScanController;
use App\Http\Middleware\RequireApiKey;
use Illuminate\Support\Facades\Route;

Route::middleware(RequireApiKey::class)->group(function () {
    Route::post('/scan', [ApiScanController::class, 'store'])->name('api.scan.store');
    Route::get('/scan/{batch}/status', [ApiScanController::class, 'status'])->name('api.scan.status');
    Route::get('/scan/{batch}/result', [ApiScanController::class, 'result'])->name('api.scan.result');
    Route::get('/search', [ScanController::class, 'search'])->name('api.search');
});
