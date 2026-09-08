<?php
declare(strict_types=1);

const PAYFAST_MERCHANT_ID = '34944543';
const PAYFAST_AMOUNT = '140.00';
const PAYFAST_CURRENCY = 'ZAR';
const DELIVERY_ROOT = '/home/liviyo/private_book_delivery';
const DELIVERY_LOG = '/home/liviyo/private_book_delivery/payments.jsonl';
const TOKEN_STORE = '/home/liviyo/private_book_delivery/download-tokens.json';
const DOWNLOAD_SECRET_ENV = 'RENAISSANCE_DOWNLOAD_SECRET';

function delivery_configured(): bool
{
    return is_dir(DELIVERY_ROOT) && is_readable(DELIVERY_ROOT) && getenv(DOWNLOAD_SECRET_ENV) !== false;
}

function fail_request(int $status, string $message): never
{
    http_response_code($status);
    header('Content-Type: text/plain; charset=UTF-8');
    exit($message);
}

function valid_payment_id(string $paymentId): bool
{
    return (bool) preg_match('/^[a-zA-Z0-9-]{8,80}$/', $paymentId);
}

function read_payment(string $paymentId): ?array
{
    if (!is_readable(DELIVERY_LOG)) return null;
    $handle = fopen(DELIVERY_LOG, 'rb');
    if (!$handle) return null;
    while (($line = fgets($handle)) !== false) {
        $record = json_decode($line, true);
        if (is_array($record) && ($record['m_payment_id'] ?? '') === $paymentId) {
            fclose($handle);
            return $record;
        }
    }
    fclose($handle);
    return null;
}

function append_payment(array $record): void
{
    if (!is_dir(DELIVERY_ROOT)) mkdir(DELIVERY_ROOT, 0700, true);
    file_put_contents(DELIVERY_LOG, json_encode($record, JSON_UNESCAPED_SLASHES) . PHP_EOL, FILE_APPEND | LOCK_EX);
}

function issue_download_token(string $paymentId): ?string
{
    $secret = getenv(DOWNLOAD_SECRET_ENV);
    if ($secret === false || $secret === '') return null;
    $handle = fopen(TOKEN_STORE, 'c+');
    if (!$handle || !flock($handle, LOCK_EX)) return null;
    $contents = stream_get_contents($handle);
    $tokens = json_decode($contents ?: '{}', true);
    if (!is_array($tokens)) $tokens = [];
    foreach ($tokens as $token => $record) {
        if (is_array($record) && ($record['payment_id'] ?? '') === $paymentId && empty($record['used'])) {
            flock($handle, LOCK_UN);
            fclose($handle);
            return (string) $token;
        }
    }
    $token = hash_hmac('sha256', $paymentId . '|' . bin2hex(random_bytes(16)), $secret);
    $tokens[$token] = ['payment_id' => $paymentId, 'used' => false, 'created_at' => time()];
    ftruncate($handle, 0);
    rewind($handle);
    fwrite($handle, json_encode($tokens, JSON_UNESCAPED_SLASHES));
    fflush($handle);
    flock($handle, LOCK_UN);
    fclose($handle);
    return $token;
}

function consume_download_token(string $token): ?string
{
    $secret = getenv(DOWNLOAD_SECRET_ENV);
    if ($secret === false || $secret === '' || !preg_match('/^[a-f0-9]{64}$/', $token)) return null;
    $handle = fopen(TOKEN_STORE, 'c+');
    if (!$handle || !flock($handle, LOCK_EX)) return null;
    $contents = stream_get_contents($handle);
    $tokens = json_decode($contents ?: '{}', true);
    $record = is_array($tokens) ? ($tokens[$token] ?? null) : null;
    if (!is_array($record) || !empty($record['used']) || (int) ($record['created_at'] ?? 0) < time() - 86400) {
        flock($handle, LOCK_UN);
        fclose($handle);
        return null;
    }
    $record['used'] = true;
    $tokens[$token] = $record;
    ftruncate($handle, 0);
    rewind($handle);
    fwrite($handle, json_encode($tokens, JSON_UNESCAPED_SLASHES));
    fflush($handle);
    flock($handle, LOCK_UN);
    fclose($handle);
    return (string) ($record['payment_id'] ?? '');
}