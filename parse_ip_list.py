# coding:utf-8
import re
import httplib2
import subprocess as sb
from netaddr import IPNetwork, IPSet, cidr_merge
import argparse


class IpParse:
    def __init__(self, site="", domain_list_file="domain.list"):
        if not domain_list_file:
            domain_list_file = "domain.list"
        self.site = site
        self.http = httplib2.Http()
        self.ip_list = set()
        self.domain_list = open(domain_list_file, "r")

    def parse_ip_by_asn(self):
        try:
            url = "http://networktools.nl/asinfo/" + self.site
            resp, content = self.http.request(url)
            if content:
                r = re.findall(r"ASNumber:\s+(\d+)", content)
                if not r:
                    r = re.findall(r"Primary ASN\s+:\s*(\d+)", content)
                asn = r[0]
                p = sb.Popen("whois -h whois.radb.net -- '-i origin AS%s' | grep ^route |grep -v route6" % (str(asn)),
                             shell=True, stdout=sb.PIPE)
                raw_ip_list = p.stdout.read().split("\n")
                for item in raw_ip_list:
                    self.ip_list.add(item.rlace("route:", "").strip())

        except Exception as e:
            print e

    @staticmethod
    def get_ns_addr_google(string):
        sting_list = string.split(" ")
        result = []
        for item in sting_list:
            r = re.findall(r"include:(.*)", item)
            if r:
                result.append(r[0])
        return result

    @staticmethod
    def get_ip_addr_google(string):
        sting_list = string.split(" ")
        result = []
        for item in sting_list:
            r = re.findall(r"ip4:(.*)", item)
            if r:
                result.append(r[0])
        return result

    def parse_google_ip(self):
        p = sb.Popen("nslookup -q=TXT _spf.google.com 8.8.8.8|grep '_spf.google.com'", shell=True, stdout=sb.PIPE)
        net_block_list = self.get_ns_addr_google(p.stdout.read())
        for item in net_block_list:
            s = sb.Popen("nslookup -q=TXT " + item + " 8.8.8.8", shell=True, stdout=sb.PIPE)
            r = self.get_ip_addr_google(s.stdout.read())
            if r:
                self.ip_list.update(r)

    def format_ip_for_openvpn(self):
        result = set()
        for raw_ip in self.ip_list:
            if raw_ip:
                ip = IPNetwork(raw_ip)
                result.add('push "route %s %s"' % (str(ip.ip), str(ip.netmask)))
        return result

    def run(self):
        if self.site:
            if "google" in self.site or "youtube" in self.site:
                self.parse_google_ip()
            else:
                self.parse_ip_by_asn()
        else:
            for line in self.domain_list:
                if "google" in line or "youtube" in line:
                    self.parse_google_ip()
                else:
                    self.site = line.replace("\n", "")
                    self.parse_ip_by_asn()

    def out(self):
        print "\n".join(sorted(self.ip_list, reverse=True))

    def out_for_openvpn(self):
        print "\n".join(sorted(self.format_ip_for_openvpn(), reverse=True))

    def merge(self):
        merge_list = cidr_merge(self.ip_list)
        tmp_list = []
        for item in merge_list:
            tmp_list.append(str(item))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", action="store", dest="domain", help="domain name,eg: google.com")
    parser.add_argument("-f", action="store", dest="file", help="domain name list in file,eg: /root/domain.list")
    parser.add_argument("-m", action="store_true", dest="merge", help="merge result")
    parser.add_argument("-o", action="store_true", dest="openvpn", help="openvpn result")
    args = parser.parse_args()

    ip_parse = IpParse(site=args.domain, domain_list_file=args.file)
    ip_parse.run()
    if args.merge:
        ip_parse.merge()
    if args.openvpn:
        ip_parse.out_for_openvpn()
    else:
        ip_parse.out()