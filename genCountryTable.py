import os
import pandas as pd

def genTable():
    # Source for 2 digit ISO codes for countries
    url = "https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2"

    try:
        os.mkdir("data")
    except FileExistsError:
        pass
    except Exception as e:
        print(e)
        exit(1)
    finally:
        os.chdir("data")

    # Get country data/list from the third table on the page
    df = pd.read_html(url)[2]

    # Delete extra columns
    df.drop(df.columns[2:], axis=1, inplace=True)

    filename = "countries.csv"
    filepath = os.path.join(os.getcwd(), filename)

    df.to_csv(filepath)
    return df

def main():
    df = genTable()
    print(df.head(3))

if __name__ == '__main__':
    main()
