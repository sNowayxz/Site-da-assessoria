-- Fix: Corrigir nome Barbara → Bárbara
UPDATE assessores SET nome = 'Bárbara', label = 'Assessoria Bárbara'
WHERE nome = 'Barbara' OR label = 'Assessoria Barbara';

-- Fix: Permitir assessoria deletar suas próprias solicitações (status aguardando)
DROP POLICY IF EXISTS "Role-based delete solicitacoes" ON solicitacoes;
CREATE POLICY "Role-based delete solicitacoes"
  ON solicitacoes FOR DELETE TO authenticated
  USING (
    get_user_role() IN ('admin', 'dono')
    OR (get_user_role() IN ('assessoria', 'extensao') AND assessor_id = auth.uid())
  );
