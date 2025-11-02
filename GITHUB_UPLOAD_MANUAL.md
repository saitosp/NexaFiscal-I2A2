# 📤 Guia de Upload Manual para GitHub

Este guia mostra como enviar o código do **NexaFiscal** para o GitHub usando a interface web (sem usar Git no terminal).

---

## 📋 Passo a Passo

### **1. Preparar os Arquivos**

Você precisa fazer download dos seguintes arquivos e pastas do Replit:

#### **📁 Pastas Principais:**
- `agents/` - Todos os agentes de IA
- `api/` - API FastAPI
- `pages/` - Páginas do Streamlit
- `services/` - Serviços de banco de dados
- `utils/` - Utilitários
- `database/` - Configuração do banco
- `config/` - Configurações de impostos
- `attached_assets/` - **IMPORTANTE:** Contém o logo NexaFiscal!
- `Projeto Final - Artefatos/` - Para os arquivos PDF, PPTX e MP4

#### **📄 Arquivos na Raiz:**
- `README.md` - **IMPORTANTE:** Com logo e configuração para avaliadores
- `LICENSE` - Licença MIT
- `replit.md` - Documentação do projeto
- `app.py` - Aplicação principal Streamlit
- `workflow_graph.py` - Orquestração LangGraph
- `chat_workflow.py` - Workflow do chat
- `init_db.py` - Inicialização do banco
- `main.py` - API principal
- `API_DOCS.md` - Documentação da API
- `.gitignore` - Arquivo que acabamos de criar
- `pyproject.toml` - Dependências Python
- `uv.lock` - Lock file de dependências

#### **❌ NÃO envie:**
- Pasta `data/uploads/` (arquivos de usuário)
- Pasta `data/exports/` (exportações temporárias)
- Arquivos `.db`, `.sqlite` (bancos de dados locais)
- Pasta `.upm/`, `.cache/`, `.config/` (configurações do Replit)
- Arquivos de log

---

### **2. Como Fazer Download do Replit**

**Opção A: Download Individual (mais fácil)**
1. Abra o Replit no navegador web (desktop)
2. No painel de arquivos (esquerda), clique com botão direito em cada pasta/arquivo
3. Selecione "Download" ou "Download folder"
4. Salve em uma pasta no seu computador

**Opção B: Download via Shell (se disponível)**
```bash
# No Shell do Replit, crie um arquivo compactado
tar -czf nexafiscal-code.tar.gz \
  agents/ api/ pages/ services/ utils/ database/ config/ \
  attached_assets/ "Projeto Final - Artefatos/" \
  README.md LICENSE replit.md app.py workflow_graph.py \
  chat_workflow.py init_db.py main.py API_DOCS.md \
  .gitignore pyproject.toml uv.lock

# Depois faça download do arquivo nexafiscal-code.tar.gz
```

---

### **3. Upload para o GitHub**

1. **Acesse seu repositório:**
   - Vá para: https://github.com/saitosp/NexaFiscal-I2A2

2. **Upload de arquivos:**
   - Clique em **"Add file"** → **"Upload files"**
   
3. **Arraste as pastas e arquivos:**
   - Arraste TODAS as pastas e arquivos que você baixou
   - OU clique em "choose your files" e selecione tudo
   
4. **Importante sobre a estrutura:**
   - O GitHub mantém a estrutura de pastas automaticamente
   - Certifique-se de que `attached_assets/generated_images/` com o logo está incluído!

5. **Commit:**
   - Na caixa de mensagem, escreva:
     ```
     Initial commit - NexaFiscal Sistema I2A2
     
     - Sistema completo de extração de dados fiscais com IA
     - Logo profissional NexaFiscal
     - README com configuração para avaliadores
     - Licença MIT
     - Pasta para artefatos acadêmicos
     ```
   
6. **Clique em "Commit changes"**

---

### **4. Verificar se Funcionou**

Após o upload, acesse: https://github.com/saitosp/NexaFiscal-I2A2

Você DEVE ver:
- ✅ Logo NexaFiscal aparecendo no README
- ✅ Badge da licença MIT
- ✅ Estrutura de pastas completa
- ✅ Pasta "Projeto Final - Artefatos/" visível

---

### **5. Adicionar os Artefatos Acadêmicos**

Depois de criar o PDF, PPTX e MP4:

1. No GitHub, navegue até `Projeto Final - Artefatos/`
2. Clique em "Add file" → "Upload files"
3. Faça upload dos 3 arquivos:
   - `I2A2_Agentes_Inteligentes_Projeto_Final_<Nome_do_Grupo>.pdf`
   - `I2A2_Agentes_Inteligentes_Projeto_Final_<Nome_do_Grupo>.pptx`
   - `I2A2_Agentes_Inteligentes_Projeto_Final_<Nome_do_Grupo>.mp4`

---

### **6. Enviar o Email Final**

Quando tudo estiver pronto:

**Para:** challenges@i2a2.academy  
**Assunto:** I2A2 - Agentes Autônomos - Projeto Final - <Nome do Grupo>  
**Corpo:**
```
https://github.com/saitosp/NexaFiscal-I2A2
```

**Prazo:** 02/11/2025 às 23:59h

---

## ✅ Checklist Final

Antes de enviar o email, confirme:

- [ ] Logo NexaFiscal aparece no README do GitHub
- [ ] Licença MIT está visível
- [ ] Seção "Configuração para Avaliadores" está no README
- [ ] Pasta "Projeto Final - Artefatos/" contém os 3 arquivos (PDF, PPTX, MP4)
- [ ] Todo o código está no repositório
- [ ] Repositório está PÚBLICO (não privado)

---

## 🆘 Problemas Comuns

**Logo não aparece:**
- Verifique se a pasta `attached_assets/generated_images/` foi enviada
- Verifique se o caminho no README está correto

**Repositório muito grande:**
- Certifique-se de NÃO enviar a pasta `data/uploads/`
- Use o .gitignore que criamos

**Erro ao fazer upload:**
- Divida em partes menores (primeiro pastas de código, depois assets)
- GitHub tem limite de 100MB por arquivo

---

Boa sorte! 🚀
