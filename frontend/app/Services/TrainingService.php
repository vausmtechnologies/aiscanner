<?php

namespace App\Services;

use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\PendingRequest;
use Illuminate\Support\Facades\Http;

/** Talks to the parser's training endpoints: list, train, delete and confirm categories. */
class TrainingService
{
    /** @return array<int, array> built-in, trained and auto-created categories */
    public function categories(): array
    {
        return $this->call(fn (PendingRequest $http) => $http->get($this->url('/categories')))['categories'] ?? [];
    }

    /**
     * Teach a category from sample documents.
     *
     * @param  array<int, array{0: string, 1: string}>  $files  [filename, contents] pairs
     */
    public function train(string $category, array $files): array
    {
        return $this->call(function (PendingRequest $http) use ($category, $files) {
            foreach ($files as [$name, $contents]) {
                $http = $http->attach('files', $contents, $name);
            }

            return $http->timeout(600)->post($this->url('/train'), ['category' => $category]);
        });
    }

    public function delete(string $name): void
    {
        $this->call(fn (PendingRequest $http) => $http->delete($this->url('/categories/'.rawurlencode($name))));
    }

    public function promote(string $name, ?string $newName): array
    {
        return $this->call(fn (PendingRequest $http) => $http->post($this->url('/categories/'.rawurlencode($name).'/promote'), ['name' => $newName]));
    }

    private function url(string $path): string
    {
        return rtrim(config('services.parser.url'), '/').$path;
    }

    private function call(callable $request): array
    {
        try {
            $response = $request(Http::timeout(30)->acceptJson()->withHeaders(['X-API-Key' => (string) config('services.parser.key')]));
        } catch (ConnectionException) {
            throw new ScanException('Parser service is not reachable. Is FastAPI running?', 503);
        }

        if (! $response->successful()) {
            throw new ScanException($response->json('message') ?? 'Parser returned an error (HTTP '.$response->status().').', 502);
        }

        return $response->json() ?? [];
    }
}
