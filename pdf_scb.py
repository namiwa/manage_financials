import argparse
import os
import pdfplumber
import camelot 
import fitz
import pandas as pd


def get_path(statement_path: str):
  full_path = os.path.abspath(statement_path)
  if not os.path.exists(full_path):
    raise Exception("File does not exists")
  
  return full_path


def parse_file_with_plumber(statement_path: str):
  full_path = get_path(statement_path) 
  all_dfs = []
    
  with pdfplumber.open(full_path) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
      # extract tables
      print(f"processing page: {page_num}")
      tables = page.extract_tables()

      for table_indx, table in enumerate(tables, start=1):
        if table:
          print(f"table in page: {page_num}, {table}")
          # do clean up for this
          df = pd.DataFrame(table[1:], columns=table[0])
          df["page_num"] = page_num
          df["table_num"] = table_indx
          all_dfs.append(df)
  
  if all_dfs:
    final_df = pd.concat(all_dfs, ignore_index=True)
    print(final_df.head())
  else:
    print("No tables found")


def parse_file_with_camelot(path: str):
  statement_path = get_path(path)
  tables = camelot.read_pdf(statement_path, pages="all", flavor="lattice", process_background=True)
  store = []
  prev_balance = None 
  for ind, table in enumerate(tables[1:]):
    print(f"processing table: {ind}")
    if ind == 0:
      prev_balance = float(table.df.iloc[1][3]) 
      table.df = table.df.iloc[2:]
    
    store.append(table.df)
  
  final_df = pd.concat(store, ignore_index=True)
  final_df = final_df.rename(columns={0: "start", 1: "end", 2: "description", 3: "amount"})
  final_df.loc[final_df["amount"].str.contains("CR"), "amount"] = "-" + final_df["amount"].str.removesuffix("CR")
  final_df["amount"] = pd.to_numeric(final_df["amount"], errors="coerce")
  final_df = final_df[final_df["start"] != ""]
  # data clean up


  print(final_df.head())
  print(final_df.describe())
  print(final_df.tail())
  print(f"prev balance: {prev_balance}")
  total_debit = final_df.loc[final_df["amount"] > 0, "amount"].sum()
  total_credit = final_df.loc[final_df["amount"] < 0, "amount"].sum()
  print(f"total credit {total_credit} total debit {total_debit} total {total_debit + total_credit}")

  final_df.to_csv("./july.csv", index=False)


def parse_csv(statement_path: str):
  statement_path = get_path(statement_path)
  df = pd.read_csv(statement_path, skip_blank_lines=True, skipfooter=6, header=2)
  df = df.rename(columns={"Date": "date", "DESCRIPTION": "description", "Foreign Currency Amount": "fca", "SGD Amount": "amount"})

  # clean date
  df['date'] = df["date"].str.strip("\t").str.strip(" ")
  df['date'] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")

  # clean credit and debit
  df.loc[df["amount"].str.contains("DR"), "amount"] = df["amount"].str.removesuffix("DR").str.removeprefix("SGD").str.strip(" ")
  df.loc[df["amount"].str.contains("CR"), "amount"] = "-" + df["amount"].str.removesuffix("CR").str.removeprefix("SGD").str.strip(" ")
  df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

  df = df[["date", "description", "amount"]]

  print(df.head())
  print(df.describe())
  print(df.tail())
  total_debit = df.loc[df["amount"] > 0, "amount"].sum()
  total_credit = df.loc[df["amount"] < 0, "amount"].sum()
  print(f"total credit {total_credit} total debit {total_debit} total {total_debit + total_credit}")


def main():
  parser = argparse.ArgumentParser() 
  parser.add_argument("statement_path")

  args = parser.parse_args()
  
  # parse_file_with_plumber(args.statement_path)
  # parse_file_with_camelot(args.statement_path)
  parse_csv(args.statement_path)


if __name__ == "__main__":
  main()