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

-- Solicitacoes: anon pode ver solicitações (para Área do Aluno acompanhar extensão)
DO $$ BEGIN
  CREATE POLICY "Anon pode ver solicitacoes" ON solicitacoes FOR SELECT TO anon USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Solicitacoes: anon pode inserir (pedido de extensão pelo site)
DO $$ BEGIN
  CREATE POLICY "Anon pode inserir solicitacao" ON solicitacoes FOR INSERT TO anon WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Pedidos Extensao: anon pode inserir (formulário do site)
DO $$ BEGIN
  CREATE POLICY "Anon pode inserir pedido_extensao" ON pedidos_extensao FOR INSERT TO anon WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Pedidos Extensao: anon pode ver (para página de status)
DO $$ BEGIN
  CREATE POLICY "Anon pode ver pedidos_extensao" ON pedidos_extensao FOR SELECT TO anon USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
