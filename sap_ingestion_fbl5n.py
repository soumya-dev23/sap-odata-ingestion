import os
import time
import requests
import urllib3
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SAP_USER = "********"
SAP_PASS = "*************"

# Base URL pointing to the correct EntitySet
url = "https://206.1.15.190:443/sap/opu/odata/sap/ZCUSTOMER_FBL5N_SRV_01/CustomerItemSet"
output_file = "sap_zfbl5n_prd_all.csv"

# Remove existing file if open/present
if os.path.exists(output_file):
    try:
        os.remove(output_file)
    except PermissionError:
        print(f"ERROR: Close {output_file} before running.")
        exit()

# Generator function to fetch data page-by-page from SAP on demand
def fetch_sap_generator(base_url, batch_size=100, max_retries=3):
    session = requests.Session()
    session.auth = (SAP_USER, SAP_PASS)
    session.verify = False
    session.headers.update({"Accept": "application/json"})
    
    skip = 0
    while True:
        # Query parameters including pagination ($skip)
        params = {
            "sap-client": "700",
            "$filter": "BUKRS eq 'LUX2' and KUNNR eq 'JAB0200'",
            "$top": str(batch_size),
            "$skip": str(skip),
            "$inlinecount": "allpages",
            "$format": "json"
        }
        
        response = None
        success = False
        retry_delay = 2  # Initial wait time in seconds for exponential backoff
        
        # Retry loop for the current batch
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Fetching batch from SAP (skip: {skip}) [Attempt {attempt}/{max_retries}]...")
                response = session.get(base_url, params=params, timeout=(30, 180))
                
                # Raise an HTTPError for bad responses (4xx or 5xx)
                response.raise_for_status()
                success = True
                break  # Exit retry loop on success
                
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")
                if response is not None:
                    print(f"Response details: {response.text}")
            except requests.exceptions.RequestException as err:
                print(f"A network or request error occurred: {err}")
            
            # If we haven't succeeded and have retries left, wait before trying again
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Double the wait time (Exponential Backoff)
        
        # If all retries failed for this batch, abort the generator
        if not success:
            print(f"Failed to fetch batch at skip {skip} after {max_retries} attempts. Aborting.")
            break
            
        data = response.json()
        # Alternatively: data = json.loads(response.text)
        records = data.get("d", {}).get("results", [])
        
        # Stop generator if no more records are returned
        if not records:
            break
            
        # Yield the current batch of records (saves memory!)
        yield records
        
        # If the returned batch is smaller than the requested batch size, we've hit the end
        if len(records) < batch_size:
            break
            
        skip += batch_size

# Consuming the generator and writing data incrementally to CSV
total_rows = 0
first_batch = True

print("Starting generator-based download from SAP...")
for batch_records in fetch_sap_generator(url, batch_size=100):
    df = pd.DataFrame(batch_records)
    
    # Remove technical metadata column if present
    if "__metadata" in df.columns:
        df = df.drop(columns=["__metadata"])
        
    # Append batch to CSV (write header only on the first pass)
    df.to_csv(output_file, mode='a', index=False, header=first_batch, encoding="utf-8-sig")
    
    first_batch = False
    total_rows += len(df)

if total_rows > 0:
    print(f"Successfully saved a total of {total_rows} rows to {output_file}.")
else:
    print("No records returned by SAP.")