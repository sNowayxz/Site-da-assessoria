-- ═══════════════════════════════════════════════════════════════
-- ASSESSORIA ACADÊMICA — SQL COMPLETO (SUPABASE)
-- Cole TUDO no SQL Editor do Supabase e clique "Run"
-- Se alguma tabela já existe, os comandos com IF NOT EXISTS vão ignorar
-- ═══════════════════════════════════════════════════════════════

-- ═══ 1. FUNÇÕES UTILITÁRIAS ═══

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ═══ 2. TABELA ASSESSORES ═══

CREATE TABLE IF NOT EXISTS assessores (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'assessor' CHECK (role IN ('admin', 'assessor')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ═══ 3. TABELA ALUNOS ═══

CREATE TABLE IF NOT EXISTS alunos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ra TEXT UNIQUE NOT NULL,
  nome TEXT NOT NULL,
  curso TEXT NOT NULL DEFAULT '',
  tipo TEXT NOT NULL DEFAULT 'avulso' CHECK (tipo IN ('avulso', 'mensalista')),
  telefone TEXT DEFAULT '',
  observacoes TEXT DEFAULT '',
  assessor_id UUID REFERENCES assessores(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Colunas extras (v2)
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS email TEXT DEFAULT '';
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS cpf TEXT DEFAULT '';
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS situacao TEXT DEFAULT 'cursando';
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS mensalista_valor DECIMAL(10,2) DEFAULT NULL;
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS mensalista_vencimento INTEGER DEFAULT NULL;
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS studeo_senha TEXT;


-- ═══ 4. TABELA MÓDULOS ═══

CREATE TABLE IF NOT EXISTS modulos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo TEXT UNIQUE NOT NULL,
  nome TEXT NOT NULL,
  situacao TEXT NOT NULL DEFAULT 'aberto' CHECK (situacao IN ('aberto', 'fechado')),
  dt_inicio DATE,
  dt_fim DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ═══ 5. TABELA DISCIPLINAS ═══

CREATE TABLE IF NOT EXISTS disciplinas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aluno_id UUID NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
  modulo_id UUID REFERENCES modulos(id) ON DELETE SET NULL,
  nome TEXT NOT NULL,
  shortname TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'matriculada' CHECK (status IN ('matriculada', 'concluida', 'trancada')),
  dt_inicio DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ═══ 6. TABELA ATIVIDADES ═══

CREATE TABLE IF NOT EXISTS atividades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aluno_id UUID NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
  tipo TEXT NOT NULL CHECK (tipo IN ('atividade', 'mapa', 'tcc', 'relatorio', 'extensao', 'pacote')),
  descricao TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'em_andamento', 'entregue', 'revisao')),
  valor DECIMAL(10,2) DEFAULT 0,
  observacoes TEXT DEFAULT '',
  assessor_id UUID REFERENCES assessores(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Colunas extras (v2)
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS disciplina_id UUID REFERENCES disciplinas(id) ON DELETE SET NULL;
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS modulo_id UUID REFERENCES modulos(id) ON DELETE SET NULL;
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS estilo TEXT DEFAULT 'questionario';
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS enunciado TEXT DEFAULT '';
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS alternativas JSONB DEFAULT '{}';
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS gabarito TEXT DEFAULT '';
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS nota DECIMAL(5,2) DEFAULT NULL;
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS dt_entrega DATE DEFAULT NULL;
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS prioridade TEXT DEFAULT 'normal';

-- Trigger updated_at
DROP TRIGGER IF EXISTS atividades_updated_at ON atividades;
CREATE TRIGGER atividades_updated_at
  BEFORE UPDATE ON atividades
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ═══ 7. TABELA PAGAMENTOS ═══

CREATE TABLE IF NOT EXISTS pagamentos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aluno_id UUID NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
  valor DECIMAL(10,2) NOT NULL,
  tipo TEXT NOT NULL DEFAULT 'avulso' CHECK (tipo IN ('avulso', 'mensalidade', 'pacote')),
  status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'pago', 'atrasado', 'cancelado')),
  referencia TEXT DEFAULT '',
  dt_vencimento DATE,
  dt_pagamento DATE,
  observacoes TEXT DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

DROP TRIGGER IF EXISTS pagamentos_updated_at ON pagamentos;
CREATE TRIGGER pagamentos_updated_at
  BEFORE UPDATE ON pagamentos
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ═══ 8. TABELA STUDEO SYNC ═══

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


-- ═══ 9. TABELA PEDIDOS DE EXTENSÃO ═══

CREATE TABLE IF NOT EXISTS pedidos_extensao (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  nome_cliente TEXT NOT NULL,
  email TEXT NOT NULL,
  telefone TEXT,
  ra TEXT,
  curso TEXT NOT NULL,
  carga_horaria INTEGER NOT NULL,
  tema TEXT NOT NULL,
  prazo DATE,
  observacoes TEXT,
  valor DECIMAL(10,2),
  status TEXT DEFAULT 'aguardando_pagamento'
    CHECK (status IN ('aguardando_pagamento','pago','em_andamento','concluido','cancelado')),
  payment_id TEXT,
  payment_status TEXT,
  preference_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

DROP TRIGGER IF EXISTS pedidos_extensao_updated_at ON pedidos_extensao;
CREATE TRIGGER pedidos_extensao_updated_at
  BEFORE UPDATE ON pedidos_extensao
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ═══ 10. ÍNDICES ═══

CREATE INDEX IF NOT EXISTS idx_alunos_curso ON alunos(curso);
CREATE INDEX IF NOT EXISTS idx_alunos_tipo ON alunos(tipo);
CREATE INDEX IF NOT EXISTS idx_atividades_status ON atividades(status);
CREATE INDEX IF NOT EXISTS idx_atividades_aluno ON atividades(aluno_id);
CREATE INDEX IF NOT EXISTS idx_atividades_tipo ON atividades(tipo);
CREATE INDEX IF NOT EXISTS idx_atividades_disciplina ON atividades(disciplina_id);
CREATE INDEX IF NOT EXISTS idx_atividades_modulo ON atividades(modulo_id);
CREATE INDEX IF NOT EXISTS idx_atividades_prioridade ON atividades(prioridade);
CREATE INDEX IF NOT EXISTS idx_disciplinas_aluno ON disciplinas(aluno_id);
CREATE INDEX IF NOT EXISTS idx_disciplinas_modulo ON disciplinas(modulo_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_aluno ON pagamentos(aluno_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_status ON pagamentos(status);
CREATE INDEX IF NOT EXISTS idx_studeo_sync_aluno ON studeo_sync(aluno_id);
CREATE INDEX IF NOT EXISTS idx_studeo_sync_respondida ON studeo_sync(respondida);
CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos_extensao(status);
CREATE INDEX IF NOT EXISTS idx_pedidos_email ON pedidos_extensao(email);
CREATE INDEX IF NOT EXISTS idx_pedidos_payment ON pedidos_extensao(payment_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_preference ON pedidos_extensao(preference_id);


-- ═══ 11. ROW LEVEL SECURITY ═══

ALTER TABLE assessores ENABLE ROW LEVEL SECURITY;
ALTER TABLE alunos ENABLE ROW LEVEL SECURITY;
ALTER TABLE atividades ENABLE ROW LEVEL SECURITY;
ALTER TABLE modulos ENABLE ROW LEVEL SECURITY;
ALTER TABLE disciplinas ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagamentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE studeo_sync ENABLE ROW LEVEL SECURITY;
ALTER TABLE pedidos_extensao ENABLE ROW LEVEL SECURITY;


-- ═══ 12. POLICIES — ASSESSORES (authenticated) ═══

-- Assessores
DO $$ BEGIN
  CREATE POLICY "Assessores podem ver assessores" ON assessores FOR SELECT TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Alunos
DO $$ BEGIN
  CREATE POLICY "Assessores podem ver alunos" ON alunos FOR SELECT TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Assessores podem inserir alunos" ON alunos FOR INSERT TO authenticated WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Assessores podem editar alunos" ON alunos FOR UPDATE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Assessores podem deletar alunos" ON alunos FOR DELETE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Atividades
DO $$ BEGIN
  CREATE POLICY "Assessores podem ver atividades" ON atividades FOR SELECT TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Assessores podem inserir atividades" ON atividades FOR INSERT TO authenticated WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Assessores podem editar atividades" ON atividades FOR UPDATE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Assessores podem deletar atividades" ON atividades FOR DELETE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Módulos
DO $$ BEGIN
  CREATE POLICY "Auth pode ver modulos" ON modulos FOR SELECT TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode inserir modulos" ON modulos FOR INSERT TO authenticated WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode editar modulos" ON modulos FOR UPDATE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode deletar modulos" ON modulos FOR DELETE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Disciplinas
DO $$ BEGIN
  CREATE POLICY "Auth pode ver disciplinas" ON disciplinas FOR SELECT TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode inserir disciplinas" ON disciplinas FOR INSERT TO authenticated WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode editar disciplinas" ON disciplinas FOR UPDATE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode deletar disciplinas" ON disciplinas FOR DELETE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Pagamentos
DO $$ BEGIN
  CREATE POLICY "Auth pode ver pagamentos" ON pagamentos FOR SELECT TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode inserir pagamentos" ON pagamentos FOR INSERT TO authenticated WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode editar pagamentos" ON pagamentos FOR UPDATE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode deletar pagamentos" ON pagamentos FOR DELETE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Studeo Sync
DO $$ BEGIN
  CREATE POLICY "Auth pode ver studeo_sync" ON studeo_sync FOR SELECT TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode inserir studeo_sync" ON studeo_sync FOR INSERT TO authenticated WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode editar studeo_sync" ON studeo_sync FOR UPDATE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth pode deletar studeo_sync" ON studeo_sync FOR DELETE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Pedidos Extensão (anon + authenticated)
DO $$ BEGIN
  CREATE POLICY "Anon can insert pedidos" ON pedidos_extensao FOR INSERT TO anon WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Anon can read pedidos" ON pedidos_extensao FOR SELECT TO anon USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth full access pedidos SELECT" ON pedidos_extensao FOR SELECT TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth full access pedidos INSERT" ON pedidos_extensao FOR INSERT TO authenticated WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth full access pedidos UPDATE" ON pedidos_extensao FOR UPDATE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE POLICY "Auth full access pedidos DELETE" ON pedidos_extensao FOR DELETE TO authenticated USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ═══ 13. INSERIR ASSESSOR ADMIN ═══
-- Após criar o usuário no Authentication do Supabase, pegue o UUID e rode:
-- INSERT INTO assessores (id, nome, role) VALUES ('SEU_USER_UUID_AQUI', 'Admin', 'admin');

-- ═══ FIM ═══
