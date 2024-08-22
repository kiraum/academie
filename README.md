# academie

TDB

### archive

Old code, just adding it here for historical reasons, the code doesn't work anymore (data sources missing) and it's not planned to be fixed.

This script performs various data collection and processing tasks related to internet exchange points (IXPs) and autonomous systems (ASNs)

Main functions:
 1. Fetch and process ASN data from DE-CIX Frankfurt
 2. Fetch and process ASN data from AMS-IX
 3. Fetch and process ASN data from IX.br (Brazilian Internet Exchange) or multiple locations
 4. Fetch RIR (Regional Internet Registry) WHOIS data
 5. Fetch CC2ASN (Country Code to ASN) data
 6. Fetch and process IX.br looking glass data
 7. Generate ASN to country code mappings
 8. Summarize ASN to country code and RIR mappings
 9. Process state information for Brazilian ASNs
 The script can be run with different command-line arguments to execute pecific functions or run all tasks in sequence
 When run with the "run" argument, it performs the following sequence:
 - Fetch data from DE-CIX, AMS-IX, and IX.br
 - Fetch WHOIS and CC2ASN data
 - Process looking glass data
 - Generate reports and summaries for collected data
 The script creates various data files and reports in the "data" and "report" directories
