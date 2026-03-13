-- ═══════════════════════════════════════════
-- Schema v3 — Studeo Sync (Rastreio)
-- Rodar no SQL Editor do Supabase
-- ═══════════════════════════════════════════

-- Adicionar campo de senha do Studeo na tabela alunos
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS studeo_senha TEXT;

-- Tabela de sincronização do Studeo
CREATE TABLE IF NOT EXISTS studeo_sync (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  aluno_id UUID REFERENCES alunos(id) ON DELETE CASCADE,
  disciplina TEXT NOT NULL,
  cd_shortname TEXT NOT NULL,
  ano TEXT,
  modulo TEXT,
  atividade TEXT NOT NULL,
  tipo_atividade TEXT DEFAULT 'AV',
  data_inicial TIMESTAMPTZ,
  data_final TIMESTAMPTZ,
  respondida BOOLEAN DEFAULT FALSE,
  synced_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(aluno_id, cd_shortname, atividade)
);

-- Índices para consultas rápidas
CREATE INDEX IF NOT EXISTS idx_studeo_sync_aluno ON studeo_sync(aluno_id);
CREATE INDEX IF NOT EXISTS idx_studeo_sync_respondida ON studeo_sync(respondida);

-- RLS para studeo_sync
ALTER TABLE studeo_sync ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read studeo_sync"
  ON studeo_sync FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert studeo_sync"
  ON studeo_sync FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update studeo_sync"
  ON studeo_sync FOR UPDATE
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can delete studeo_sync"
  ON studeo_sync FOR DELETE
  TO authenticated
  USING (true);
