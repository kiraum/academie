#!/bin/sh

format_bgp_table(){
    # Process BGP table, extract network and ROA information, and write to /tmp/bgptable

    if [ -f "lgbgp" ]
    then
        echo "bgp table file exist..."
    else
        echo "missing bgp table file..."
        exit 1
    fi

    echo "" > /tmp/bgptable

    while read line
    do
        network=$(echo "$line" | grep ^* | awk '{print $2}')
        if echo $network | grep -vEq '187.16.2[1][0-9]|187.16.2[2][0-3]'
        then
            last=$network
        else
            network=$last
        fi
        roa=$(echo "$line" | grep ^* | awk '{print $(NF-1)}' | sed 's/{//' | sed 's/}//')
        if [ "$network" != "" ] || [ "$roa" != "" ]
        then
            echo $roa"|"$network >> /tmp/bgptable
        fi
    done < lgbgp
}

format_bgp_table
