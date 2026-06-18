from normalize import normalize_ticker, normalize_year

print("--- Ticker tests ---")
print(repr(normalize_ticker("tcs")))
print(repr(normalize_ticker("  TCS  ")))
print(repr(normalize_ticker("Adani Ports & Special Economic Zone Ltd\n")))

print()
print("--- Year tests ---")
print(normalize_year("Mar-23"))
print(normalize_year("FY24"))
print(normalize_year("2023"))
print(normalize_year("Dec-22"))
print(normalize_year("garbage"))
