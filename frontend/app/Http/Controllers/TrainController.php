<?php

namespace App\Http\Controllers;

use App\Services\ScanException;
use App\Services\TrainingService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;
use ZipArchive;

class TrainController extends Controller
{
    private const ALLOWED_EXT = ['pdf', 'jpg', 'jpeg', 'png', 'tif', 'tiff', 'docx', 'doc', 'pptx', 'ppt', 'txt'];

    private const MAX_ENTRY_BYTES = 10485760; // 10 MB per document, same as scanning

    private const MAX_DOCUMENTS = 100;

    public function __construct(private TrainingService $training) {}

    public function index(): View
    {
        try {
            $categories = $this->training->categories();
            $error = null;
        } catch (ScanException $e) {
            $categories = [];
            $error = $e->getMessage();
        }

        return view('train', ['categories' => $categories, 'loadError' => $error]);
    }

    public function store(Request $request): RedirectResponse
    {
        $request->validate([
            'category' => ['required', 'string', 'max:60', 'regex:/^[A-Za-z0-9][A-Za-z0-9 &_\-]{1,59}$/'],
            'files' => 'required|array|min:1',
            'files.*' => 'file',
        ], [
            'category.regex' => 'Use 2-60 characters: letters, numbers, spaces, - _ &',
            'files.required' => 'Choose at least one sample document.',
            'files.uploaded' => 'Upload failed. A file is larger than the server allows.',
        ]);

        set_time_limit(0);
        $documents = $this->collectDocuments($request->file('files'));
        if (! $documents) {
            return back()->withInput()->withErrors(['files' => 'No supported documents found (pdf, image, docx, pptx, txt or a zip of them).']);
        }

        try {
            $report = $this->training->train($request->string('category')->toString(), $documents);
        } catch (ScanException $e) {
            return back()->withInput()->withErrors(['files' => $e->getMessage()]);
        }

        return redirect()->route('train.index')->with('trained', $report);
    }

    public function destroy(string $name): RedirectResponse
    {
        try {
            $this->training->delete($name);
        } catch (ScanException $e) {
            return back()->withErrors(['action' => $e->getMessage()]);
        }

        return redirect()->route('train.index')->with('status', "Removed \"{$name}\".");
    }

    public function promote(Request $request, string $name): RedirectResponse
    {
        $request->validate(['name' => 'nullable|string|max:60']);

        try {
            $category = $this->training->promote($name, trim((string) $request->input('name')) ?: null);
        } catch (ScanException $e) {
            return back()->withErrors(['action' => $e->getMessage()]);
        }

        return redirect()->route('train.index')->with('status', "Saved \"{$category['category']['name']}\" as a trained category.");
    }

    /**
     * Flattens uploads (single files and zips) into [filename, contents] pairs.
     *
     * @param  array<int, \Illuminate\Http\UploadedFile>  $uploads
     * @return array<int, array{0: string, 1: string}>
     */
    private function collectDocuments(array $uploads): array
    {
        $documents = [];
        foreach ($uploads as $upload) {
            $ext = strtolower($upload->getClientOriginalExtension());
            if ($ext === 'zip') {
                array_push($documents, ...$this->readZip($upload->getRealPath()));
            } elseif (in_array($ext, self::ALLOWED_EXT, true) && $upload->getSize() <= self::MAX_ENTRY_BYTES) {
                $documents[] = [$upload->getClientOriginalName(), file_get_contents($upload->getRealPath())];
            }
        }

        return array_slice($documents, 0, self::MAX_DOCUMENTS);
    }

    private function readZip(string $path): array
    {
        $zip = new ZipArchive;
        if ($zip->open($path) !== true) {
            return [];
        }

        $documents = [];
        for ($i = 0; $i < $zip->numFiles; $i++) {
            $stat = $zip->statIndex($i);
            $base = basename($stat['name']);
            if (str_ends_with($stat['name'], '/') || str_contains($stat['name'], '__MACOSX') || str_starts_with($base, '.')
                || ! in_array(strtolower(pathinfo($base, PATHINFO_EXTENSION)), self::ALLOWED_EXT, true)
                || $stat['size'] > self::MAX_ENTRY_BYTES) {
                continue;
            }
            $documents[] = [$base, $zip->getFromIndex($i)];
        }
        $zip->close();

        return $documents;
    }
}
