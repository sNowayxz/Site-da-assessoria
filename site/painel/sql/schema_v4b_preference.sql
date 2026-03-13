-- ═══════════════════════════════════════════
-- Schema v4b — Adicionar preference_id à tabela pedidos_extensao
-- Rodar DEPOIS do schema_v4_pedidos.sql
-- ═══════════════════════════════════════════

-- Adiciona a coluna preference_id (ID da preferência do Mercado Pago)
ALTER TABLE pedidos_extensao
  ADD COLUMN IF NOT EXISTS preference_id TEXT;

-- Índice para busca por preference_id
CREATE INDEX IF NOT EXISTS idx_pedidos_preference ON pedidos_extensao(preference_id);
