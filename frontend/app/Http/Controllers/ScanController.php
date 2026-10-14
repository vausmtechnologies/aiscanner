<?php

namespace App\Http\Controllers;

use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Http\Client\ConnectionException;
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
            $data = $this->parse(file_get_contents($file->getRealPath()), $file->getClientOriginalName());
        } catch (ConnectionException $e) {
            return back()->withErrors(['file' => 'Parser service is not reachable. Is FastAPI running?']);
        }

        if (!($data['success'] ?? false)) {
            return back()->withErrors(['file' => $data['message'] ?? 'Parser returned an error.']);
        }

        return back()
            ->with('result', $data)
            ->with('filename', $file->getClientOriginalName());
    }

    private function scanZip($file): RedirectResponse
    {
        set_time_limit(0);

        $zip = new ZipArchive();
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
                || !in_array(strtolower(pathinfo($base, PATHINFO_EXTENSION)), self::ALLOWED_EXT, true)) {
                if (!str_ends_with($name, '/')) {
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
                $data = $this->parse($zip->getFromIndex($i), $base);
            } catch (ConnectionException $e) {
                $zip->close();
                return back()->withErrors(['file' => 'Parser service is not reachable. Is FastAPI running?']);
            }

            $items[] = ($data['success'] ?? false)
                ? ['filename' => $name, 'result' => $data]
                : ['filename' => $name, 'error' => $data['message'] ?? 'Parser returned an error.'];
        }
        $zip->close();

        if (!$items) {
            return back()->withErrors(['file' => 'No supported documents found inside the zip.']);
        }

        return back()->with('batch', [
            'zip' => $file->getClientOriginalName(),
            'items' => $items,
            'skipped' => $skipped,
        ]);
    }

    private function parse(string $contents, string $name): array
    {
        $response = Http::timeout(120) // OCR can be slow
            ->attach('file', $contents, $name)
            ->post(rtrim(config('services.parser.url'), '/') . '/parse-document');

        return $response->json() ?? ['success' => false, 'message' => 'Parser returned an error (HTTP ' . $response->status() . ').'];
    }
}
