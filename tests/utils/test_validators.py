import pytest
from utils.validators import (
    validate_cnpj,
    validate_cpf,
    validate_nfe_key,
    format_cnpj,
    format_cpf,
)

class TestValidateCNPJ:
    def test_valid_cnpj_unformatted(self):
        # A known valid CNPJ generated earlier
        assert validate_cnpj("91797476681751") is True

    def test_valid_cnpj_formatted(self):
        assert validate_cnpj("91.797.476/6817-51") is True

    def test_invalid_cnpj_wrong_digit(self):
        assert validate_cnpj("91797476681752") is False

    def test_invalid_cnpj_wrong_length(self):
        assert validate_cnpj("9179747668175") is False
        assert validate_cnpj("917974766817510") is False

    def test_empty_or_none(self):
        assert validate_cnpj("") is False
        assert validate_cnpj(None) is False

class TestValidateCPF:
    def test_valid_cpf_unformatted(self):
        # A known valid CPF generated earlier
        assert validate_cpf("93074123087") is True

    def test_valid_cpf_formatted(self):
        assert validate_cpf("930.741.230-87") is True

    def test_invalid_cpf_wrong_digit(self):
        assert validate_cpf("93074123088") is False

    def test_invalid_cpf_wrong_length(self):
        assert validate_cpf("9307412308") is False
        assert validate_cpf("930741230870") is False

    def test_empty_or_none(self):
        assert validate_cpf("") is False
        assert validate_cpf(None) is False

class TestValidateNFeKey:
    def test_valid_nfe_key(self):
        # A known valid NFe Key (44 digits, correct check digit)
        assert validate_nfe_key("35180512345678901234550010000000011000000008") is True

    def test_valid_nfe_key_with_formatting(self):
        # If it has formatting it should clean it (utils removes non-digits)
        assert validate_nfe_key("3518.0512.3456.7890.1234.5500.1000.0000.0110.0000.0008") is True

    def test_invalid_nfe_key_wrong_digit(self):
        # Changing the check digit
        assert validate_nfe_key("35180512345678901234550010000000011000000009") is False

    def test_invalid_nfe_key_wrong_length(self):
        assert validate_nfe_key("3518051234567890123455001000000001100000000") is False
        assert validate_nfe_key("351805123456789012345500100000000110000000080") is False

    def test_empty_or_none(self):
        assert validate_nfe_key("") is False
        assert validate_nfe_key(None) is False

class TestFormatCNPJ:
    def test_format_clean_cnpj(self):
        assert format_cnpj("91797476681751") == "91.797.476/6817-51"

    def test_format_already_formatted(self):
        assert format_cnpj("91.797.476/6817-51") == "91.797.476/6817-51"

    def test_format_with_weird_chars(self):
        assert format_cnpj("91a797b476c6817d51") == "91.797.476/6817-51"

    def test_format_wrong_length_returns_original(self):
        # Should return original input if length isn't 14
        assert format_cnpj("12345") == "12345"

class TestFormatCPF:
    def test_format_clean_cpf(self):
        assert format_cpf("93074123087") == "930.741.230-87"

    def test_format_already_formatted(self):
        assert format_cpf("930.741.230-87") == "930.741.230-87"

    def test_format_with_weird_chars(self):
        assert format_cpf("930a741b230c87") == "930.741.230-87"

    def test_format_wrong_length_returns_original(self):
        # Should return original input if length isn't 11
        assert format_cpf("12345") == "12345"

    def test_nfe_key_exception(self, monkeypatch):
        # Force an exception to test the except block
        def mock_int(val):
            raise ValueError("Forced error")

        # We mock the built-in int function within the utils.validators module scope for this test
        import builtins
        original_int = builtins.int

        monkeypatch.setattr("builtins.int", mock_int)
        assert validate_nfe_key("35180512345678901234550010000000011000000008") is False
