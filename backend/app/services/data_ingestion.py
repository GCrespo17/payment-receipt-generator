import pandas as pd
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import re
import math

def extract_sheet_names_from_excel(excel_path:Path)->list[str]:
    sheet_names = pd.ExcelFile(excel_path).sheet_names
    return sheet_names

def extract_data_from_excelsheet(excel_path:Path, sheet_name:str, header_row_index=0)->pd.DataFrame:
    sheet_dataframe = pd.read_excel(excel_path, sheet_name = sheet_name, skiprows=header_row_index, keep_default_na=False)
    return sheet_dataframe

def extract_column_names(data:pd.DataFrame)->list[str]:
    return [str(column) for column in data.columns]

def parse_mixed_number(number_string:str)->Decimal:
    number_string = number_string.strip().replace(" ", "")
    
    if not number_string:
        print("Empty value")

    has_comma = "," in number_string
    has_dot = "." in number_string

    if has_comma and has_dot:
        if number_string.rfind(",") > number_string.rfind("."):
            number_string = number_string.replace(".","").replace(",",".")
        else:
            number_string = number_string.replace(",","")
    elif has_comma:
        if re.search(r",\d{1,2}$", number_string):
            number_string = number_string.replace(".","").replace(",",".")
        else:
            number_string = number_string.replace(",","")
    elif has_dot:
        if re.search(r"\.\d{1,2}$", number_string):
            number_string = number_string.replace(",","")
        else:
            number_string = number_string.replace(".","")

    return Decimal(number_string)

def parse_to_decimal(value, precision:Decimal = Decimal("0.01"))->Decimal:
    if pd.isna(value):
        return value
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, (int, float)):
        decimal_value = Decimal(str(value))
    else:
        decimal_value = parse_mixed_number(str(value))
    return decimal_value.quantize(precision, rounding=ROUND_HALF_UP)

def format_currency_ve(value) ->str:
    if pd.isna(value):
        return ""
    d = value if isinstance(value, Decimal) else Decimal(str(value))
    us = f"{d:,.2f}"
    return us.replace(",", "_").replace(".", ",").replace("_", ".")

def clean_numeric_column(data_frame, column_name:str, )->None:
    data_frame[column_name] = data_frame[column_name].map(parse_to_decimal)

def intersection_of_payments(requested_payment_data:pd.DataFrame, requested_payment_row:str, recieved_payment_data:pd.DataFrame, recieved_payment_row:str):
    intersection_dataframe = recieved_payment_data[recieved_payment_data[recieved_payment_row].isin(requested_payment_data[requested_payment_row])]
    return intersection_dataframe

def data_to_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()

def normalize_reference(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if "." in value:
        value = value.split(".", 1)[0].strip()
    if not value.isdigit():
        raise ValueError(f"Invalid transaction reference: {value}")
    return value.zfill(8)
