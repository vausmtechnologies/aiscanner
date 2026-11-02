<?php

namespace Tests\Feature;

use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class TrainingTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        config(['services.parser.url' => 'http://parser.test', 'services.parser.key' => 'secret', 'services.app.password' => '']);
    }

    private function category(string $name, string $kind, array $extra = []): array
    {
        return array_merge(['name' => $name, 'kind' => $kind, 'documents' => 0, 'trained_documents' => 0, 'keywords' => ['alpha', 'beta'], 'trained_keywords' => []], $extra);
    }

    public function test_lists_built_in_trained_and_auto_categories(): void
    {
        Http::fake(['parser.test/categories' => Http::response(['categories' => [
            $this->category('Vehicles', 'built-in'),
            $this->category('Medical Prescription', 'trained', ['trained_documents' => 3, 'trained_keywords' => ['alpha']]),
            $this->category('Lease Agreement', 'auto', ['documents' => 2]),
        ]])]);

        $this->get(route('train.index'))
            ->assertOk()
            ->assertSeeInOrder(['Vehicles', 'built-in', 'Medical Prescription', 'trained', 'Lease Agreement', 'auto-created', 'Confirm']);
    }

    public function test_shows_an_error_when_the_parser_is_down(): void
    {
        Http::fake(['parser.test/*' => Http::response([], 500)]);

        $this->get(route('train.index'))->assertOk()->assertSee('Parser returned an error');
    }

    public function test_training_sends_every_file_with_the_category_name(): void
    {
        Http::fake([
            'parser.test/train' => Http::response(['success' => true, 'category' => 'Medical Prescription', 'trained_documents' => 2, 'files' => [
                ['filename' => 'a.txt', 'ok' => true], ['filename' => 'b.txt', 'ok' => true],
            ]]),
            'parser.test/categories' => Http::response(['categories' => []]),
        ]);

        $this->post(route('train.store'), [
            'category' => 'Medical Prescription',
            'files' => [UploadedFile::fake()->createWithContent('a.txt', 'sample one'), UploadedFile::fake()->createWithContent('b.txt', 'sample two')],
        ])->assertRedirect(route('train.index'))->assertSessionHas('trained.trained_documents', 2);

        Http::assertSent(fn ($request) => $request->url() === 'http://parser.test/train'
            && $request->hasHeader('X-API-Key', 'secret')
            && collect($request->data())->where('name', 'files')->count() === 2
            && collect($request->data())->firstWhere('name', 'category')['contents'] === 'Medical Prescription');
    }

    public function test_rejects_bad_category_names_and_missing_files(): void
    {
        Http::fake();

        $this->post(route('train.store'), ['category' => '<b>x</b>', 'files' => [UploadedFile::fake()->create('a.txt', 1)]])
            ->assertSessionHasErrors('category');
        $this->post(route('train.store'), ['category' => 'Valid Name'])->assertSessionHasErrors('files');
        Http::assertNothingSent();
    }

    public function test_unsupported_files_are_not_sent(): void
    {
        Http::fake();

        $this->post(route('train.store'), ['category' => 'Valid Name', 'files' => [UploadedFile::fake()->create('virus.exe', 1)]])
            ->assertSessionHasErrors('files');
        Http::assertNothingSent();
    }

    public function test_can_confirm_an_auto_category_and_delete_a_trained_one(): void
    {
        Http::fake([
            'parser.test/categories/Lease%20Agreement/promote' => Http::response(['success' => true, 'category' => ['name' => 'Lease']]),
            'parser.test/categories/Medical%20Prescription' => Http::response(['success' => true]),
        ]);

        $this->post(route('train.promote', 'Lease Agreement'), ['name' => 'Lease'])
            ->assertRedirect(route('train.index'))->assertSessionHas('status', 'Saved "Lease" as a trained category.');
        $this->delete(route('train.destroy', 'Medical Prescription'))->assertRedirect(route('train.index'));

        Http::assertSent(fn ($r) => $r->method() === 'DELETE' && str_ends_with($r->url(), '/categories/Medical%20Prescription'));
    }
}
