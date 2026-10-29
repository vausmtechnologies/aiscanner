<?php

use App\Http\Controllers\LoginController;
use App\Http\Controllers\ScanController;
use App\Http\Middleware\RequireAppPassword;
use Illuminate\Support\Facades\Route;

Route::get('/login', [LoginController::class, 'show'])->name('login');
Route::post('/login', [LoginController::class, 'store'])->middleware('throttle:10,1')->name('login.store');
Route::post('/logout', [LoginController::class, 'destroy'])->name('logout');

Route::middleware(RequireAppPassword::class)->group(function () {
    Route::get('/', [ScanController::class, 'index'])->name('scan.index');
    Route::post('/scan', [ScanController::class, 'scan'])->name('scan.run');
    Route::get('/search', [ScanController::class, 'search'])->name('scan.search');
    Route::get('/scan/{batch}', [ScanController::class, 'wait'])->name('scan.wait');
    Route::get('/scan/{batch}/status', [ScanController::class, 'status'])->name('scan.status');
    Route::get('/scan/{batch}/result', [ScanController::class, 'result'])->name('scan.result');
});
