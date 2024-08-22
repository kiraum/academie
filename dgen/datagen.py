""" Datagen """

import asyncio
import json
import os
import sys

import aiohttp
import backoff
import requests
import yaml


class RetryMeta(type):
    """
    A metaclass that applies retry logic to all callable methods of a class using backoff.

    This metaclass enhances methods to retry up to 5 times upon `requests.exceptions.RequestException`,
    using an exponential backoff strategy. It automatically decorates all methods that are not special
    methods (not starting with '__').

    Attributes:
        name (str): The name of the class.
        bases (tuple): The base classes of the class.
        dct (dict): The dictionary containing the class's attributes.

    Returns:
        type: The new class with modified methods.
    """

    def __new__(mcs, name, bases, dct):
        for key, value in dct.items():
            if callable(value) and not key.startswith("__"):
                dct[key] = backoff.on_exception(
                    backoff.expo, requests.exceptions.RequestException, max_tries=5
                )(value)
        return type.__new__(mcs, name, bases, dct)


class Datagen(metaclass=RetryMeta):
    """
    A class for generating and processing data related to Internet Exchange Points (IXPs).

    This class uses asynchronous methods to fetch and process data from various sources,
    including route servers, ASN details, and WHOIS information. It implements retry logic
    using the RetryMeta metaclass for improved reliability in network operations.

    Methods:
        alice_host: Process data for a specific IXP.
        process_route_server: Handle data for individual route servers.
        get_asn_details: Retrieve detailed information for ASNs.
        alice_rs: Fetch route server information.
        alice_neighbours: Get neighbor information for a route server.
        alice_routes: Retrieve routes for a specific neighbor.
        caida_asn_whois: Fetch WHOIS information from CAIDA.
        ripe_asn_name: Get ASN name from RIPE database.
        create_report: Generate a shareable report of the processed data.
        process_all_ixps_concurrently: Handle multiple IXPs concurrently.

    The class uses asynchronous programming patterns for efficient data retrieval
    and processing, making it suitable for handling large-scale IXP data operations.
    """

    def __init__(self):
        pass

    async def alice_host(self, url):
        """
        Process data for a specific Internet Exchange Point (IXP) host.

        This method fetches and processes data from route servers, retrieves ASN details,
        and generates a comprehensive report for the given IXP.

        Args:
            url (str): The URL of the IXP host to process.

        Returns:
            None

        Side effects:
            - Prints processed data to console.
            - Creates a shareable report link.
            - Writes report to files in both text and JSON formats.

        The method performs the following steps:
        1. Fetches route server information.
        2. Processes each route server concurrently.
        3. Retrieves detailed ASN information.
        4. Compiles all data into a formatted text report.
        5. Generates a shareable report link.
        6. Writes the report to files.

        This is an asynchronous method that utilizes concurrent processing for efficiency.
        """
        origin_asns = {}
        text = []
        fname = url.replace("https://", "")
        rs_list = await self.alice_rs(url)
        # rs_list = {'cw-rs1-v4': 'lg.ams-ix.net => CW', 'cw-rs2-v4': 'lg.ams-ix.net => CW'}

        tasks = [
            self.process_route_server(url, rs, group, origin_asns)
            for rs, group in rs_list.items()
        ]
        await asyncio.gather(*tasks)

        text.append("IXP ; ASN ; AS-NAME ; AS Rank ; Source ; Country ; PeeringDB link")

        asn_details_tasks = [
            self.get_asn_details(asn, group)
            for group, asns in origin_asns.items()
            for asn in asns
        ]
        asn_details = await asyncio.gather(*asn_details_tasks)

        for detail in asn_details:
            text.append(detail)

        print("\n".join(map(str, text)))
        report_link = await self.create_report("\n".join(map(str, text)))
        print("=" * 80)
        print(f"We created a sharable report link, enjoy => {report_link}")
        await self.write_report_to_file(fname, "\n".join(map(str, text)), as_json=False)
        await self.write_report_to_file(fname, "\n".join(map(str, text)), as_json=True)

    async def process_route_server(self, url, route_server, group, origin_asns):
        """
        Process a single route server for an Internet Exchange Point (IXP).

        This method fetches neighbor information and routes for a specific route server,
        and updates the origin ASNs dictionary with new ASNs found.

        Args:
            url (str): The base URL of the IXP.
            route_server (str): The identifier of the route server to process.
            group (str): The group identifier for this route server.
            origin_asns (dict): A dictionary to store the origin ASNs, updated in-place.

        Returns:
            None

        Side effects:
            - Prints progress information to console.
            - Updates the origin_asns dictionary with new ASNs found.
            - Introduces a 60-second delay after processing.

        The method performs the following steps:
        1. Fetches the list of neighbors for the route server.
        2. Retrieves routes for the route server and its neighbors.
        3. Updates the origin_asns dictionary with new ASNs if found.
        4. Waits for 60 seconds before completing (non-blocking).

        This is an asynchronous method that allows for concurrent processing of multiple route servers.
        """
        print(f"Working on {url} - {route_server}")
        neighbours_list = await self.alice_neighbours(url, route_server)
        new_asns = await self.alice_routes(url, route_server, neighbours_list)
        if new_asns:
            origin_asns[group] = list(set(new_asns))

        if origin_asns is None:
            return

        await asyncio.sleep(60)  # Non-blocking sleep

    async def get_asn_details(self, asn, group):
        """
        Retrieve detailed information for a specific ASN.

        Args:
            asn (int): The Autonomous System Number to query.
            group (str): The group identifier for this ASN.

        Returns:
            str: A formatted string containing ASN details.

        This method fetches ASN details from CAIDA and RIPE databases, handling special cases
        like private ASNs. It formats the information into a single string for reporting.
        """
        if asn != 64567:  # AMS-IX using private ASN
            details = await self.caida_asn_whois(asn)
            asn_name = await self.ripe_asn_name(asn)
            await asyncio.sleep(0.5)  # Non-blocking sleep
        else:
            asn_name = "AMS-IX"
            details = {
                "asnName": "Private ASN",
                "rank": "NA",
                "source": "NA",
                "country": {"iso": "NL"},
            }

        if not asn_name:
            asn_name = "NA"

        if not details:
            details = {
                "rank": "NA",
                "source": "NA",
                "country": {"iso": "NA"},
            }

        return (
            f"{group} ; {asn} ; {asn_name} ; {details['rank']} ; {details['source']} ; {details['country']['iso']} "
            f"; https://www.peeringdb.com/asn/{asn}"
        )

    def parse_text_to_json(self, data_text):
        """
        Convert a list of delimited text data into a list of dictionaries.

        Args:
            data_text (str): A string containing multiple lines of data, each line is a delimited record.

        Returns:
            list: A list of dictionaries with parsed data.
        """
        lines = data_text.strip().split("\n")
        headers = [header.strip() for header in lines[0].split("|")]
        json_data = []

        for line in lines[1:]:
            values = [value.strip() for value in line.split("|")]
            entry = dict(zip(headers, values))
            json_data.append(entry)
        return json_data

    async def write_report_to_file(self, fname: str, data: list, as_json: bool = False):
        """
        Write data to a file, creating the necessary directories if they do not exist.
        The data can be written as plain text or as JSON.

        Args:
            fname (str): The filename (without extension) where the data will be saved.
            data (list): A list of data entries, each entry can be a string or a dictionary.
            as_json (bool): If True, writes the data in JSON format. Otherwise, writes as plain text.

        Example:
            write_report_to_file("2023-01-01_report", data, as_json=True)
        """
        extension = "json" if as_json else "txt"
        fwrite = f"reports/{fname}.{extension}"

        os.makedirs(os.path.dirname(fwrite), exist_ok=True)

        with open(fwrite, "w", encoding="utf8") as tfile:
            if as_json:
                data = self.parse_text_to_json(data)
                json.dump(data, tfile, indent=4)
            else:
                tfile.write(data)

    async def alice_rs(self, url):
        """
        Fetch route server information for a given IXP URL.

        Args:
            url (str): The base URL of the IXP.

        Returns:
            dict: A dictionary mapping route server IDs to their group information.

        Raises:
            SystemExit: If the API response is not successful (non-200 status code).
        """
        url_ixp = url.replace("https://", "")
        url = f"{url}/api/v1/routeservers"
        timeout = aiohttp.ClientTimeout(total=600)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    rs_dict = {}
                    data = await response.json()
                    for rserver in data["routeservers"]:
                        rs_dict[rserver["id"]] = url_ixp + " => " + rserver["group"]
                else:
                    print("ERROR | HTTP status != 200 - alice_rs")
                    sys.exit(1)
        return rs_dict

    async def alice_neighbours(self, url, route_server):
        """
        Get neighbor information for a specific route server.

        Args:
            url (str): The base URL of the IXP.
            route_server (str): The identifier of the route server.

        Returns:
            list or None: A list of neighbor IDs if successful, None if there's an error.

        Side effects:
            - Prints error messages to console if the request fails.
        """
        print(f"Getting neighbours for {route_server}")
        url = f"{url}/api/v1/routeservers/{route_server}/neighbors"
        with requests.Session() as session:
            response = session.get(url, timeout=600)
        if response.status_code == 200:
            neighbour_list = []
            data = response.json()
            if "neighbors" in data:
                neigh = "neighbors"
            else:
                neigh = "neighbours"
            for neighbour in data[neigh]:
                neighbour_list.append(neighbour["id"])
        else:
            print(
                "ERROR | HTTP status != 200 - alice_neighbours"
                f" - Error {response.status_code}: {url} - {route_server}"
            )
            if response.status_code == 500:
                neighbour_list = None
        return neighbour_list

    async def alice_routes(self, base_url, route_server, neighbours):
        """
        Retrieve routes for a specific route server and its neighbors.

        Args:
            base_url (str): The base URL of the IXP.
            route_server (str): The identifier of the route server.
            neighbours (list): A list of neighbor IDs.

        Returns:
            list or None: A list of unique origin ASNs if successful, None if there's an error.

        Side effects:
            - Prints progress and error messages to console.
            - Introduces a 1-second delay between processing each neighbor.
        """
        if neighbours is None:
            print(
                f"WARNING: No neighbours found for route server {route_server}. Skipping."
            )
            return None

        origin_asn_list = []
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for neighbour_id in neighbours:
                await asyncio.sleep(1)
                print(f"Getting routes for {route_server} - {neighbour_id}")
                url = f"{base_url}/api/v1/routeservers/{route_server}/neighbors/{neighbour_id}/routes"

                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            for route in data["imported"] + data["filtered"]:
                                origin_asn_list.append(route["bgp"]["as_path"][-1])
                        else:
                            print(
                                f"ERROR | HTTP status {response.status} - alice_routes: {url} - {route_server} - {neighbour_id}"
                            )
                            if response.status == 500:
                                return None
                except aiohttp.ClientError as e:
                    print(f"Error fetching routes: {e}")
                    return None

        return list(set(origin_asn_list)) if origin_asn_list else None

    async def caida_asn_whois(self, asn):
        """
        Fetches WHOIS information for a specified ASN from the CAIDA AS Rank API.

        Args:
            asn (int): The Autonomous System Number to query.

        Returns:
            dict: WHOIS information if the request is successful, None otherwise.

        Raises:
            KeyError: If expected data keys are missing in the response.
            SystemExit: If the API response is not successful (non-200 status code).
        """
        url = f"https://api.asrank.caida.org/v2/restful/asns/{asn}"
        result = None
        with requests.Session() as session:
            response = session.get(url, timeout=600)
        if response.status_code == 200:
            data = response.json()
            try:
                result = data["data"]["asn"]
            except KeyError:
                print(f"ASN {asn} has no data at whois!")
                raise
        else:
            print(
                "ERROR | HTTP status != 200 - caida_asn_whois"
                f" - Error {response.status_code}: {asn}"
            )
            sys.exit(1)
        return result

    async def ripe_asn_name(self, asn):
        """
        Fetches the holder name of the specified ASN from RIPE's API.

        Args:
            asn (str): The ASN number as a string.

        Returns:
            str or None: The holder name of the ASN if available, otherwise None.

        Raises:
            KeyError: If the ASN data is missing in the API response.
            SystemExit: If the API response status is not 200.
        """
        url = f"https://stat.ripe.net/data/as-overview/data.json?resource={asn}"
        result = None
        with requests.Session() as session:
            response = session.get(url, timeout=600)
        if response.status_code == 200:
            try:
                result = response.json()["data"]["holder"]
            except KeyError:
                print(f"ASN {asn} has no data at whois!")
                raise
        else:
            print(
                "ERROR | HTTP status != 200 - ripe_asn_name"
                f" - Error {response.status_code}: {asn}"
            )
            sys.exit(1)
        return result

    async def create_report(self, data):
        """
        Create a pastebin-like report using glot.io API.

        Args:
            data (str): The data to include in the report.

        Returns:
            str: URL of the created report.
        """
        url = "https://glot.io/api/snippets"
        report_url = None
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "language": "plaintext",
            "title": "Report",
            "public": True,
            "files": [{"name": "report.txt", "content": data}],
        }

        response = requests.post(url, headers=headers, json=payload, timeout=600)
        if response.status_code == 200:
            report_url = f"https://glot.io/snippets/{response.json()['id']}"
        else:
            print("ERROR | HTTP status != 200 - create_report")
            sys.exit(1)
        return report_url

    def load_yaml(self):
        """
        Load a YAML config file.

        Returns:
            dict: Dictionary containing the YAML config data.
        """
        with open("pgossip/config.yaml", "r", encoding="utf8") as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
        return data

    async def process_all_ixps_concurrently(self, ixps):
        """
        Asynchronously processes each IXP in the provided list concurrently by calling the alice_host method.

        Args:
            ixps (dict): A dictionary containing a list of IXPs under the key "ixps".
        """
        tasks = [self.alice_host(ixp) for ixp in ixps["ixps"]]
        await asyncio.gather(*tasks)
