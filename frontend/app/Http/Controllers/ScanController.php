<?php

namespace App\Http\Controllers;

use App\Models\Document;
use App\Services\ScanException;
use App\Services\ScanService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ScanController extends Controller
{
    public function __construct(private ScanService $scans) {}

    public function index(): View
    {
        return view('scan');
    }

    public function scan(Request $request): RedirectResponse
    {
        $request->validate([
            'file' => 'required|file|max:51200', // KB
        ]);

        try {
            $batch = $this->scans->start($request->file('file'));
        } catch (ScanException $e) {
            return back()->withErrors(['file' => $e->getMessage()]);
        }

        return redirect()->route('scan.wait', $batch);
    }

    /** Keyword search over every document scanned so far (empty term lists the latest ones). */
    public function search(Request $request): JsonResponse
    {
        $term = trim((string) $request->query('q', ''));
        $type = trim((string) $request->query('type', ''));
        $status = trim((string) $request->query('status', ''));

        $documents = Document::query()
            ->when($term !== '', fn ($query) => $query->matching($term))
            ->when($type !== '', fn ($query) => $type === 'unknown' ? $query->whereNull('document_type') : $query->where('document_type', $type))
            ->when($status !== '', fn ($query) => $query->where('expiry_status', $status))
            ->latest('updated_at')
            ->limit(50)
            ->get();

        // Chip counts follow the search term only, so the chips don't vanish when one is selected.
        $types = Document::query()
            ->when($term !== '', fn ($query) => $query->matching($term))
            ->selectRaw('document_type, count(*) as total')
            ->groupBy('document_type')
            ->pluck('total', 'document_type');

        return response()->json([
            'query' => $term,
            'count' => $documents->count(),
            'types' => $types,
            'documents' => $documents->map(fn (Document $document) => [
                'id' => $document->id,
                'filename' => $document->filename,
                'document_type' => $document->document_type,
                'country' => $document->country,
                'confidence' => $document->confidence,
                'expiry_status' => $document->expiry_status,
                'expiry_date' => $document->expiry_date?->toDateString(),
                'metadata' => $document->metadata ?? [],
                'scanned_at' => $document->updated_at?->diffForHumans(),
            ]),
        ]);
    }

    /** Waiting page: polls status until all queued jobs are done. */
    public function wait(string $batch): View|RedirectResponse
    {
        if (! $this->scans->exists($batch)) {
            return redirect()->route('scan.index')->withErrors(['file' => 'This scan expired. Please upload again.']);
        }

        return view('scan', ['waiting' => $batch]);
    }

    public function status(string $batch): JsonResponse
    {
        return response()->json($this->scans->status($batch));
    }

    /** Collects finished jobs and hands them to the existing result views. */
    public function result(string $batch): RedirectResponse
    {
        $outcome = $this->scans->result($batch);
        if ($outcome === null) {
            return redirect()->route('scan.index')->withErrors(['file' => 'This scan expired. Please upload again.']);
        }

        if ($outcome['zip'] === null) {
            $only = $outcome['items'][0];
            if (isset($only['error'])) {
                return redirect()->route('scan.index')->withErrors(['file' => $only['error']]);
            }

            return redirect()->route('scan.index')->with('result', $only['result'])->with('filename', $outcome['filename']);
        }

        return redirect()->route('scan.index')->with('batch', ['zip' => $outcome['zip'], 'items' => $outcome['items'], 'skipped' => $outcome['skipped']]);
    }
}
