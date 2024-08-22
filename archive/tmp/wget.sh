#!/bin/sh

cd rirs
wget ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest
wget ftp.ripe.net/ripe/stats/delegated-ripencc-latest
wget ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-latest
wget ftp.apnic.net/pub/stats/apnic/delegated-apnic-latest
wget ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest

