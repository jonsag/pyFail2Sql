pyFail2Sql
==========

Log fail2ban bans to mysql

Installation
============
copy files to suitable folder

setup database:
./pyFail2Sql.py --setupdb


edit your action, for example action.d/iptables.conf

add row beneath 'actionban = iptables -I fail2ban-<name> 1 -s <ip> -j <blocktype>'

add this:
/path/to/your/folder/pyFail2Sql.py -w -n <name> -q <protocol> -p <port> -i <ip> -e ban
