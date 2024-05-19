import argparse
import logging
import sys
from Custom_print import print_status_message
import Evn_Wrapper;
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


def main(args):

    #setup influx db connection parameters
    influxdb_url = args.influxurl
    influxdb_token = args.influxtoken
    influxdb_org = args.influxorg
    influxdb_bucket = args.influxbucket

    #setup influx db connection 
    client = InfluxDBClient(url=influxdb_url, token=influxdb_token, org=influxdb_org)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    #create new EVN smartmeter object
    evn = Evn_Wrapper.EVNAccount()
    user=args.user
    password=args.password

    #authenticate to the smartmeter API
    evn.authenticate(user,password)

    # Output details about the metering point
    print_status_message("Meteringpoint ID: "+evn.get_metering_point_id(),"info")
    print_status_message("Account ID: "+ evn.get_accountID(),"info")

    #retrieve relevant technical parameters for the specified metering point

    if evn.get_Smartmeter() is None:
        print_status_message("No Smartmeter installed", "error")
        return
    print_status_message("Smartmeter installed", "success")


    if evn.get_Communicative() is None:
        print_status_message("Smartmeter is installed but not communicative","error")
        return
    print_status_message("Smartmeter is communicative","success")

    if  evn.get_Optin() is None:
        print_status_message("Opt-In is not enabled","error")
        return
    print_status_message("Opt-in enabled, we can work with 15min values :)","success")
        
    
    consumption_per_day = evn.get_consumption_per_day(args.day)
    for date_str, consumption in consumption_per_day:
        if date_str is not None:
            print(f"Timestamp: {date_str}\nConsumption: {consumption}\n")
            point = Point("measurements") \
            .time(date_str) \
            .field("measure", consumption)
            write_api.write(bucket=influxdb_bucket, record=point)
            print(point)


if __name__ == '__main__':
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='An importer for Grafana, which uses the EVN Wrapper to connect to the EVN API.')


    # Add command-line arguments
    parser.add_argument('-u','--user', required=True, help='The username for the EVN smartmeter portal')
    parser.add_argument('-p','--password', required=True,  help='The password for the EVN smartmeter portal')
    parser.add_argument('-d','--day', required=True,  help='The day for which the 15 minute measurements are retrieved')

    parser.add_argument('-fu','--influxurl', required=True,  help='The URL of the influxdb in the format IP:PORT')
    parser.add_argument('-ft','--influxtoken', required=True,  help='The autorisation token for the influxdb')
    parser.add_argument('-fo','--influxorg', required=True,  help='The influxdb org')
    parser.add_argument('-fb','--influxbucket', required=True,  help='The bucket to store the information in')

    parser.add_argument('-mID','--meteringPointID',required=False, help='The ID of the meter, if no ID is set the ID will be retrieved automatically')
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