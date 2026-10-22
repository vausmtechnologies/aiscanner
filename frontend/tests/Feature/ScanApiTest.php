<?php

namespace Tests\Feature;

use App\Models\Document;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class ScanApiTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        config(['services.parser.url' => 'http://parser.test', 'services.api.key' => 'secret']);
        $this->withHeaders(['X-API-Key' => 'secret']);
    }

    private function finishedResult(): array
    {
        return [
            'success' => true,
            'document_type' => 'Vehicles',
            'country' => 'India',
            'metadata' => [],
            'keywords_detected' => [],
            'expiry' => ['status' => 'valid', 'expiry_date' => '2030-01-31'],
        ];
    }

    public function test_scan_returns_a_batch_id_that_can_be_polled_and_collected(): void
    {
        Http::fake([
            'parser.test/jobs' => Http::response(['job_id' => 'job-1'], 202),
            'parser.test/jobs/job-1' => Http::response(['status' => 'finished', 'result' => $this->finishedResult()]),
        ]);

        $batch = $this->postJson('/api/scan', ['file' => UploadedFile::fake()->create('rc.pdf', 10)])
            ->assertStatus(202)
            ->json('batch_id');

        $this->getJson("/api/scan/{$batch}/status")
            ->assertOk()
            ->assertJson(['done' => true, 'finished' => 1, 'total' => 1]);

        $this->getJson("/api/scan/{$batch}/result")
            ->assertOk()
            ->assertJsonPath('zip', null)
            ->assertJsonPath('items.0.filename', 'rc.pdf')
            ->assertJsonPath('items.0.result.document_type', 'Vehicles');

        $this->assertSame(1, Document::count());
        $this->getJson("/api/scan/{$batch}/result")->assertNotFound();
    }

    public function test_result_is_rejected_while_jobs_are_still_running(): void
    {
        Http::fake([
            'parser.test/jobs' => Http::response(['job_id' => 'job-1'], 202),
            'parser.test/jobs/job-1' => Http::response(['status' => 'queued']),
        ]);

        $batch = $this->postJson('/api/scan', ['file' => UploadedFile::fake()->create('rc.pdf', 10)])->json('batch_id');

        $this->getJson("/api/scan/{$batch}/result")->assertStatus(409)->assertJson(['done' => false]);
        $this->getJson("/api/scan/{$batch}/status")->assertOk()->assertJson(['done' => false]);
    }

    public function test_unknown_batch_is_a_404(): void
    {
        $this->getJson('/api/scan/nope/status')->assertNotFound()->assertJson(['expired' => true]);
        $this->getJson('/api/scan/nope/result')->assertNotFound();
    }

    public function test_scan_requires_a_file(): void
    {
        $this->postJson('/api/scan')->assertStatus(422)->assertJsonValidationErrors('file');
    }

    public function test_scan_reports_an_unreachable_parser_as_503(): void
    {
        Http::fake(fn () => throw new ConnectionException('refused'));

        $this->postJson('/api/scan', ['file' => UploadedFile::fake()->create('rc.pdf', 10)])
            ->assertStatus(503)
            ->assertJsonPath('message', 'Parser service is not reachable. Is FastAPI running?');
    }

    public function test_search_is_available_under_the_api_prefix(): void
    {
        Document::factory()->create(['filename' => 'gst.pdf', 'search_text' => 'gst.pdf company']);

        $this->getJson('/api/search?q=gst')->assertOk()->assertJsonPath('count', 1);
    }

    public function test_any_origin_can_call_the_api_by_default(): void
    {
        $this->call('OPTIONS', '/api/scan', [], [], [], [
            'HTTP_ORIGIN' => 'http://localhost:3000',
            'HTTP_ACCESS_CONTROL_REQUEST_METHOD' => 'POST',
        ])->assertNoContent()->assertHeader('Access-Control-Allow-Origin', '*');

        $this->getJson('/api/search', ['Origin' => 'https://anything.example'])
            ->assertOk()
            ->assertHeader('Access-Control-Allow-Origin', '*');
    }

    public function test_api_requires_the_key(): void
    {
        $this->withHeaders(['X-API-Key' => 'wrong'])->getJson('/api/search')->assertUnauthorized();
        $this->withHeaders(['X-API-Key' => ''])->getJson('/api/search')->assertUnauthorized();
        $this->withHeaders(['X-API-Key' => 'secret'])->getJson('/api/search')->assertOk();
        $this->withHeaders(['X-API-Key' => '', 'Authorization' => 'Bearer secret'])->getJson('/api/search')->assertOk();
    }

    public function test_api_is_closed_when_no_key_is_configured(): void
    {
        config(['services.api.key' => '']);

        $this->getJson('/api/search')->assertStatus(503);
    }

    public function test_parser_calls_carry_the_parser_key(): void
    {
        config(['services.parser.key' => 'parser-secret']);
        Http::fake(['parser.test/jobs' => Http::response(['job_id' => 'job-1'], 202)]);

        $this->postJson('/api/scan', ['file' => UploadedFile::fake()->create('rc.pdf', 10)])->assertStatus(202);

        Http::assertSent(fn ($request) => $request->hasHeader('X-API-Key', 'parser-secret'));
    }
}
