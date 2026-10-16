<?php

namespace Tests\Feature;

use App\Models\Document;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class DocumentSearchTest extends TestCase
{
    use RefreshDatabase;

    public function test_finds_documents_by_any_stored_keyword(): void
    {
        Document::storeScan('rc-book.pdf', [
            'document_type' => 'Vehicles',
            'country' => 'India',
            'metadata' => ['registration_number' => 'MH12AB1234'],
            'keywords_detected' => ['registration certificate'],
            'expiry' => ['status' => 'valid', 'expiry_date' => '2030-01-31'],
        ]);
        Document::factory()->create(['filename' => 'gst.pdf', 'search_text' => 'gst.pdf company']);

        $this->getJson(route('scan.search', ['q' => 'mh12ab']))
            ->assertOk()
            ->assertJsonPath('count', 1)
            ->assertJsonPath('documents.0.filename', 'rc-book.pdf')
            ->assertJsonPath('documents.0.expiry_date', '2030-01-31');

        $this->getJson(route('scan.search', ['q' => 'vehicles india']))->assertJsonPath('count', 1);
        $this->getJson(route('scan.search', ['q' => 'nothing-here']))->assertJsonPath('count', 0);
    }

    public function test_lists_latest_documents_when_search_is_empty(): void
    {
        Document::factory()->count(3)->create();

        $this->getJson(route('scan.search'))->assertOk()->assertJsonPath('count', 3);
    }

    public function test_like_wildcards_are_treated_as_plain_text(): void
    {
        Document::factory()->create(['search_text' => 'invoice 100% paid']);
        Document::factory()->create(['search_text' => 'invoice unpaid']);

        $this->getJson(route('scan.search', ['q' => '%']))->assertJsonPath('count', 1);
    }

    public function test_rescanning_the_same_file_updates_instead_of_duplicating(): void
    {
        Document::storeScan('rc.pdf', ['document_type' => 'Vehicles', 'metadata' => ['fuel' => 'Petrol']]);
        Document::storeScan('rc.pdf', ['document_type' => 'Vehicles', 'metadata' => ['fuel' => 'Diesel']]);

        $this->assertSame(1, Document::count());
        $this->getJson(route('scan.search', ['q' => 'diesel']))->assertJsonPath('count', 1);
        $this->getJson(route('scan.search', ['q' => 'petrol']))->assertJsonPath('count', 0);
    }

    public function test_filters_by_type_and_expiry_status(): void
    {
        Document::factory()->create(['document_type' => 'Vehicles', 'expiry_status' => 'valid']);
        Document::factory()->create(['document_type' => 'Vehicles', 'expiry_status' => 'expired']);
        Document::factory()->create(['document_type' => null, 'expiry_status' => 'unknown']);

        $this->getJson(route('scan.search', ['type' => 'Vehicles']))->assertJsonPath('count', 2);
        $this->getJson(route('scan.search', ['type' => 'Vehicles', 'status' => 'expired']))->assertJsonPath('count', 1);
        $this->getJson(route('scan.search', ['type' => 'unknown']))->assertJsonPath('count', 1);
        $this->getJson(route('scan.search'))->assertJsonPath('types.Vehicles', 2);
    }
}
