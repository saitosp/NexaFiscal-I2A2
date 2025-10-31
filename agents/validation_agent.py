"""
Agente de Validação - Valida a consistência dos dados extraídos
"""
from typing import Dict, Any, List
from utils.validators import validate_cnpj, validate_cpf, validate_nfe_key


class ValidationAgent:
    """
    Agente responsável por validar dados extraídos de notas fiscais
    """
    
    def validate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida os dados extraídos
        
        Args:
            state: Estado contendo dados extraídos
            
        Returns:
            Estado atualizado com resultados da validação
        """
        extracted_data = state.get('extracted_data', {})
        
        validations = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'validations': {}
        }
        
        # Valida CNPJ do emitente
        emitente_cnpj = extracted_data.get('emitente', {}).get('cnpj', '')
        if emitente_cnpj:
            cnpj_valid = validate_cnpj(emitente_cnpj)
            validations['validations']['emitente_cnpj'] = cnpj_valid
            if not cnpj_valid:
                validations['errors'].append('CNPJ do emitente inválido')
                validations['is_valid'] = False
        else:
            validations['warnings'].append('CNPJ do emitente não encontrado')
        
        # Valida CNPJ/CPF do destinatário
        dest_cnpj = extracted_data.get('destinatario', {}).get('cnpj', '')
        dest_cpf = extracted_data.get('destinatario', {}).get('cpf', '')
        
        if dest_cnpj:
            cnpj_valid = validate_cnpj(dest_cnpj)
            validations['validations']['destinatario_cnpj'] = cnpj_valid
            if not cnpj_valid:
                validations['errors'].append('CNPJ do destinatário inválido')
                validations['is_valid'] = False
        elif dest_cpf:
            cpf_valid = validate_cpf(dest_cpf)
            validations['validations']['destinatario_cpf'] = cpf_valid
            if not cpf_valid:
                validations['errors'].append('CPF do destinatário inválido')
                validations['is_valid'] = False
        else:
            validations['warnings'].append('CNPJ/CPF do destinatário não encontrado')
        
        # Valida chave de acesso
        chave = extracted_data.get('informacoes_adicionais', {}).get('chave_acesso', '')
        if chave:
            chave_valid = validate_nfe_key(chave)
            validations['validations']['chave_acesso'] = chave_valid
            if not chave_valid:
                validations['errors'].append('Chave de acesso inválida')
                validations['is_valid'] = False
        else:
            validations['warnings'].append('Chave de acesso não encontrada')
        
        # Valida valores dos totais
        totais = extracted_data.get('totais', {})
        if totais:
            valor_total = totais.get('valor_total', 0)
            valor_produtos = totais.get('valor_produtos', 0)
            
            if valor_total <= 0:
                validations['warnings'].append('Valor total da nota é zero ou negativo')
            
            if valor_produtos <= 0:
                validations['warnings'].append('Valor dos produtos é zero ou negativo')
        else:
            validations['warnings'].append('Totais não encontrados')
        
        # Valida itens
        itens = extracted_data.get('itens', [])
        if not itens:
            validations['warnings'].append('Nenhum item encontrado na nota')
        else:
            validations['validations']['num_itens'] = len(itens)
            
            # Valida valores dos itens
            for i, item in enumerate(itens):
                qtd = item.get('quantidade', 0)
                valor_unit = item.get('valor_unitario', 0)
                valor_total = item.get('valor_total', 0)
                
                if qtd <= 0:
                    validations['warnings'].append(f'Item {i+1}: quantidade inválida')
                
                if valor_unit < 0:
                    validations['warnings'].append(f'Item {i+1}: valor unitário negativo')
                
                # Valida cálculo do item
                if qtd > 0 and valor_unit > 0:
                    valor_calculado = qtd * valor_unit
                    diferenca = abs(valor_calculado - valor_total)
                    
                    # Tolerância de 0.5% para diferenças de arredondamento
                    if diferenca > (valor_total * 0.005):
                        validations['warnings'].append(
                            f'Item {i+1}: divergência no cálculo (esperado: {valor_calculado:.2f}, '
                            f'encontrado: {valor_total:.2f})'
                        )
        
        state['validation'] = validations
        state['status'] = 'validated'
        
        return state
