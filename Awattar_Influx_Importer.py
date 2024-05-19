import argparse
import logging
import sys
import requests
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


def get_awattar_data(start, end):
    """
    Returns JSON data for electricity prices from Awattar API.

    Parameters:
    api_key (str): API key for Awattar API
    start (str): Start date in YYYY-MM-DD format
    end (str): End date in YYYY-MM-DD format

    Returns:
    dict: JSON data from Awattar API
    """
    url = f"https://api.awattar.de/v1/marketdata?start={start}&end={end}"
    response = requests.get(url)
    data = json.loads(response.text)
    return data

def main(args):

    #initialize the start and end date for the API query
    start = args.startDate
    end = args.endDate

    #setup influx db connection parameters
    influxdb_url = args.influxurl
    influxdb_token = args.influxtoken
    influxdb_org = args.influxorg
    influxdb_bucket = args.influxbucket

    #setup influx db connection 
    client = InfluxDBClient(url=influxdb_url, token=influxdb_token, org=influxdb_org)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    #retrieve data from public Awattar API
    data = get_awattar_data(start, end)

    #iterate over the returned data, create a point and insert the point into grafana
    for item in data["data"]:
        price_eur_per_mwh = item["marketprice"]
        price_eur_per_kwh = price_eur_per_mwh / 1000.0
        price_cent_per_kwh = price_eur_per_kwh * 100.0
        timestamp = int(item["start_timestamp"])*1000000
        point = Point("electricity_prices_awattar") \
            .time(timestamp) \
            .field("price", price_cent_per_kwh)
        write_api.write(bucket=influxdb_bucket, record=point)
        print(point)
    print("Data written to InfluxDB.")

if __name__ == '__main__':
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='An importer for Grafana, which uses the public Awattar API to retrieve the electricity prices for a given date')

    # Add command-line arguments
    parser.add_argument('-f','--startDate', required=True,  help='The start date for the Awattar API Call in the format YYYY-MM-DD')
    parser.add_argument('-t','--endDate', required=True,  help='The end date for the Awattar API Call in the format YYYY-MM-DD')

    parser.add_argument('-fu','--influxurl', required=True,  help='The URL of the influxdb in the format IP:PORT')
    parser.add_argument('-ft','--influxtoken', required=True,  help='The autorisation token for the influxdb')
    parser.add_argument('-fo','--influxorg', required=True,  help='The influxdb org')
    parser.add_argument('-fb','--influxbucket', required=True,  help='The bucket to store the information in')

    parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity.')

    # Parse command-line arguments
    args = parser.parse_args()

    # Check if there are any arguments
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Call the main function
    main(args)