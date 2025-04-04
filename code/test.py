import pandas as pd

date = '2025-03-04'
start_date = pd.to_datetime(date)
end_date = start_date + pd.Timedelta(days=1)
print(start_date)
print(end_date)