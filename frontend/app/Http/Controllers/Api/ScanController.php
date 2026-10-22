<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\ScanException;
use App\Services\ScanService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ScanController extends Controller
{
    public function __construct(private ScanService $scans) {}

    /** Queue a document or zip; poll status() with the returned batch id. */
    public function store(Request $request): JsonResponse
    {
        $request->validate([
            'file' => 'required|file|max:51200', // KB
        ]);

        try {
            $batch = $this->scans->start($request->file('file'));
        } catch (ScanException $e) {
            return response()->json(['message' => $e->getMessage()], $e->status);
        }

        return response()->json(['batch_id' => $batch], 202);
    }

    public function status(string $batch): JsonResponse
    {
        $status = $this->scans->status($batch);

        return response()->json($status, ($status['expired'] ?? false) ? 404 : 200);
    }

    /** Single-use: returns the finished scans and clears the batch. */
    public function result(string $batch): JsonResponse
    {
        if (! $this->scans->exists($batch)) {
            return response()->json(['message' => 'This scan expired. Please upload again.'], 404);
        }

        $status = $this->scans->status($batch);
        if (! $status['done']) {
            return response()->json($status, 409);
        }

        $result = $this->scans->result($batch);
        if ($result === null) {
            return response()->json(['message' => 'This scan expired. Please upload again.'], 404);
        }

        return response()->json($result);
    }
}
