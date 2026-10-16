<?php

namespace Database\Factories;

use App\Models\Document;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Document>
 */
class DocumentFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $type = fake()->randomElement(['Vehicles', 'Company', 'Equipments', 'People']);
        $filename = fake()->word().'.pdf';
        $metadata = ['registration_number' => strtoupper(fake()->bothify('??##??####'))];

        return [
            'filename' => $filename,
            'document_type' => $type,
            'country' => 'India',
            'confidence' => 0.6,
            'expiry_status' => 'valid',
            'expiry_date' => now()->addYear()->toDateString(),
            'metadata' => $metadata,
            'keywords' => [],
            'result' => ['document_type' => $type, 'metadata' => $metadata],
            'search_text' => strtolower($filename.' '.$type.' '.implode(' ', $metadata)),
        ];
    }
}
