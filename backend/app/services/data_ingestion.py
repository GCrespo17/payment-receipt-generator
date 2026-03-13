import pandas as pd
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import re


"""
 CREATION OF BASIC ETL
   THIS PROGRAM EXTRACTS DATA FROM EXCEL FILES AND GENERATES A PDF
   BASED ON DEMANDED INFORMATION
"""

def extract_sheet_names_from_excel(excel_path:Path)->list[str]:
    sheet_names = pd.ExcelFile(excel_path).sheet_names
    return sheet_names

def extract_data_from_excelsheet(excel_path:Path, sheet_name:str, header_row_index=0)->pd.DataFrame:
    sheet_dataframe = pd.read_excel(excel_path, sheet_name = sheet_name, skiprows=header_row_index)
    return sheet_dataframe

def extract_column_names(data:pd.DataFrame)->list[str]:
    return list(data.columns)

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

def clean_numeric_column(data_frame:pd.DataFrame, column_name:str, )->None:
    data_frame[column_name] = data_frame[column_name].map(parse_to_decimal)


