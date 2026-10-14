<?php

use App\Http\Controllers\ScanController;
use Illuminate\Support\Facades\Route;

Route::get('/', [ScanController::class, 'index'])->name('scan.index');
Route::post('/scan', [ScanController::class, 'scan'])->name('scan.run');
