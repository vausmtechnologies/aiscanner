<?php

use App\Http\Controllers\ScanController;
use Illuminate\Support\Facades\Route;

Route::get('/', [ScanController::class, 'index'])->name('scan.index');
Route::post('/scan', [ScanController::class, 'scan'])->name('scan.run');
Route::get('/search', [ScanController::class, 'search'])->name('scan.search');
Route::get('/scan/{batch}', [ScanController::class, 'wait'])->name('scan.wait');
Route::get('/scan/{batch}/status', [ScanController::class, 'status'])->name('scan.status');
Route::get('/scan/{batch}/result', [ScanController::class, 'result'])->name('scan.result');
