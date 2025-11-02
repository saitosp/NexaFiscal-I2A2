"""
Página de Configuração de Impostos - Interface visual para gerenciar impostos
"""
import streamlit as st
import pandas as pd
from utils.tax_config_loader import get_tax_config


def render_tax_config():
    """
    Renderiza interface de configuração de impostos
    """
    st.title("⚙️ Configuração de Impostos - NexaFiscal")
    st.markdown("**Gerencie os impostos do sistema de forma visual e intuitiva**")
    
    st.divider()
    
    tax_config = get_tax_config()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Impostos Cadastrados")
        render_tax_list(tax_config)
    
    with col2:
        st.subheader("➕ Adicionar Novo Imposto")
        render_add_tax_form(tax_config)
    
    st.divider()
    
    st.subheader("📖 Como Adicionar o IVA (quando implementado)")
    st.info("""
    **Quando o IVA for implementado no Brasil:**
    
    1. Clique no formulário à direita
    2. Preencha os campos:
       - **ID**: iva (minúsculo, sem espaços)
       - **Nome**: IVA
       - **Nome Completo**: Imposto sobre Valor Agregado
       - **Cor**: Escolha uma cor no seletor
       - **Escopo**: Federal
       - **Campos XML**: vIVA (ou o campo definido pela Receita)
       - **Aplica-se aos documentos**: Selecione NFe, NFCe, SAT
    3. Clique em "Adicionar Imposto"
    
    **Pronto!** O sistema automaticamente:
    - Extrairá o IVA de documentos XML
    - Pedirá à IA para identificar IVA em documentos visuais
    - Mostrará o IVA no dashboard
    - Incluirá o IVA nas análises
    
    Sem necessidade de alterar código!
    """)


def render_tax_list(tax_config):
    """Renderiza tabela com lista de impostos"""
    all_taxes = tax_config.get_all_taxes(enabled_only=False)
    
    if not all_taxes:
        st.info("Nenhum imposto cadastrado ainda")
        return
    
    tax_data = []
    for tax in all_taxes:
        tax_data.append({
            'ID': tax['id'],
            'Nome': tax['name'],
            'Nome Completo': tax.get('full_name', ''),
            'Escopo': tax.get('scope', ''),
            'Status': '✅ Ativo' if tax.get('enabled', True) else '❌ Inativo',
            'Cor': tax.get('color', '#808080')
        })
    
    df = pd.DataFrame(tax_data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    st.subheader("🔧 Ações nos Impostos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Ativar/Desativar**")
        tax_ids = [f"{tax['name']} ({tax['id']})" for tax in all_taxes]
        selected_toggle = st.selectbox(
            "Selecione o imposto:",
            options=tax_ids,
            key="toggle_select"
        )
        
        if st.button("🔄 Ativar/Desativar", key="toggle_btn"):
            tax_id = selected_toggle.split('(')[1].split(')')[0]
            new_status = tax_config.toggle_tax_status(tax_id)
            
            if new_status is not None:
                status_msg = "ativado" if new_status else "desativado"
                st.success(f"✅ Imposto {status_msg} com sucesso!")
                st.rerun()
            else:
                st.error("❌ Erro ao alterar status do imposto")
    
    with col2:
        st.write("**Editar**")
        selected_edit = st.selectbox(
            "Selecione o imposto:",
            options=tax_ids,
            key="edit_select"
        )
        
        if st.button("✏️ Editar", key="edit_btn"):
            tax_id = selected_edit.split('(')[1].split(')')[0]
            st.session_state['editing_tax_id'] = tax_id
            st.rerun()
    
    with col3:
        st.write("**Remover**")
        selected_delete = st.selectbox(
            "Selecione o imposto:",
            options=tax_ids,
            key="delete_select"
        )
        
        if st.button("🗑️ Remover", key="delete_btn", type="secondary"):
            tax_id = selected_delete.split('(')[1].split(')')[0]
            
            if st.session_state.get('confirm_delete') == tax_id:
                if tax_config.delete_tax(tax_id):
                    st.success(f"✅ Imposto removido com sucesso!")
                    st.session_state.pop('confirm_delete', None)
                    st.rerun()
                else:
                    st.error("❌ Erro ao remover imposto")
            else:
                st.session_state['confirm_delete'] = tax_id
                st.warning("⚠️ Clique novamente para confirmar a remoção")
    
    if 'editing_tax_id' in st.session_state:
        render_edit_tax_form(tax_config, st.session_state['editing_tax_id'])


def render_add_tax_form(tax_config):
    """Renderiza formulário para adicionar novo imposto"""
    with st.form("add_tax_form"):
        tax_id = st.text_input(
            "ID do Imposto*",
            placeholder="ex: iva",
            help="Identificador único (minúsculo, sem espaços)"
        )
        
        tax_name = st.text_input(
            "Nome*",
            placeholder="ex: IVA",
            help="Nome curto do imposto"
        )
        
        tax_full_name = st.text_input(
            "Nome Completo*",
            placeholder="ex: Imposto sobre Valor Agregado",
            help="Nome completo legal do imposto"
        )
        
        tax_description = st.text_area(
            "Descrição",
            placeholder="Breve descrição do imposto",
            help="Informação adicional sobre o imposto"
        )
        
        tax_color = st.color_picker(
            "Cor para Gráficos*",
            value="#9C27B0",
            help="Cor usada nos gráficos do dashboard"
        )
        
        tax_scope = st.selectbox(
            "Escopo*",
            options=["federal", "estadual", "municipal"],
            help="Jurisdição do imposto"
        )
        
        tax_xml_fields = st.text_input(
            "Campos XML*",
            placeholder="ex: vIVA, vIVAST",
            help="Campos XML separados por vírgula (ex: vIVA, vIVAST)"
        )
        
        doc_types = st.multiselect(
            "Aplica-se aos Documentos*",
            options=["NFe", "NFCe", "SAT", "CTe", "NFSe"],
            default=["NFe", "NFCe"],
            help="Tipos de documentos onde este imposto pode aparecer"
        )
        
        enabled = st.checkbox("Ativar imposto imediatamente", value=True)
        
        submitted = st.form_submit_button("➕ Adicionar Imposto", type="primary")
        
        if submitted:
            if not all([tax_id, tax_name, tax_full_name, tax_xml_fields, doc_types]):
                st.error("⚠️ Por favor, preencha todos os campos obrigatórios (*)")
                return
            
            if tax_config.get_tax_by_id(tax_id):
                st.error(f"❌ Já existe um imposto com o ID '{tax_id}'")
                return
            
            xml_fields_list = [field.strip() for field in tax_xml_fields.split(',')]
            
            new_tax = {
                "id": tax_id.lower().strip(),
                "name": tax_name.strip(),
                "full_name": tax_full_name.strip(),
                "description": tax_description.strip() if tax_description else "",
                "xml_fields": xml_fields_list,
                "color": tax_color,
                "enabled": enabled,
                "scope": tax_scope,
                "applies_to": doc_types
            }
            
            if tax_config.add_tax(new_tax):
                st.success(f"✅ Imposto '{tax_name}' adicionado com sucesso!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Erro ao adicionar imposto")


def render_edit_tax_form(tax_config, tax_id):
    """Renderiza formulário para editar imposto existente"""
    st.divider()
    st.subheader(f"✏️ Editando Imposto: {tax_id}")
    
    current_tax = tax_config.get_tax_by_id(tax_id)
    
    if not current_tax:
        st.error(f"Imposto '{tax_id}' não encontrado")
        return
    
    with st.form("edit_tax_form"):
        tax_name = st.text_input(
            "Nome*",
            value=current_tax.get('name', ''),
            help="Nome curto do imposto"
        )
        
        tax_full_name = st.text_input(
            "Nome Completo*",
            value=current_tax.get('full_name', ''),
            help="Nome completo legal do imposto"
        )
        
        tax_description = st.text_area(
            "Descrição",
            value=current_tax.get('description', ''),
            help="Informação adicional sobre o imposto"
        )
        
        tax_color = st.color_picker(
            "Cor para Gráficos*",
            value=current_tax.get('color', '#808080'),
            help="Cor usada nos gráficos do dashboard"
        )
        
        tax_scope = st.selectbox(
            "Escopo*",
            options=["federal", "estadual", "municipal"],
            index=["federal", "estadual", "municipal"].index(current_tax.get('scope', 'federal')),
            help="Jurisdição do imposto"
        )
        
        xml_fields_str = ', '.join(current_tax.get('xml_fields', []))
        tax_xml_fields = st.text_input(
            "Campos XML*",
            value=xml_fields_str,
            help="Campos XML separados por vírgula"
        )
        
        doc_types = st.multiselect(
            "Aplica-se aos Documentos*",
            options=["NFe", "NFCe", "SAT", "CTe", "NFSe"],
            default=current_tax.get('applies_to', []),
            help="Tipos de documentos onde este imposto pode aparecer"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            save_btn = st.form_submit_button("💾 Salvar Alterações", type="primary")
        
        with col2:
            cancel_btn = st.form_submit_button("❌ Cancelar")
        
        if cancel_btn:
            st.session_state.pop('editing_tax_id', None)
            st.rerun()
        
        if save_btn:
            if not all([tax_name, tax_full_name, tax_xml_fields, doc_types]):
                st.error("⚠️ Por favor, preencha todos os campos obrigatórios (*)")
                return
            
            xml_fields_list = [field.strip() for field in tax_xml_fields.split(',')]
            
            updated_tax = {
                "id": tax_id,
                "name": (tax_name or "").strip(),
                "full_name": (tax_full_name or "").strip(),
                "description": tax_description.strip() if tax_description else "",
                "xml_fields": xml_fields_list,
                "color": tax_color,
                "enabled": current_tax.get('enabled', True),
                "scope": tax_scope,
                "applies_to": doc_types
            }
            
            if tax_config.update_tax(tax_id, updated_tax):
                st.success(f"✅ Imposto '{tax_name}' atualizado com sucesso!")
                st.session_state.pop('editing_tax_id', None)
                st.rerun()
            else:
                st.error("❌ Erro ao atualizar imposto")


if __name__ == "__main__":
    render_tax_config()
