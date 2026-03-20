-- ═══════════════════════════════════════════
-- Migration: Tabela atividade_arquivos + Storage bucket
-- Execute no Supabase SQL Editor
-- ═══════════════════════════════════════════

-- 1. Criar tabela de metadados de arquivos
CREATE TABLE IF NOT EXISTS atividade_arquivos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  atividade_id UUID NOT NULL REFERENCES atividades(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  tamanho BIGINT DEFAULT 0,
  tipo TEXT DEFAULT 'application/octet-stream',
  url TEXT NOT NULL,
  path TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_atividade_arquivos_atividade ON atividade_arquivos(atividade_id);

-- 2. Habilitar RLS
ALTER TABLE atividade_arquivos ENABLE ROW LEVEL SECURITY;

-- 3. Política de acesso (mesma lógica das outras tabelas)
CREATE POLICY "Acesso total para autenticados" ON atividade_arquivos
  FOR ALL USING (auth.role() = 'authenticated');

-- 4. Criar bucket de storage (executar via API ou Dashboard do Supabase)
-- No Dashboard: Storage > New Bucket > Nome: "arquivos" > Public: ON
-- Ou via SQL:
INSERT INTO storage.buckets (id, name, public) VALUES ('arquivos', 'arquivos', true)
ON CONFLICT (id) DO NOTHING;

-- 5. Política de storage (permitir upload/download para autenticados)
CREATE POLICY "Upload arquivos autenticados" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'arquivos' AND auth.role() = 'authenticated');

CREATE POLICY "Download arquivos publico" ON storage.objects
  FOR SELECT USING (bucket_id = 'arquivos');

CREATE POLICY "Delete arquivos autenticados" ON storage.objects
  FOR DELETE USING (bucket_id = 'arquivos' AND auth.role() = 'authenticated');

-- 6. Corrigir constraint alunos_tipo_check
-- Primeiro normalizar dados existentes que podem ter valores antigos
UPDATE alunos SET tipo = 'mensalista' WHERE tipo NOT IN ('avulso', 'mensalista');
-- Dropar e recriar o constraint
ALTER TABLE alunos DROP CONSTRAINT IF EXISTS alunos_tipo_check;
ALTER TABLE alunos ADD CONSTRAINT alunos_tipo_check CHECK (tipo IN ('avulso', 'mensalista'));
