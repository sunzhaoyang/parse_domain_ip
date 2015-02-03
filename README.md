# parse_domain_ip
获取网站的ip列表
用于给openvpn配置推送路由

编辑domain.list文件，运行python parse_ip_list.py

追加到openvpn 的server.conf文件最后

依赖：
pip install httplib2
pip install netaddr
