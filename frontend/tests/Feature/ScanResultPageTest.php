<?php

namespace Tests\Feature;

use Tests\TestCase;

class ScanResultPageTest extends TestCase
{
    private function mixedResult(): array
    {
        return [
            'success' => true,
            'document_type' => 'Vehicles',
            'confidence' => 0.21,
            'method' => 'keyword',
            'country' => 'US',
            'keywords_detected' => ['vin', 'license plate'],
            'text_length' => 900,
            'processing_time_ms' => 80,
            'metadata' => ['chassis_number' => '1HGCM82633A004352'],
            'expiry' => ['status' => 'unknown'],
            'categories' => [
                ['category' => 'Vehicles', 'confidence' => 0.21, 'keywords_detected' => ['vin', 'license plate'], 'metadata' => ['chassis_number' => '1HGCM82633A004352']],
                ['category' => 'Company', 'confidence' => 0.16, 'keywords_detected' => ['ein', 'entity type'], 'metadata' => ['ein' => '12-3456789', 'cin' => null]],
                ['category' => 'Equipments', 'confidence' => 0.11, 'keywords_detected' => ['invoice date'], 'metadata' => ['invoice_number' => 'NS-2026-104']],
            ],
        ];
    }

    public function test_a_document_with_several_categories_shows_a_card_for_each(): void
    {
        $this->withSession(['result' => $this->mixedResult(), 'filename' => 'mixed.pdf'])
            ->get(route('scan.index'))
            ->assertOk()
            ->assertSeeInOrder(['Vehicles', '1HGCM82633A004352', 'Company', '12-3456789', 'Equipments', 'NS-2026-104'])
            ->assertSee('Not found');
    }

    public function test_a_result_without_categories_still_shows_its_details(): void
    {
        $result = $this->mixedResult();
        unset($result['categories']);

        $this->withSession(['result' => $result, 'filename' => 'old.pdf'])
            ->get(route('scan.index'))
            ->assertOk()
            ->assertSeeInOrder(['Vehicles', '1HGCM82633A004352']);
    }
}
