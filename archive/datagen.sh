#!/bin/sh

# Function to fetch DE-CIX API data
get_data_decix_api() {
    echo "getting de-cix api data... - $(date)"
    mkdir -p data

    # Fetch and process DE-CIX Frankfurt ASN data
    curl -s https://www.de-cix.net/participants_FRA.json | jq '.' | grep -E "\"asnum\"\:" | cut -d ':' -f2 | sed 's/,//' | sed 's/\ /AS/' > data/de-cix_fra_asn.latest
}

# Function to fetch AMS-IX API data
get_data_amsix_api() {
    echo "getting ams-ix api data... - $(date)"
    mkdir -p data

    # Fetch and process AMS-IX ASN data
    curl -s https://my.ams-ix.net/api/v1/members.ascii?exchange=NL | grep asnum | awk '{print $2}' | sed 's/^/AS/' | sort | uniq > data/ams-ix_asn.latest
}

# Function to get IX.br locations
get_ixbr_loc() {
    curl -s http://ix.br/localidades/atuais | grep "adesao/" | tr '=' '\n' | grep adesao | cut -d '/' -f3
}

# Function to fetch IX.br site data for all locations
get_data_ixbr_site() {
    mkdir -p data

    locs=$(get_ixbr_loc)

    for loc in $locs
    do  
        echo "getting ixbr $loc site data... - $(date)"
        curl -s "http://ix.br/particip/$loc" | grep "ok.gif" | cut -d '>' -f3 | cut -d '<' -f1 | sed 's/^/AS/' | sed 's/*//' > "data/ixbr_${loc}_asn.latest"
    done
}

# Function to fetch RIR WHOIS data
get_data_whois() {
    echo "getting rirs whois data... - $(date)"
    mkdir -p db/whois

    cd db/whois
    wget -q ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest -O delegated-arin-extended-latest
    wget -q ftp.ripe.net/ripe/stats/delegated-ripencc-latest -O delegated-ripencc-latest
    wget -q ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-latest -O delegated-afrinic-latest
    wget -q ftp.apnic.net/pub/stats/apnic/delegated-apnic-latest -O delegated-apnic-latest
    wget -q ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest -O delegated-lacnic-latest
    cd ../..
}

# Function to fetch CC2ASN data
get_data_cc2asn() {
    echo "getting cc2asn data... - $(date)"
    mkdir -p db/cc2asn

    cd db/cc2asn
    wget -q www.cc2asn.com/data/db.tar.gz -O db.tar.gz
    tar zxf db.tar.gz
    cd ../..
}

# Function to fetch IX.br looking glass data
get_data_lg() {
    if [ -z "$1" ]
    then
        echo "missing loc..."
        exit 1
    fi
    
    echo "getting ixbr $1 lg data - $(date)"
    mkdir -p db/lg
    { echo "terminal length 0"; sleep 2; echo "show ip bgp"; sleep 295; } | telnet "lg.$1.ptt.br" > "db/lg/lgbgp_$1"
}

# Function to format IX.br SP connected ASN data
format_lg_bgp_table_connected() {
    echo "formatting lg ixbr sp connected asn - $(date)"
    if [ ! -f "data/lgbgp" ]; then
        echo "missing bgp table file..."
        exit 1
    fi

    echo "" > /tmp/bgptable_connected

    while read line
    do
        network=$(echo "$line" | grep ^* | awk '{print $2}')
        if echo $network | grep -vEq '187.16.2[1][0-9]|187.16.2[2][0-3]'
        then
            last=$network
        else
            network=$last
        fi
        as=$(echo "$line" | grep ^* | sed 's/.*             0 //' | awk '{print $1}')
        if [ -n "$network" ] || [ -n "$as" ]
        then
            echo $as"|"$network >> /tmp/bgptable_connected
        fi
    done < data/lgbgp
    cat /tmp/bgptable_connected | cut -d '|' -f1 | sort | uniq | awk 'NF>0' | sed 's/^/AS/' > data/ixbr_sp_asn_lg_connected
}

# Function to format IX.br origin ASN data
format_lg_bgp_table_origin() {
    mkdir -p data

    locs="sp rj"

    for loc in $locs
    do
        get_data_lg $loc
        echo "formatting lg ixbr $loc origin asn - $(date)"
        echo "" > "db/lg/bgptable_$loc"

        while read line
        do
            network=$(echo "$line" | grep ^* | awk '{print $2}')
            if echo $network | grep -vEq '^187.16.2[1][0-9]|^187.16.2[2][0-3]|^200.219.130|^200.219.131|^200.219.138|^45.6.5[2-5]|^200.219.139|^200.219.140|^200.219.141|^200.219.143|^200.219.144|^200.219.145|^200.219.146|^200.219.147|^200.192.108|^200.192.109|^200.192.110|^200.192.111|^187.16.192|^187.16.193|^187.16.194|^187.16.195|^187.16.196|^187.16.197|^187.16.198|^187.16.199|^187.16.200|^187.16.201|^187.16.202|^187.16.203|^187.16.204|^187.16.205|^45.227.0'
            then
                last=$network
            else
                network=$last
            fi
            roa=$(echo "$line" | grep ^* | awk '{print $(NF-1)}' | sed 's/{//' | sed 's/}//')
            if [ -n "$network" ] || [ -n "$roa" ]
            then
                if echo "$roa" | grep -Eq ","
                then
                    roas=$(echo "$roa" | sed 's/,/ /g')
                    for roa in $roas
                    do
                        echo $roa"|"$network >> "db/lg/bgptable_$loc"
                    done
                else
                    echo $roa"|"$network >> "db/lg/bgptable_$loc"
                fi
            fi
        done < "db/lg/lgbgp_$loc"
        cat "db/lg/bgptable_$loc" | cut -d '|' -f1 | sort | uniq | awk 'NF>0' | sed 's/^/AS/' > "data/ixbr_${loc}_asn_lg_origin"
    done
}

# Function to generate ASN to country code mapping
generate_asn_cc() {
    if [ -z "$1" ]
    then
        echo "missing file to format..."
        exit 1
    fi
    
    while read as
    do
        asn=$(echo $as | sed 's/AS//')
        cc=$(grep -Ri "|asn|$asn|" ../db/whois/ | grep asn | cut -d ':' -f2 | cut -d '|' -f2 | awk '{print tolower($0)}' | xargs -n1 | sort -u | xargs)
        if [ -n "$cc" ]
        then
            echo $as"|"$cc"|whois"
        fi
        if [ -z "$cc" ]
        then
            cc=$(grep -Ri ^$as$ ../db/cc2asn/ | cut -d '/' -f2 | cut -d '_' -f1 | awk '{print tolower($0)}' | xargs -n1 | sort -u | xargs)
            if [ -n "$cc" ]
            then
                echo $as"|"$cc"|cc2asn"
            fi
        fi
        if [ -z "$cc" ]
        then
            cc=$(whois -h whois.cymru.com " -v $as" | grep ^[0-9] | awk '{print $3}' | awk '{print tolower($0)}' | xargs -n1 | sort -u | xargs)
            if [ -n "$cc" ]
            then
                if [ "$cc" = "|" ]
                then
                    cc=""
                else
                    echo $as"|"$cc"|cymrus"
                fi
            fi
        fi
        if [ -z "$cc" ]
        then
            cc=$(curl -s https://ipinfo.io/$as | grep -A1 "<td>Country</td>" | tail -1 | cut -d '/' -f3 | cut -d '"' -f1 | awk '{print tolower($0)}')
            if [ -z "$cc" ]
            then
                echo $as"|null|missing"
            else
                echo $as"|"$cc"|ipinfo"
            fi
        fi
    done < "$1"
}

# Function to summarize ASN to country code mapping
asn_cc() {
    grep -Ri asn db/whois/ | grep -vE 'summary|available|reserved' |  cut -d '|' -f2 | grep -E '^[A-Za-z]' | awk 'NF>0' |  awk '{print tolower($0)}' | sort | uniq -c | awk '{print $2"|"$1}' | sort -k2 -rn -t "|"
}

# Function to summarize ASN to RIR mapping
asn_rir() {
    grep -Ri asn db/whois/ | grep -vE 'summary|available|reserved' | cut -d ':' -f2 | cut -d '|' -f1 | grep -E '^[A-Za-z]' | awk 'NF>0' |  awk '{print tolower($0)}' | sort | uniq -c | awk '{print $2"|"$1}' | sort -k2 -rn -t "|" 
}

# Function to get state information for Brazilian ASNs
asn_state() {
    if [ -z "$1" ]
    then
        echo "missing file to format..."
        exit 1
    fi

    asns=$(grep "|br|" "$1" | cut -d'|' -f1 | sed 's/^AS//')

    for asn in $asns
    do
        state=$(grep " $asn |" registro/base.registro | cut -d '|' -f6 | sed 's/ //g' | awk '{print tolower($0)}')
        if [ -z "$state" ]
        then
            echo "na"
        else
            echo $state
        fi
    done
}

# Function to summarize state information for Brazilian ASNs
asn_state_summary() {
    asn_state "$1" | sort | uniq -c | sort -k1 -nr

    total=$(grep "|br|" "$1" | cut -d'|' -f1 | sed 's/^AS//' | wc -l)
    echo ""
    echo "Total: $total"
}

# Main execution logic
if [ "$1" = "get_data_decix_api" ]
then
    get_data_decix_api
elif [ "$1" = "get_data_amsix_api" ]
then
    get_data_amsix_api
elif [ "$1" = "get_data_ixbr_site" ]
then
    get_data_ixbr_site
elif [ "$1" = "get_data_whois" ]
then
    get_data_whois
elif [ "$1" = "get_data_cc2asn" ]
then
    get_data_cc2asn
elif [ "$1" = "get_data_lg" ]
then
    get_data_lg $2
elif [ "$1" = "format_lg_bgp_table_connected" ]
then
    format_lg_bgp_table_connected
elif [ "$1" = "format_lg_bgp_table_origin" ]
then
    format_lg_bgp_table_origin
elif [ "$1" = "generate_asn_cc" ]
then
    generate_asn_cc $2
elif [ "$1" = "asn_cc" ]
then
    asn_cc
elif [ "$1" = "asn_rir" ]
then
    asn_rir
elif [ "$1" = "asn_state" ]
then
    asn_state "$2"
elif [ "$1" = "asn_state_summary" ]
then
    asn_state_summary "$2"
elif [ "$1" = "run" ]
then
    get_data_decix_api
    get_data_amsix_api
    get_data_ixbr_site
    get_data_whois
    get_data_cc2asn
    format_lg_bgp_table_origin
    echo "generating ixbr aggregate data... - $(date)"
    files=$(ls data)
    for file in $files
    do
        mkdir -p report
        cd data
        echo "formating files to asn|cc|source - $(date)"
        generate_asn_cc "$file" > "../report/${file}_cc"
        cd ../report
        echo "generating report files for $file - $(date)"
        cat "${file}_cc" | cut -d '|' -f2 | tr " " "\n" | awk 'NF>0' | sort | uniq -c | sort -k1 -n > "${file}_cc_summary"
        cat "${file}_cc" | grep "|null|missing" > "${file}_missing_cc"
        cd ..
    done
    cat report/ixbr_*latest_cc | cut -d '|' -f1-2 | sort | uniq > report/total_ixbr_asn.latest_cc
    echo "generating ixbr aggregate summary data... - $(date)"
    cat report/ixbr_*latest_cc | cut -d '|' -f1-2 | sort | uniq | cut -d '|' -f2 | sort | uniq -c | sort -k1 -n > report/total_ixbr_asn.latest_cc_summary
else
    echo "wrong option"
fi
