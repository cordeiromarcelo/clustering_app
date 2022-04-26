import pandas as pd


def parseCSV(filePath):
    # CVS Column Names
    col_names = ['first_name', 'last_name', 'address', 'street', 'state', 'zip']
    # Use Pandas to parse the CSV file
    csvData = pd.read_csv(filePath, names=col_names, header=None)
    # Loop through the Rows
    for i, row in csvData.iterrows():
        print(i, row['first_name'], row['last_name'], row['address'], row['street'], row['state'], row['zip'], )

    return csvData
