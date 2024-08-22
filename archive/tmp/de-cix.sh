curl -s https://www.de-cix.net/participants_FRA.json | jq '.' | grep -E "\"asnum\"\:" | cut -d ':' -f2 | sed 's/,//' | sed 's/\ /AS/' | sed '1 i\begin' | sed -e "\$aend" > de-cix_fra_asn
netcat whois.cymru.com 43 < de-cix_fra_asn > asn_connected_on_de-cix_fra
cat asn_connected_on_de-cix_fra | rev | cut -d ',' -f1 | rev | sort | uniq -c | sort -k1 -n | grep -v Bulk > asn_connected_on_de-cix_fra_summary
