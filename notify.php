<?php
declare(strict_types=1);
require __DIR__ . '/payfast-config.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !delivery_configured()) fail_request(404, 'Not found');
$post = $_POST;
$signature = (string) ($post['signature'] ?? '');
unset($post['signature']);
$parts = [];
foreach ($post as $key => $value) $parts[] = urlencode((string) $key) . '=' . urlencode(trim((string) $value));
$signaturePayload = implode('&', $parts);
$passphrase = getenv('PAYFAST_PASSPHRASE') ?: '';
if ($passphrase !== '') $signaturePayload .= '&passphrase=' . urlencode($passphrase);
if (!hash_equals($signature, md5($signaturePayload))) fail_request(400, 'Invalid signature');

$validationHandle = curl_init('https://www.payfast.co.za/eng/query/validate');
curl_setopt_array($validationHandle, [
	CURLOPT_POST => true,
	CURLOPT_POSTFIELDS => http_build_query($_POST),
	CURLOPT_RETURNTRANSFER => true,
	CURLOPT_TIMEOUT => 10,
	CURLOPT_SSL_VERIFYPEER => true,
	CURLOPT_SSL_VERIFYHOST => 2,
]);
$validationResponse = curl_exec($validationHandle);
$validationStatus = curl_getinfo($validationHandle, CURLINFO_HTTP_CODE);
curl_close($validationHandle);
if ($validationResponse !== 'VALID' || $validationStatus !== 200) fail_request(400, 'Payment could not be validated');

$paymentId = (string) ($post['m_payment_id'] ?? '');
$cover = (string) ($post['custom_str1'] ?? '');
$validCovers = ['cover1', 'cover2', 'cover3', 'cover4', 'cover5'];
if (!valid_payment_id($paymentId) || !in_array($cover, $validCovers, true)) fail_request(400, 'Invalid order');
if ((string) ($post['merchant_id'] ?? '') !== PAYFAST_MERCHANT_ID || (string) ($post['amount_gross'] ?? '') !== PAYFAST_AMOUNT || (string) ($post['currency'] ?? '') !== PAYFAST_CURRENCY || (string) ($post['payment_status'] ?? '') !== 'COMPLETE') fail_request(400, 'Payment not complete');

append_payment(['m_payment_id' => $paymentId, 'cover' => $cover, 'payment_status' => 'COMPLETE', 'email' => filter_var($post['email_address'] ?? '', FILTER_VALIDATE_EMAIL) ?: '', 'created_at' => gmdate('c')]);
http_response_code(200);
echo 'OK';