#!/bin/sh

#{ echo "terminal length 0"; sleep 5; echo "show ip bgp"; sleep 295; } | telnet lg.sp.ptt.br > lgbgp

format_bgp_table(){
    # Process BGP table, extract network and AS information, and write to /tmp/bgptable_connected

    if [ -f "lgbgp" ]
    then
        echo "bgp table file exist..."
    else
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
        if [ "$network" != "" ] || [ "$as" != "" ]
        then
            echo $as"|"$network >> /tmp/bgptable_connected
        fi
    done < lgbgp
}

format_bgp_table
