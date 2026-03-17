-- ═══ POLÍTICAS PARA ÁREA DO ALUNO (acesso anon read-only) ═══
-- Cole este SQL no Supabase SQL Editor após o schema principal

-- Alunos: anon pode buscar por RA (apenas SELECT)
DO $$ BEGIN
  CREATE POLICY "Anon pode buscar aluno por RA" ON alunos FOR SELECT TO anon USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Atividades: anon pode ver atividades (filtrado por aluno_id no client)
DO $$ BEGIN
  CREATE POLICY "Anon pode ver atividades" ON atividades FOR SELECT TO anon USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Pagamentos: anon pode ver pagamentos (filtrado por aluno_id no client)
DO $$ BEGIN
  CREATE POLICY "Anon pode ver pagamentos" ON pagamentos FOR SELECT TO anon USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
