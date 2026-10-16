<?php

namespace App\Http\Controllers;

use App\Models\Document;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Str;
use Illuminate\View\View;
use ZipArchive;

class ScanController extends Controller
{
    private const ALLOWED_EXT = ['pdf', 'jpg', 'jpeg', 'png', 'tif', 'tiff', 'docx', 'doc', 'pptx', 'ppt', 'txt'];

    private const MAX_ZIP_FILES = 30;

    private const MAX_ENTRY_BYTES = 10485760; // 10 MB per document inside a zip

    public function index(): View
    {
        return view('scan');
    }

    public function scan(Request $request): RedirectResponse
    {
        $request->validate([
            'file' => 'required|file|max:51200', // KB
        ]);

        $file = $request->file('file');

        if (strtolower($file->getClientOriginalExtension()) === 'zip') {
            return $this->scanZip($file);
        }

        if ($file->getSize() > 20 * 1024 * 1024) {
            return back()->withErrors(['file' => 'File is too large (max 20 MB).']);
        }

        try {
            $jobId = $this->enqueue(file_get_contents($file->getRealPath()), $file->getClientOriginalName());
        } catch (ConnectionException $e) {
            return back()->withErrors(['file' => 'Parser service is not reachable. Is FastAPI running?']);
        } catch (\RuntimeException $e) {
            return back()->withErrors(['file' => $e->getMessage()]);
        }

        return $this->startBatch([
            'zip' => null,
            'filename' => $file->getClientOriginalName(),
            'items' => [['filename' => $file->getClientOriginalName(), 'job_id' => $jobId]],
            'skipped' => 0,
        ]);
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
        if (! Cache::has($this->key($batch))) {
            return redirect()->route('scan.index')->withErrors(['file' => 'This scan expired. Please upload again.']);
        }

        return view('scan', ['waiting' => $batch]);
    }

    public function status(string $batch): JsonResponse
    {
        $meta = Cache::get($this->key($batch));
        if (! $meta) {
            return response()->json(['done' => true, 'expired' => true]);
        }

        $total = 0;
        $finished = 0;
        foreach ($meta['items'] as $item) {
            if (! isset($item['job_id'])) {
                continue;
            }
            $total++;
            if (in_array($this->jobStatus($item['job_id'])['status'], ['finished', 'failed', 'missing'], true)) {
                $finished++;
            }
        }

        return response()->json(['done' => $finished >= $total, 'finished' => $finished, 'total' => $total]);
    }

    /** Collects finished jobs and hands them to the existing result views. */
    public function result(string $batch): RedirectResponse
    {
        $meta = Cache::get($this->key($batch));
        if (! $meta) {
            return redirect()->route('scan.index')->withErrors(['file' => 'This scan expired. Please upload again.']);
        }

        $items = [];
        foreach ($meta['items'] as $item) {
            if (! isset($item['job_id'])) {
                $items[] = $item;

                continue;
            }
            $job = $this->jobStatus($item['job_id']);
            $data = $job['result'] ?? null;
            if ($job['status'] === 'finished' && ($data['success'] ?? false)) {
                Document::storeScan($item['filename'], $data);
                $items[] = ['filename' => $item['filename'], 'result' => $data];
            } else {
                $items[] = ['filename' => $item['filename'], 'error' => $data['message'] ?? $job['message'] ?? 'Parser returned an error.'];
            }
        }
        Cache::forget($this->key($batch));

        if ($meta['zip'] === null) {
            $only = $items[0];
            if (isset($only['error'])) {
                return redirect()->route('scan.index')->withErrors(['file' => $only['error']]);
            }

            return redirect()->route('scan.index')->with('result', $only['result'])->with('filename', $meta['filename']);
        }

        return redirect()->route('scan.index')->with('batch', ['zip' => $meta['zip'], 'items' => $items, 'skipped' => $meta['skipped']]);
    }

    private function startBatch(array $meta): RedirectResponse
    {
        $id = (string) Str::uuid();
        Cache::put($this->key($id), $meta, now()->addHour());

        return redirect()->route('scan.wait', $id);
    }

    private function key(string $batch): string
    {
        return 'scan:'.$batch;
    }

    private function scanZip($file): RedirectResponse
    {
        set_time_limit(0);

        $zip = new ZipArchive;
        if ($zip->open($file->getRealPath()) !== true) {
            return back()->withErrors(['file' => 'Could not open the zip file. Is it corrupt?']);
        }

        $items = [];
        $skipped = 0;

        for ($i = 0; $i < $zip->numFiles; $i++) {
            $stat = $zip->statIndex($i);
            $name = $stat['name'];
            $base = basename($name);

            // skip folders, macOS junk, hidden files, nested archives and unsupported types
            if (str_ends_with($name, '/') || str_contains($name, '__MACOSX') || str_starts_with($base, '.')
                || ! in_array(strtolower(pathinfo($base, PATHINFO_EXTENSION)), self::ALLOWED_EXT, true)) {
                if (! str_ends_with($name, '/')) {
                    $skipped++;
                }

                continue;
            }

            if ($stat['size'] > self::MAX_ENTRY_BYTES) {
                $items[] = ['filename' => $name, 'error' => 'File is too large (max 10 MB).'];

                continue;
            }

            if (count($items) >= self::MAX_ZIP_FILES) {
                $skipped++;

                continue;
            }

            try {
                $items[] = ['filename' => $name, 'job_id' => $this->enqueue($zip->getFromIndex($i), $base)];
            } catch (ConnectionException $e) {
                $zip->close();

                return back()->withErrors(['file' => 'Parser service is not reachable. Is FastAPI running?']);
            } catch (\RuntimeException $e) {
                $zip->close();

                return back()->withErrors(['file' => $e->getMessage()]);
            }
        }
        $zip->close();

        if (! $items) {
            return back()->withErrors(['file' => 'No supported documents found inside the zip.']);
        }

        return $this->startBatch([
            'zip' => $file->getClientOriginalName(),
            'filename' => $file->getClientOriginalName(),
            'items' => $items,
            'skipped' => $skipped,
        ]);
    }

    private function baseUrl(): string
    {
        return rtrim(config('services.parser.url'), '/');
    }

    /** Queue a document on the parser service; returns the job id. */
    private function enqueue(string $contents, string $name): string
    {
        $response = Http::timeout(30)
            ->attach('file', $contents, $name)
            ->post($this->baseUrl().'/jobs');

        $jobId = $response->json('job_id');
        if (! $response->successful() || ! $jobId) {
            throw new \RuntimeException($response->json('message') ?? 'Could not queue the document (HTTP '.$response->status().').');
        }

        return $jobId;
    }

    private function jobStatus(string $jobId): array
    {
        try {
            $response = Http::timeout(10)->get($this->baseUrl().'/jobs/'.$jobId);
        } catch (ConnectionException $e) {
            return ['status' => 'queued']; // keep waiting; service may be restarting
        }

        if ($response->status() === 404) {
            return ['status' => 'missing', 'message' => 'Result expired. Please upload again.'];
        }

        return $response->json() ?? ['status' => 'queued'];
    }
}
