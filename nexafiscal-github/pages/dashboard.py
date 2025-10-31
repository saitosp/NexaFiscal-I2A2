"""
Dashboard de Análise - Visualizações interativas com Plotly
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from services.analysis_service import AnalysisService
from services.batch_service import BatchService
from utils.tax_config_loader import get_tax_config, get_all_tax_names, get_all_tax_colors
import pandas as pd


def render_dashboard():
    """
    Renderiza dashboard de análise com gráficos interativos
    """
    st.title("📊 Dashboard NexaFiscal")
    st.markdown("**Visualizações interativas e insights automáticos dos documentos processados**")
    
    st.divider()
    
    # Seletor de lotes
    selected_batch_ids = render_batch_selector()
    
    st.divider()
    
    try:
        dashboard_data = AnalysisService.get_dashboard_data(batch_ids=selected_batch_ids if selected_batch_ids is not None else [])
        
        if 'error' in dashboard_data:
            st.warning(f"⚠️ {dashboard_data.get('note', dashboard_data['error'])}")
            if dashboard_data.get('overview', {}).get('total_documents', 0) == 0:
                st.info("📭 Nenhum documento processado ainda. Faça upload de notas fiscais para começar!")
                return
        
        overview = dashboard_data.get('overview', {})
        
        if overview.get('total_documents', 0) == 0:
            st.info("📭 Nenhum documento processado ainda. Faça upload de notas fiscais para começar!")
            return
        
        render_overview_metrics(overview)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            render_document_types_chart(dashboard_data.get('by_type', {}))
        
        with col2:
            render_tax_breakdown_chart(selected_batch_ids)
        
        st.divider()
        
        col3, col4 = st.columns(2)
        
        with col3:
            render_monthly_trend_chart(dashboard_data.get('monthly_trend', {}))
        
        with col4:
            render_top_issuers_chart(dashboard_data.get('top_issuers', []))
        
        st.divider()
        
        render_top_products_table(selected_batch_ids)
        
        st.divider()
        
        render_insights(dashboard_data.get('insights', []))
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dashboard: {str(e)}")


def render_batch_selector():
    """
    Renderiza seletor de lotes para filtrar dashboard
    
    Returns:
        Lista de batch_ids selecionados (None = todos os documentos)
    """
    st.subheader("🗂️ Filtro de Lotes")
    
    # Busca todos os lotes disponíveis
    all_batches = BatchService.get_all_batch_metadata()
    
    if not all_batches:
        st.info("📭 Nenhum lote criado ainda. Importe documentos em lote para começar!")
        return None
    
    # Seletor de modo
    mode = st.radio(
        "Modo de visualização:",
        ["📊 Todos os documentos", "📁 Lote individual", "📂 Múltiplos lotes"],
        horizontal=True,
        help="Escolha como deseja visualizar os dados no dashboard"
    )
    
    if mode == "📊 Todos os documentos":
        st.success("Exibindo todos os documentos processados (sem filtro de lote)")
        return None
    
    elif mode == "📁 Lote individual":
        # Lista de lotes para seleção única
        batch_options = {
            f"{batch['batch_name']} ({batch['document_count']} docs, R$ {batch['total_value']:,.2f})": batch['batch_id']
            for batch in all_batches
        }
        
        selected_label = st.selectbox(
            "Selecione um lote:",
            options=list(batch_options.keys()),
            help="Escolha um lote específico para análise detalhada"
        )
        
        selected_batch_id = batch_options[selected_label]
        
        # Exibe resumo do lote selecionado
        selected_batch = next(b for b in all_batches if b['batch_id'] == selected_batch_id)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 Documentos", selected_batch['document_count'])
        with col2:
            st.metric("💰 Valor Total", f"R$ {selected_batch['total_value']:,.2f}")
        with col3:
            from datetime import datetime
            created_date = selected_batch['created_at']
            if isinstance(created_date, str):
                created_date = datetime.fromisoformat(created_date)
            st.metric("📅 Criado em", created_date.strftime('%d/%m/%Y') if created_date else 'N/A')
        
        return [selected_batch_id]
    
    else:  # Múltiplos lotes
        # Multiselect para escolher vários lotes
        batch_options = {
            f"{batch['batch_name']} ({batch['document_count']} docs)": batch['batch_id']
            for batch in all_batches
        }
        
        selected_labels = st.multiselect(
            "Selecione os lotes para comparar:",
            options=list(batch_options.keys()),
            help="Escolha múltiplos lotes para análise comparativa"
        )
        
        if not selected_labels:
            st.warning("⚠️ Selecione pelo menos um lote para continuar")
            return []
        
        selected_batch_ids = [batch_options[label] for label in selected_labels]
        
        # Resumo dos lotes selecionados
        total_docs = sum(b['document_count'] for b in all_batches if b['batch_id'] in selected_batch_ids)
        total_value = sum(b['total_value'] for b in all_batches if b['batch_id'] in selected_batch_ids)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📂 Lotes Selecionados", len(selected_batch_ids))
        with col2:
            st.metric("📄 Total de Documentos", total_docs)
        with col3:
            st.metric("💰 Valor Total", f"R$ {total_value:,.2f}")
        
        return selected_batch_ids


def render_overview_metrics(overview):
    """
    Renderiza métricas de visão geral
    """
    st.subheader("📈 Visão Geral")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Documentos",
            f"{overview.get('total_documents', 0):,}",
            help="Número total de notas fiscais processadas"
        )
    
    with col2:
        total_value = overview.get('total_value', 0)
        st.metric(
            "Valor Total",
            f"R$ {total_value:,.2f}",
            help="Soma de todos os valores dos documentos"
        )
    
    with col3:
        total_taxes = overview.get('total_taxes', 0)
        st.metric(
            "Impostos Totais",
            f"R$ {total_taxes:,.2f}",
            help="Soma de todos os impostos pagos"
        )
    
    with col4:
        tax_burden = overview.get('tax_burden_percent', 0)
        st.metric(
            "Carga Tributária",
            f"{tax_burden:.1f}%",
            help="Percentual médio de impostos sobre o valor total",
            delta=f"{tax_burden - 30:.1f}%" if tax_burden > 0 else None,
            delta_color="inverse"
        )


def render_document_types_chart(by_type):
    """
    Gráfico de pizza com tipos de documentos
    """
    st.subheader("📄 Distribuição por Tipo de Documento")
    
    if not by_type:
        st.info("Sem dados para exibir")
        return
    
    df = pd.DataFrame([
        {'Tipo': tipo, 'Quantidade': qtd}
        for tipo, qtd in by_type.items()
    ])
    
    fig = px.pie(
        df,
        values='Quantidade',
        names='Tipo',
        title='Tipos de Documentos Processados',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    st.plotly_chart(fig, use_container_width=True)


def render_tax_breakdown_chart(batch_ids=None):
    """
    Gráfico de barras com breakdown de impostos
    Renderiza dinamicamente todos os impostos configurados em tax_config.json
    """
    st.subheader("💰 Breakdown de Impostos")
    
    tax_data = AnalysisService.get_tax_analysis(batch_ids=batch_ids if batch_ids is not None else [])
    
    if sum(tax_data.values()) == 0:
        st.info("Sem dados de impostos disponíveis")
        return
    
    # Obtém configuração de impostos
    tax_config = get_tax_config()
    tax_names = get_all_tax_names()
    tax_colors = get_all_tax_colors()
    
    # Constrói DataFrame dinamicamente a partir da configuração
    tax_rows = []
    for tax in tax_config.get_all_taxes(enabled_only=True):
        tax_id = tax['id']
        tax_name = tax_names.get(tax_id, tax_id.upper())
        tax_value = tax_data.get(f'total_{tax_id}', 0)
        
        if tax_value > 0:
            tax_rows.append({
                'Imposto': tax_name,
                'Valor': tax_value,
                'tax_id': tax_id
            })
    
    if not tax_rows:
        st.info("Sem dados de impostos disponíveis")
        return
    
    df = pd.DataFrame(tax_rows)
    
    # Mapeia cores baseado na configuração
    color_map = {row['Imposto']: tax_colors.get(row['tax_id'], '#808080') 
                 for row in tax_rows}
    
    fig = px.bar(
        df,
        x='Imposto',
        y='Valor',
        title='Total de Impostos por Tipo',
        color='Imposto',
        color_discrete_map=color_map
    )
    
    fig.update_layout(
        showlegend=False,
        height=400,
        yaxis_title="Valor (R$)"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_monthly_trend_chart(monthly_data):
    """
    Gráfico de linha com tendência temporal
    """
    st.subheader("📅 Tendência Temporal")
    
    if not monthly_data:
        st.info("Dados insuficientes para tendência temporal")
        return
    
    df = pd.DataFrame([
        {
            'Mês': mes,
            'Documentos': data['count'],
            'Valor Total': data['total_value']
        }
        for mes, data in monthly_data.items()
    ])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['Mês'],
        y=df['Documentos'],
        mode='lines+markers',
        name='Documentos',
        line=dict(color='#636EFA', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Documentos Processados por Mês',
        xaxis_title='Mês',
        yaxis_title='Quantidade',
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_top_issuers_chart(top_issuers):
    """
    Gráfico de barras horizontais com top emitentes
    """
    st.subheader("🏢 Top 5 Emitentes")
    
    if not top_issuers:
        st.info("Sem dados de emitentes disponíveis")
        return
    
    df = pd.DataFrame(top_issuers)
    
    fig = px.bar(
        df,
        x='count',
        y='name',
        orientation='h',
        title='Empresas com Mais Notas Emitidas',
        color='count',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        showlegend=False,
        height=400,
        xaxis_title="Número de Documentos",
        yaxis_title="Emitente"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_top_products_table(batch_ids=None):
    """
    Tabela com produtos mais frequentes
    """
    st.subheader("🛒 Top 10 Produtos Mais Frequentes")
    
    products = AnalysisService.get_top_products(limit=10, batch_ids=batch_ids if batch_ids is not None else [])
    
    if not products:
        st.info("Sem dados de produtos disponíveis")
        return
    
    df = pd.DataFrame(products)
    
    df['total_value'] = df['total_value'].apply(lambda x: f"R$ {x:,.2f}")
    df['total_quantity'] = df['total_quantity'].apply(lambda x: f"{x:,.2f}")
    
    df.columns = ['Descrição', 'Ocorrências', 'Valor Total', 'Quantidade Total']
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Descrição': st.column_config.TextColumn('Descrição', width='large'),
            'Ocorrências': st.column_config.NumberColumn('Ocorrências', width='small'),
            'Valor Total': st.column_config.TextColumn('Valor Total', width='medium'),
            'Quantidade Total': st.column_config.TextColumn('Quantidade', width='medium')
        }
    )


def render_insights(insights):
    """
    Renderiza insights e recomendações
    """
    st.subheader("💡 Insights e Recomendações")
    
    if not insights:
        insights = ["✅ Nenhuma recomendação especial no momento"]
    
    for insight in insights:
        st.info(insight)


if __name__ == "__main__":
    render_dashboard()
