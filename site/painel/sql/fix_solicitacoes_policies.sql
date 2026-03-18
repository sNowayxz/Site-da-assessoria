-- ═══════════════════════════════════════════
-- FIX: Policies para solicitacoes + colunas faltantes
-- Rodar no Supabase SQL Editor
-- ═══════════════════════════════════════════

-- 1. Adicionar colunas faltantes em solicitacoes
ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS horas_validadas INTEGER DEFAULT 0;
ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS horas_a_validar INTEGER DEFAULT 0;
ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS origem TEXT DEFAULT 'assessoria';

-- 2. Adicionar coluna avatar_url em assessores
ALTER TABLE assessores ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- 3. Atualizar constraint de role para incluir novos roles
ALTER TABLE assessores DROP CONSTRAINT IF EXISTS assessores_role_check;
ALTER TABLE assessores ADD CONSTRAINT assessores_role_check
  CHECK (role IN ('admin', 'dono', 'extensao', 'assessoria', 'assessor', 'visualizador'));

-- 4. Atualizar funções helper para novos roles
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT AS $$
  SELECT role FROM public.assessores WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.assessores
    WHERE id = auth.uid() AND role IN ('admin', 'dono')
  );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 5. Habilitar RLS na tabela solicitacoes (caso não esteja)
ALTER TABLE solicitacoes ENABLE ROW LEVEL SECURITY;

-- 6. POLICIES — SOLICITACOES

-- Anon pode ver (para Área do Aluno consultar por RA)
DROP POLICY IF EXISTS "Anon pode ver solicitacoes" ON solicitacoes;
CREATE POLICY "Anon pode ver solicitacoes"
  ON solicitacoes FOR SELECT TO anon USING (true);

-- Anon pode inserir (para formulário de extensão no site)
DROP POLICY IF EXISTS "Anon pode inserir solicitacao" ON solicitacoes;
CREATE POLICY "Anon pode inserir solicitacao"
  ON solicitacoes FOR INSERT TO anon WITH CHECK (true);

-- Auth: admin/dono/extensao veem tudo, assessoria vê só suas
DROP POLICY IF EXISTS "Role-based select solicitacoes" ON solicitacoes;
CREATE POLICY "Role-based select solicitacoes"
  ON solicitacoes FOR SELECT TO authenticated
  USING (
    get_user_role() IN ('admin', 'dono', 'extensao')
    OR (get_user_role() = 'assessoria' AND assessor_id = auth.uid())
  );

-- Auth: assessoria pode inserir (com assessor_id = próprio)
DROP POLICY IF EXISTS "Role-based insert solicitacoes" ON solicitacoes;
CREATE POLICY "Role-based insert solicitacoes"
  ON solicitacoes FOR INSERT TO authenticated
  WITH CHECK (
    get_user_role() IN ('admin', 'dono', 'extensao', 'assessoria')
  );

-- Auth: admin/dono/extensao podem editar qualquer, assessoria só suas
DROP POLICY IF EXISTS "Role-based update solicitacoes" ON solicitacoes;
CREATE POLICY "Role-based update solicitacoes"
  ON solicitacoes FOR UPDATE TO authenticated
  USING (
    get_user_role() IN ('admin', 'dono', 'extensao')
    OR (get_user_role() = 'assessoria' AND assessor_id = auth.uid())
  );

-- Auth: só admin/dono podem deletar
DROP POLICY IF EXISTS "Role-based delete solicitacoes" ON solicitacoes;
CREATE POLICY "Role-based delete solicitacoes"
  ON solicitacoes FOR DELETE TO authenticated
  USING (get_user_role() IN ('admin', 'dono'));

-- 7. POLICIES — PEDIDOS EXTENSAO (garantir anon access)

-- Habilitar RLS
ALTER TABLE pedidos_extensao ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anon pode inserir pedido_extensao" ON pedidos_extensao;
CREATE POLICY "Anon pode inserir pedido_extensao"
  ON pedidos_extensao FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "Anon pode ver pedidos_extensao" ON pedidos_extensao;
CREATE POLICY "Anon pode ver pedidos_extensao"
  ON pedidos_extensao FOR SELECT TO anon USING (true);

-- 8. Atualizar horas_a_validar para registros existentes
UPDATE solicitacoes SET horas_a_validar = GREATEST(0, horas - COALESCE(horas_validadas, 0))
WHERE horas_a_validar IS NULL OR horas_a_validar = 0;

-- 9. Marcar registros sem origem como 'assessoria'
UPDATE solicitacoes SET origem = 'assessoria' WHERE origem IS NULL;
