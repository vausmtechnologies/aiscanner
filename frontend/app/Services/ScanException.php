<?php

namespace App\Services;

use RuntimeException;

/** A scan could not be started; the message is safe to show to the user. */
class ScanException extends RuntimeException
{
    public function __construct(string $message, public readonly int $status = 422)
    {
        parent::__construct($message);
    }
}
