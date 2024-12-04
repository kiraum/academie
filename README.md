# academie

A tool to generate Origin ASN summaries per country using IXP data.

````bash
» python3 datagen.py
usage: datagen.py [-h] [-lg ALICE_URL] [-a]

Datagen - Generate Origin ASN summary per country.

options:
  -h, --help     show this help message and exit
  -lg ALICE_URL  Datagen - Generate Origin ASN summary per country.
  -a             Generate Origin ASN summary per country.for all IXPS @ datagen/config.yaml.
````

## Features

The script provides functionality to:
* Process data from ALICE-LG instances
* Generate Origin ASN summaries per country
* Batch process multiple IXPs concurrently using configuration from datagen/config.yaml

## Configuration

IXP configurations are stored in datagen/config.yaml. The -a flag will process all IXPs defined in this file.

## Examples

Process a single ALICE-LG instance:
````bash
python3 datagen.py -lg https://lg.example.com
````

Process all configured IXPs:
````bash
python3 datagen.py -a
````

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
