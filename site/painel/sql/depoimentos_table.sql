-- Tabela de depoimentos/avaliações
CREATE TABLE IF NOT EXISTS depoimentos (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  nome TEXT NOT NULL,
  curso TEXT,
  texto TEXT NOT NULL,
  nota INTEGER DEFAULT 5 CHECK (nota >= 1 AND nota <= 5),
  aprovado BOOLEAN DEFAULT false,
  rejeitado BOOLEAN DEFAULT false,
  aprovado_por UUID REFERENCES auth.users(id),
  aprovado_em TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS
ALTER TABLE depoimentos ENABLE ROW LEVEL SECURITY;

-- Anon: pode ler aprovados e inserir novos
DROP POLICY IF EXISTS "anon_select_depoimentos" ON depoimentos;
CREATE POLICY "anon_select_depoimentos" ON depoimentos
  FOR SELECT TO anon USING (aprovado = true);

DROP POLICY IF EXISTS "anon_insert_depoimentos" ON depoimentos;
CREATE POLICY "anon_insert_depoimentos" ON depoimentos
  FOR INSERT TO anon WITH CHECK (aprovado = false);

-- Authenticated: admin/dono veem todos, podem atualizar e deletar
DROP POLICY IF EXISTS "auth_select_depoimentos" ON depoimentos;
CREATE POLICY "auth_select_depoimentos" ON depoimentos
  FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "auth_update_depoimentos" ON depoimentos;
CREATE POLICY "auth_update_depoimentos" ON depoimentos
  FOR UPDATE TO authenticated
  USING (get_user_role() IN ('admin', 'dono'));

DROP POLICY IF EXISTS "auth_delete_depoimentos" ON depoimentos;
CREATE POLICY "auth_delete_depoimentos" ON depoimentos
  FOR DELETE TO authenticated
  USING (get_user_role() IN ('admin', 'dono'));

-- Inserir depoimentos iniciais já aprovados
INSERT INTO depoimentos (nome, curso, texto, nota, aprovado) VALUES
  ('Lucas M.', 'Administração', 'Serviço excelente! Fiz minhas atividades MAPA e extensão com eles, tudo entregue no prazo e com qualidade.', 5, true),
  ('Amanda S.', 'Pedagogia', 'Super atenciosos, me ajudaram em todas as etapas do TCC. Recomendo demais!', 5, true),
  ('Carlos E.', 'Engenharia Civil', 'Profissionais competentes. Minhas atividades foram feitas com muito cuidado.', 5, true),
  ('Fernanda R.', 'Direito', 'Rapidez e qualidade. As atividades foram entregues antes do prazo.', 4, true),
  ('Rafael O.', 'Ciências Contábeis', 'Atendimento via WhatsApp é muito prático. Resolveram tudo rápido.', 5, true),
  ('Juliana P.', 'Serviço Social', 'Fiz o pacote de atividades e saiu muito mais em conta. Nota 10!', 5, true);
