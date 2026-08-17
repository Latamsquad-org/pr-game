<?php
declare(strict_types=1);

/**
 * ACL: quien puede borrar partidas del tracker (ademas de ser staff).
 * Owner fijo siempre puede; el resto solo si esta en delete-acl.json.
 */

/**
 * Discord ID del owner (Chaziz). Unico que administra la ACL.
 */
function delete_acl_owner_id(): string
{
    return '357055203348054027';
}

/**
 * True si el Discord ID es el owner.
 */
function delete_acl_is_owner(?string $discordId): bool
{
    return $discordId !== null && $discordId !== '' && hash_equals(delete_acl_owner_id(), $discordId);
}

/**
 * Path al JSON de ACL (bajo admin/data/, denegado por nginx).
 */
function delete_acl_path(): string
{
    return dirname(__DIR__) . '/data/delete-acl.json';
}

/**
 * @return array{can_delete: list<array{id: string, label: string}>}
 */
function delete_acl_defaults(): array
{
    return ['can_delete' => []];
}

/**
 * Normaliza lista can_delete desde input crudo.
 *
 * @param mixed $raw
 * @return array{ok: bool, entries: list<array{id: string, label: string}>, errors: list<string>}
 */
function delete_acl_normalize_entries($raw): array
{
    $errors = [];
    $entries = [];
    $seen = [];
    if ($raw === null) {
        return ['ok' => true, 'entries' => [], 'errors' => []];
    }
    if (!is_array($raw)) {
        return ['ok' => false, 'entries' => [], 'errors' => ['can_delete invalido']];
    }
    foreach ($raw as $row) {
        $id = '';
        $label = '';
        if (is_string($row) || is_int($row)) {
            $id = preg_replace('/\D+/', '', (string) $row);
        } elseif (is_array($row)) {
            $id = preg_replace('/\D+/', '', (string) ($row['id'] ?? ''));
            $label = trim((string) ($row['label'] ?? ''));
        } else {
            $errors[] = 'entrada invalida en can_delete';
            continue;
        }
        if ($id === '' || strlen($id) < 5 || strlen($id) > 32) {
            $errors[] = 'Discord ID invalido';
            continue;
        }
        if (isset($seen[$id])) {
            continue;
        }
        // Owner no se guarda en la lista (ya tiene poder fijo)
        if (hash_equals(delete_acl_owner_id(), $id)) {
            continue;
        }
        if (strlen($label) > 64) {
            $label = substr($label, 0, 64);
        }
        $seen[$id] = true;
        $entries[] = ['id' => $id, 'label' => $label];
    }
    return ['ok' => $errors === [], 'entries' => $entries, 'errors' => $errors];
}

/**
 * @return array{can_delete: list<array{id: string, label: string}>}
 */
function delete_acl_load(): array
{
    $defaults = delete_acl_defaults();
    $path = delete_acl_path();
    if (!is_file($path)) {
        return $defaults;
    }
    $raw = file_get_contents($path);
    $data = json_decode(is_string($raw) ? $raw : '', true);
    if (!is_array($data)) {
        return $defaults;
    }
    $norm = delete_acl_normalize_entries($data['can_delete'] ?? []);
    return ['can_delete' => $norm['entries']];
}

/**
 * @param array{can_delete: list<array{id: string, label: string}>} $settings
 */
function delete_acl_save(array $settings): void
{
    $norm = delete_acl_normalize_entries($settings['can_delete'] ?? []);
    if (!$norm['ok']) {
        throw new RuntimeException(implode('; ', $norm['errors']));
    }
    $dir = dirname(delete_acl_path());
    if (!is_dir($dir) && !mkdir($dir, 0755, true) && !is_dir($dir)) {
        throw new RuntimeException('No se pudo crear admin/data');
    }
    $payload = json_encode(
        ['can_delete' => $norm['entries']],
        JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE
    );
    if ($payload === false) {
        throw new RuntimeException('JSON encode fallo');
    }
    $tmp = delete_acl_path() . '.tmp';
    if (file_put_contents($tmp, $payload . "\n", LOCK_EX) === false) {
        throw new RuntimeException('No se pudo escribir ACL temporal');
    }
    if (!rename($tmp, delete_acl_path())) {
        @unlink($tmp);
        throw new RuntimeException('No se pudo guardar ACL');
    }
}

/**
 * True si este Discord ID puede borrar partidas (owner o whitelist).
 */
function delete_acl_can_delete(?string $discordId): bool
{
    if ($discordId === null || $discordId === '') {
        return false;
    }
    if (delete_acl_is_owner($discordId)) {
        return true;
    }
    $settings = delete_acl_load();
    foreach ($settings['can_delete'] as $row) {
        if (hash_equals($row['id'], $discordId)) {
            return true;
        }
    }
    return false;
}

/**
 * Agrega un Discord ID a la whitelist.
 *
 * @return array{ok: bool, settings: array{can_delete: list<array{id: string, label: string}>}, error: string}
 */
function delete_acl_grant(string $discordId, string $label = ''): array
{
    $settings = delete_acl_load();
    $id = preg_replace('/\D+/', '', $discordId);
    $label = trim($label);
    if ($id === '' || strlen($id) < 5 || strlen($id) > 32) {
        return ['ok' => false, 'settings' => $settings, 'error' => 'Discord ID invalido'];
    }
    if (hash_equals(delete_acl_owner_id(), $id)) {
        return ['ok' => false, 'settings' => $settings, 'error' => 'El owner ya tiene permiso fijo'];
    }
    foreach ($settings['can_delete'] as $row) {
        if (hash_equals($row['id'], $id)) {
            return ['ok' => false, 'settings' => $settings, 'error' => 'Ese ID ya tiene permiso'];
        }
    }
    if (strlen($label) > 64) {
        $label = substr($label, 0, 64);
    }
    $settings['can_delete'][] = ['id' => $id, 'label' => $label];
    delete_acl_save($settings);
    return ['ok' => true, 'settings' => delete_acl_load(), 'error' => ''];
}

/**
 * Quita un Discord ID de la whitelist.
 *
 * @return array{ok: bool, settings: array{can_delete: list<array{id: string, label: string}>}, error: string}
 */
function delete_acl_revoke(string $discordId): array
{
    $settings = delete_acl_load();
    $id = preg_replace('/\D+/', '', $discordId);
    if ($id === '') {
        return ['ok' => false, 'settings' => $settings, 'error' => 'Discord ID invalido'];
    }
    $next = [];
    $found = false;
    foreach ($settings['can_delete'] as $row) {
        if (hash_equals($row['id'], $id)) {
            $found = true;
            continue;
        }
        $next[] = $row;
    }
    if (!$found) {
        return ['ok' => false, 'settings' => $settings, 'error' => 'ID no estaba en la lista'];
    }
    $settings['can_delete'] = $next;
    delete_acl_save($settings);
    return ['ok' => true, 'settings' => delete_acl_load(), 'error' => ''];
}
