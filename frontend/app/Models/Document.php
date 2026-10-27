<?php

namespace App\Models;

use Carbon\Carbon;
use Database\Factories\DocumentFactory;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Str;

class Document extends Model
{
    /** @use HasFactory<DocumentFactory> */
    use HasFactory;

    protected $fillable = [
        'filename', 'document_type', 'country', 'confidence', 'expiry_status',
        'expiry_date', 'metadata', 'keywords', 'result', 'search_text',
    ];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'metadata' => 'array',
            'keywords' => 'array',
            'result' => 'array',
            'confidence' => 'float',
            'expiry_date' => 'date',
        ];
    }

    /**
     * Save a parser result so it can be found by keyword search later.
     *
     * @param  array<string, mixed>  $result
     */
    public static function storeScan(string $filename, array $result): self
    {
        $metadata = $result['metadata'] ?? [];
        $keywords = $result['keywords_detected'] ?? [];
        $expiry = $result['expiry'] ?? [];

        $searchText = Str::lower(implode(' ', array_filter([
            $filename,
            $result['document_type'] ?? null,
            $result['country'] ?? null,
            $expiry['status'] ?? null,
            $expiry['expiry_date'] ?? null,
            implode(' ', array_keys($metadata)),
            implode(' ', array_filter($metadata)),
            collect($result['categories'] ?? [])->map(fn ($section) => $section['category'].' '.implode(' ', array_filter($section['metadata'] ?? [])))->implode(' '),
            implode(' ', $keywords),
        ])));

        // Re-scanning the same file updates its entry instead of adding a duplicate.
        $document = self::firstOrNew(['filename' => $filename]);
        $document->fill([
            'document_type' => $result['document_type'] ?? null,
            'country' => $result['country'] ?? null,
            'confidence' => (float) ($result['confidence'] ?? 0),
            'expiry_status' => $expiry['status'] ?? 'unknown',
            'expiry_date' => self::parseDate($expiry['expiry_date'] ?? null),
            'metadata' => $metadata,
            'keywords' => $keywords,
            'result' => $result,
            'search_text' => $searchText,
        ]);
        $document->save();
        $document->touch();

        return $document;
    }

    /**
     * Every word typed must appear somewhere in the document (AND match).
     *
     * @param  Builder<Document>  $query
     * @return Builder<Document>
     */
    public function scopeMatching(Builder $query, string $term): Builder
    {
        foreach (preg_split('/\s+/', Str::lower(trim($term)), -1, PREG_SPLIT_NO_EMPTY) as $word) {
            $escaped = addcslashes($word, '%_\\');
            $query->whereRaw("search_text LIKE ? ESCAPE '\\'", ['%'.$escaped.'%']);
        }

        return $query;
    }

    private static function parseDate(?string $value): ?string
    {
        if (! $value) {
            return null;
        }

        try {
            return Carbon::parse($value)->toDateString();
        } catch (\Throwable) {
            return null;
        }
    }
}
