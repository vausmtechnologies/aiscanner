<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('documents', function (Blueprint $table) {
            $table->id();
            $table->string('filename');
            $table->string('document_type')->nullable();
            $table->string('country')->nullable();
            $table->float('confidence')->default(0);
            $table->string('expiry_status')->default('unknown');
            $table->date('expiry_date')->nullable();
            $table->json('metadata')->nullable();
            $table->json('keywords')->nullable();
            $table->json('result')->nullable();
            $table->text('search_text');
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('documents');
    }
};
