-- ═══════════════════════════════════════════
-- Assessoria Acadêmica — Schema SQL (Supabase)
-- Execute no SQL Editor do Supabase
-- ═══════════════════════════════════════════

-- Tabela de assessores (perfil vinculado ao auth.users)
CREATE TABLE assessores (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'assessor' CHECK (role IN ('admin', 'assessor')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de alunos
CREATE TABLE alunos (
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

-- Tabela de atividades
CREATE TABLE atividades (
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

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER atividades_updated_at
  BEFORE UPDATE ON atividades
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Índices
CREATE INDEX idx_alunos_curso ON alunos(curso);
CREATE INDEX idx_alunos_tipo ON alunos(tipo);
CREATE INDEX idx_atividades_status ON atividades(status);
CREATE INDEX idx_atividades_aluno ON atividades(aluno_id);
CREATE INDEX idx_atividades_tipo ON atividades(tipo);

-- Row Level Security (RLS)
ALTER TABLE assessores ENABLE ROW LEVEL SECURITY;
ALTER TABLE alunos ENABLE ROW LEVEL SECURITY;
ALTER TABLE atividades ENABLE ROW LEVEL SECURITY;

-- Policies: assessores autenticados podem ver/editar tudo
CREATE POLICY "Assessores podem ver assessores"
  ON assessores FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Assessores podem ver alunos"
  ON alunos FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Assessores podem inserir alunos"
  ON alunos FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Assessores podem editar alunos"
  ON alunos FOR UPDATE
  TO authenticated
  USING (true);

CREATE POLICY "Assessores podem deletar alunos"
  ON alunos FOR DELETE
  TO authenticated
  USING (true);

CREATE POLICY "Assessores podem ver atividades"
  ON atividades FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Assessores podem inserir atividades"
  ON atividades FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Assessores podem editar atividades"
  ON atividades FOR UPDATE
  TO authenticated
  USING (true);

CREATE POLICY "Assessores podem deletar atividades"
  ON atividades FOR DELETE
  TO authenticated
  USING (true);

-- Criar primeiro assessor (rode depois de criar o user no Auth)
-- INSERT INTO assessores (id, nome, role) VALUES ('SEU_USER_UUID', 'Admin', 'admin');
