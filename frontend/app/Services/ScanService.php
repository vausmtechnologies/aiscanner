<?php

namespace App\Services;

use App\Models\Document;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Str;
use ZipArchive;

class ScanService
{
    private const ALLOWED_EXT = ['pdf', 'jpg', 'jpeg', 'png', 'tif', 'tiff', 'docx', 'doc', 'pptx', 'ppt', 'txt'];

    private const MAX_ZIP_FILES = 30;

    private const MAX_ENTRY_BYTES = 10485760; // 10 MB per document inside a zip

    private const MAX_FILE_BYTES = 20971520; // 20 MB for a single document

    /**
     * Queue the upload (a single document or a zip) on the parser service.
     *
     * @return string the batch id to poll with status() and collect with result()
     *
     * @throws ScanException
     */
    public function start(UploadedFile $file): string
    {
        if (strtolower($file->getClientOriginalExtension()) === 'zip') {
            return $this->startZip($file);
        }

        if ($file->getSize() > self::MAX_FILE_BYTES) {
            throw new ScanException('File is too large (max 20 MB).');
        }

        $name = $file->getClientOriginalName();

        return $this->startBatch([
            'zip' => null,
            'filename' => $name,
            'items' => [['filename' => $name, 'job_id' => $this->enqueue(file_get_contents($file->getRealPath()), $name)]],
            'skipped' => 0,
        ]);
    }

    public function exists(string $batch): bool
    {
        return Cache::has($this->key($batch));
    }

    /** @return array{done: bool, finished?: int, total?: int, expired?: bool} */
    public function status(string $batch): array
    {
        $meta = Cache::get($this->key($batch));
        if (! $meta) {
            return ['done' => true, 'expired' => true];
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

        return ['done' => $finished >= $total, 'finished' => $finished, 'total' => $total];
    }

    /**
     * Collects the finished jobs, stores the successful scans and forgets the batch.
     *
     * @return array{zip: ?string, filename: string, skipped: int, items: array<int, array>}|null null when the batch expired
     */
    public function result(string $batch): ?array
    {
        $meta = Cache::get($this->key($batch));
        if (! $meta) {
            return null;
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

        return ['zip' => $meta['zip'], 'filename' => $meta['filename'], 'skipped' => $meta['skipped'], 'items' => $items];
    }

    private function startBatch(array $meta): string
    {
        $id = (string) Str::uuid();
        Cache::put($this->key($id), $meta, now()->addHour());

        return $id;
    }

    private function key(string $batch): string
    {
        return 'scan:'.$batch;
    }

    private function startZip(UploadedFile $file): string
    {
        set_time_limit(0);

        $zip = new ZipArchive;
        if ($zip->open($file->getRealPath()) !== true) {
            throw new ScanException('Could not open the zip file. Is it corrupt?');
        }

        $items = [];
        $skipped = 0;

        try {
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

                $items[] = ['filename' => $name, 'job_id' => $this->enqueue($zip->getFromIndex($i), $base)];
            }
        } finally {
            $zip->close();
        }

        if (! $items) {
            throw new ScanException('No supported documents found inside the zip.');
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

    private function parserHeaders(): array
    {
        return ['X-API-Key' => (string) config('services.parser.key')];
    }

    /** Queue a document on the parser service; returns the job id. */
    private function enqueue(string $contents, string $name): string
    {
        try {
            $response = Http::timeout(30)
                ->withHeaders($this->parserHeaders())
                ->attach('file', $contents, $name)
                ->post($this->baseUrl().'/jobs');
        } catch (ConnectionException) {
            throw new ScanException('Parser service is not reachable. Is FastAPI running?', 503);
        }

        $jobId = $response->json('job_id');
        if (! $response->successful() || ! $jobId) {
            throw new ScanException($response->json('message') ?? 'Could not queue the document (HTTP '.$response->status().').', 502);
        }

        return $jobId;
    }

    private function jobStatus(string $jobId): array
    {
        try {
            $response = Http::timeout(10)->withHeaders($this->parserHeaders())->get($this->baseUrl().'/jobs/'.$jobId);
        } catch (ConnectionException) {
            return ['status' => 'queued']; // keep waiting; service may be restarting
        }

        if ($response->status() === 404) {
            return ['status' => 'missing', 'message' => 'Result expired. Please upload again.'];
        }

        return $response->json() ?? ['status' => 'queued'];
    }
}
