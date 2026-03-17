-- ═══════════════════════════════════════════
-- Schema v6: Sistema de Roles e Permissões
-- ═══════════════════════════════════════════
-- Rodar no Supabase SQL Editor APÓS o schema_COMPLETO.sql

-- 1. Adicionar 'visualizador' ao CHECK constraint
ALTER TABLE assessores DROP CONSTRAINT IF EXISTS assessores_role_check;
ALTER TABLE assessores ADD CONSTRAINT assessores_role_check
  CHECK (role IN ('admin', 'assessor', 'visualizador'));

-- 2. Função helper: retorna role do user logado
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT AS $$
  SELECT role FROM public.assessores WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 3. Função helper: verifica se user é admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
  SELECT EXISTS (SELECT 1 FROM public.assessores WHERE id = auth.uid() AND role = 'admin');
$$ LANGUAGE sql SECURITY DEFINER STABLE;


-- ═══════════════════════════════════════════
-- 4. NOVAS POLICIES — ASSESSORES
-- ═══════════════════════════════════════════

-- Remover policies antigas de assessores
DROP POLICY IF EXISTS "Assessores podem ver assessores" ON assessores;

-- Todos autenticados podem ver assessores (necessário para lookup de nomes)
CREATE POLICY "Auth pode ver assessores"
  ON assessores FOR SELECT TO authenticated
  USING (true);

-- Só admin pode inserir assessores
DROP POLICY IF EXISTS "Admin pode inserir assessores" ON assessores;
CREATE POLICY "Admin pode inserir assessores"
  ON assessores FOR INSERT TO authenticated
  WITH CHECK (is_admin());

-- Só admin pode editar assessores (ou o próprio user pode editar seu nome)
DROP POLICY IF EXISTS "Admin pode editar assessores" ON assessores;
CREATE POLICY "Admin pode editar assessores"
  ON assessores FOR UPDATE TO authenticated
  USING (is_admin() OR id = auth.uid());

-- Só admin pode deletar assessores
DROP POLICY IF EXISTS "Admin pode deletar assessores" ON assessores;
CREATE POLICY "Admin pode deletar assessores"
  ON assessores FOR DELETE TO authenticated
  USING (is_admin());


-- ═══════════════════════════════════════════
-- 5. NOVAS POLICIES — ALUNOS
-- ═══════════════════════════════════════════

DROP POLICY IF EXISTS "Assessores podem ver alunos" ON alunos;
DROP POLICY IF EXISTS "Assessores podem inserir alunos" ON alunos;
DROP POLICY IF EXISTS "Assessores podem editar alunos" ON alunos;
DROP POLICY IF EXISTS "Assessores podem deletar alunos" ON alunos;

-- SELECT: admin vê tudo, assessor vê só os seus, visualizador vê tudo (readonly)
CREATE POLICY "Role-based select alunos"
  ON alunos FOR SELECT TO authenticated
  USING (
    get_user_role() IN ('admin', 'visualizador')
    OR (get_user_role() = 'assessor' AND assessor_id = auth.uid())
  );

-- INSERT: admin e assessor podem criar
CREATE POLICY "Role-based insert alunos"
  ON alunos FOR INSERT TO authenticated
  WITH CHECK (get_user_role() IN ('admin', 'assessor'));

-- UPDATE: admin pode editar qualquer, assessor só os seus
CREATE POLICY "Role-based update alunos"
  ON alunos FOR UPDATE TO authenticated
  USING (
    get_user_role() = 'admin'
    OR (get_user_role() = 'assessor' AND assessor_id = auth.uid())
  );

-- DELETE: só admin
CREATE POLICY "Only admin delete alunos"
  ON alunos FOR DELETE TO authenticated
  USING (is_admin());


-- ═══════════════════════════════════════════
-- 6. NOVAS POLICIES — ATIVIDADES
-- ═══════════════════════════════════════════

DROP POLICY IF EXISTS "Assessores podem ver atividades" ON atividades;
DROP POLICY IF EXISTS "Assessores podem inserir atividades" ON atividades;
DROP POLICY IF EXISTS "Assessores podem editar atividades" ON atividades;
DROP POLICY IF EXISTS "Assessores podem deletar atividades" ON atividades;

CREATE POLICY "Role-based select atividades"
  ON atividades FOR SELECT TO authenticated
  USING (
    get_user_role() IN ('admin', 'visualizador')
    OR (get_user_role() = 'assessor' AND assessor_id = auth.uid())
  );

CREATE POLICY "Role-based insert atividades"
  ON atividades FOR INSERT TO authenticated
  WITH CHECK (get_user_role() IN ('admin', 'assessor'));

CREATE POLICY "Role-based update atividades"
  ON atividades FOR UPDATE TO authenticated
  USING (
    get_user_role() = 'admin'
    OR (get_user_role() = 'assessor' AND assessor_id = auth.uid())
  );

CREATE POLICY "Only admin delete atividades"
  ON atividades FOR DELETE TO authenticated
  USING (is_admin());


-- ═══════════════════════════════════════════
-- 7. NOVAS POLICIES — PAGAMENTOS (só admin)
-- ═══════════════════════════════════════════

DROP POLICY IF EXISTS "Auth pode ver pagamentos" ON pagamentos;
DROP POLICY IF EXISTS "Auth pode inserir pagamentos" ON pagamentos;
DROP POLICY IF EXISTS "Auth pode editar pagamentos" ON pagamentos;
DROP POLICY IF EXISTS "Auth pode deletar pagamentos" ON pagamentos;

CREATE POLICY "Only admin select pagamentos"
  ON pagamentos FOR SELECT TO authenticated
  USING (is_admin());

CREATE POLICY "Only admin insert pagamentos"
  ON pagamentos FOR INSERT TO authenticated
  WITH CHECK (is_admin());

CREATE POLICY "Only admin update pagamentos"
  ON pagamentos FOR UPDATE TO authenticated
  USING (is_admin());

CREATE POLICY "Only admin delete pagamentos"
  ON pagamentos FOR DELETE TO authenticated
  USING (is_admin());


-- ═══════════════════════════════════════════
-- 8. NOVAS POLICIES — MÓDULOS (só admin)
-- ═══════════════════════════════════════════

DROP POLICY IF EXISTS "Auth pode ver modulos" ON modulos;
DROP POLICY IF EXISTS "Auth pode inserir modulos" ON modulos;
DROP POLICY IF EXISTS "Auth pode editar modulos" ON modulos;
DROP POLICY IF EXISTS "Auth pode deletar modulos" ON modulos;

CREATE POLICY "Only admin select modulos"
  ON modulos FOR SELECT TO authenticated
  USING (is_admin());

CREATE POLICY "Only admin insert modulos"
  ON modulos FOR INSERT TO authenticated
  WITH CHECK (is_admin());

CREATE POLICY "Only admin update modulos"
  ON modulos FOR UPDATE TO authenticated
  USING (is_admin());

CREATE POLICY "Only admin delete modulos"
  ON modulos FOR DELETE TO authenticated
  USING (is_admin());


-- ═══════════════════════════════════════════
-- 9. NOVAS POLICIES — DISCIPLINAS (só admin)
-- ═══════════════════════════════════════════

DROP POLICY IF EXISTS "Auth pode ver disciplinas" ON disciplinas;
DROP POLICY IF EXISTS "Auth pode inserir disciplinas" ON disciplinas;
DROP POLICY IF EXISTS "Auth pode editar disciplinas" ON disciplinas;
DROP POLICY IF EXISTS "Auth pode deletar disciplinas" ON disciplinas;

CREATE POLICY "Only admin select disciplinas"
  ON disciplinas FOR SELECT TO authenticated
  USING (is_admin());

CREATE POLICY "Only admin insert disciplinas"
  ON disciplinas FOR INSERT TO authenticated
  WITH CHECK (is_admin());

CREATE POLICY "Only admin update disciplinas"
  ON disciplinas FOR UPDATE TO authenticated
  USING (is_admin());

CREATE POLICY "Only admin delete disciplinas"
  ON disciplinas FOR DELETE TO authenticated
  USING (is_admin());


-- ═══════════════════════════════════════════
-- 10. NOVAS POLICIES — STUDEO SYNC (admin + assessor próprios)
-- ═══════════════════════════════════════════

DROP POLICY IF EXISTS "Auth pode ver studeo_sync" ON studeo_sync;
DROP POLICY IF EXISTS "Auth pode inserir studeo_sync" ON studeo_sync;
DROP POLICY IF EXISTS "Auth pode editar studeo_sync" ON studeo_sync;
DROP POLICY IF EXISTS "Auth pode deletar studeo_sync" ON studeo_sync;

CREATE POLICY "Role-based select studeo_sync"
  ON studeo_sync FOR SELECT TO authenticated
  USING (
    is_admin()
    OR EXISTS (
      SELECT 1 FROM alunos WHERE alunos.id = studeo_sync.aluno_id AND alunos.assessor_id = auth.uid()
    )
  );

CREATE POLICY "Role-based insert studeo_sync"
  ON studeo_sync FOR INSERT TO authenticated
  WITH CHECK (get_user_role() IN ('admin', 'assessor'));

CREATE POLICY "Role-based update studeo_sync"
  ON studeo_sync FOR UPDATE TO authenticated
  USING (is_admin());

CREATE POLICY "Only admin delete studeo_sync"
  ON studeo_sync FOR DELETE TO authenticated
  USING (is_admin());


-- ═══════════════════════════════════════════
-- 11. POLICIES — EVENTOS AGENDA (per-user, mantém igual)
-- ═══════════════════════════════════════════
-- eventos_agenda já tem policies por user_id, não precisa alterar


-- ═══════════════════════════════════════════
-- 12. POLICIES — AUDIT LOG (só admin)
-- ═══════════════════════════════════════════

DROP POLICY IF EXISTS "Auth pode ver audit_log" ON audit_log;
DROP POLICY IF EXISTS "Auth pode inserir audit_log" ON audit_log;

CREATE POLICY "Only admin select audit_log"
  ON audit_log FOR SELECT TO authenticated
  USING (is_admin());

-- Todos autenticados podem inserir no audit log
CREATE POLICY "Auth pode inserir audit_log"
  ON audit_log FOR INSERT TO authenticated
  WITH CHECK (true);


-- ═══════════════════════════════════════════
-- 13. POLICIES — NOTIFICAÇÕES (só admin)
-- ═══════════════════════════════════════════

DROP POLICY IF EXISTS "Auth full notificacoes SELECT" ON notificacoes;
DROP POLICY IF EXISTS "Auth full notificacoes INSERT" ON notificacoes;
DROP POLICY IF EXISTS "Auth full notificacoes UPDATE" ON notificacoes;

CREATE POLICY "Only admin select notificacoes"
  ON notificacoes FOR SELECT TO authenticated
  USING (is_admin());

CREATE POLICY "Only admin insert notificacoes"
  ON notificacoes FOR INSERT TO authenticated
  WITH CHECK (is_admin());

CREATE POLICY "Only admin update notificacoes"
  ON notificacoes FOR UPDATE TO authenticated
  USING (is_admin());


-- ═══════════════════════════════════════════
-- NOTA: As policies de pedidos_extensao e depoimentos
-- (anon access) NÃO são alteradas aqui pois já funcionam corretamente.
-- ═══════════════════════════════════════════
